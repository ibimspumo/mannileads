"use node";
import { v } from "convex/values";
import { action, internalAction } from "./_generated/server";
import { api, internal } from "./_generated/api";
import type { Id } from "./_generated/dataModel";

// ===== CAMPAIGN QUEUE & SEND =====

// Start a campaign: filter leads, create emailSends entries
export const startCampaign = action({
  args: { campaignId: v.id("emailCampaigns") },
  handler: async (ctx, args): Promise<{ totalLeads: number; sendIds: any[] }> => {
    const campaign = await ctx.runQuery(api.email.getCampaign, { id: args.campaignId });
    if (!campaign) throw new Error("Campaign not found");
    if (campaign.status !== "draft") throw new Error("Campaign already started");

    const template = campaign.template;
    const account = campaign.account;
    if (!template || !account) throw new Error("Template or Account not found");

    // Parse filters
    const filters = JSON.parse(campaign.filtersJson || "{}");

    // Query leads with filters
    const allLeads: any[] = await ctx.runQuery(api.leads.list, {});
    const filteredLeads: any[] = allLeads.filter((lead: any) => {
      // Must have email
      if (!lead.email || lead.email.trim() === "") return false;

      // Apply filters
      if (filters.branche && lead.branche !== filters.branche) return false;
      if (filters.plz && lead.plz !== filters.plz) return false;
      if (filters.segment && lead.segment !== filters.segment) return false;
      if (filters.status && lead.status !== filters.status) return false;
      if (filters.scoreMin && lead.score < filters.scoreMin) return false;
      if (filters.scoreMax && lead.score > filters.scoreMax) return false;

      return true;
    });

    // Create emailSends for each lead
    const now = new Date().toISOString();
    const sendIds: any[] = [];

    for (const lead of filteredLeads) {
      // Render template
      const subject = renderTemplate(template.subject, lead);
      const htmlBody = renderTemplate(template.htmlBody, lead);

      // Create send
      const sendId: any = await ctx.runMutation(internal.emailSendingMutations.createSend, {
        campaignId: args.campaignId,
        leadId: lead._id,
        accountId: account._id,
        to: lead.email,
        subject,
        htmlBody,
      });
      sendIds.push(sendId);
    }

    // Update campaign
    await ctx.runMutation(api.email.updateCampaign, {
      id: args.campaignId,
      status: "queued",
    });

    await ctx.runMutation(api.email.updateCampaignStats, {
      campaignId: args.campaignId,
    });

    return { totalLeads: filteredLeads.length, sendIds };
  },
});

// Process send queue (call this from a cron or manual trigger)
export const processSendQueue = action({
  args: {
    batchSize: v.optional(v.number()),
  },
  handler: async (ctx, args): Promise<{ processed: number; message?: string; results?: any[] }> => {
    const batchSize = args.batchSize || 10;

    // Get queued sends
    const queuedSends: any[] = await ctx.runQuery(api.email.listSends, {
      status: "queued",
      limit: batchSize,
    });

    if (queuedSends.length === 0) {
      return { processed: 0, message: "No queued sends" };
    }

    // Process each send
    const results: any[] = [];
    for (const send of queuedSends) {
      try {
        const result: any = await ctx.runAction(internal.emailSending.sendEmail, {
          sendId: send._id,
        });
        results.push({ sendId: send._id, success: true, result });
      } catch (error: any) {
        console.error(`Failed to send ${send._id}:`, error);
        await ctx.runMutation(api.email.updateSendStatus, {
          id: send._id,
          status: "failed",
          errorMessage: error.message,
        });
        results.push({ sendId: send._id, success: false, error: error.message });
      }

      // Rate limiting: ~72 seconds between emails = max 50/hour (Hetzner SMTP limit)
      // For batches, 2 seconds between sends is safe for moderate volumes
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }

    return { processed: results.length, results };
  },
});

// Send single email via SES (internal action)
export const sendEmail = internalAction({
  args: { sendId: v.id("emailSends") },
  handler: async (ctx, args) => {
    const send = await ctx.runQuery(api.email.getSend, { id: args.sendId });
    if (!send) throw new Error("Send not found");

    const account = await ctx.runQuery(api.email.getAccount, { id: send.accountId });
    if (!account) throw new Error("Account not found");

    // Update status to sending
    await ctx.runMutation(api.email.updateSendStatus, {
      id: args.sendId,
      status: "sending",
    });

    // Add tracking pixel and replace links
    const trackedHtml = await addTracking(send.htmlBody, args.sendId);

    // Send via SMTP (Nodemailer)
    try {
      if (!account.smtpHost || !account.smtpUser || !account.smtpPassword) {
        throw new Error("SMTP credentials not configured for this account");
      }
      const result = await sendViaSMTP({
        host: account.smtpHost,
        port: account.smtpPort ?? 587,
        user: account.smtpUser,
        password: account.smtpPassword,
        tls: account.smtpTls ?? true,
        from: `${account.fromName} <${account.fromEmail}>`,
        to: send.to,
        subject: send.subject,
        htmlBody: trackedHtml + account.signatureHtml,
      });

      // Update status
      await ctx.runMutation(api.email.updateSendStatus, {
        id: args.sendId,
        status: "sent",
        sesMessageId: result.messageId, // nodemailer messageId
      });

      // Account stats updated - could be tracked via aggregation later

      return result;
    } catch (error: any) {
      await ctx.runMutation(api.email.updateSendStatus, {
        id: args.sendId,
        status: "failed",
        errorMessage: error.message,
      });
      throw error;
    }
  },
});

// ===== TRACKING UTILITIES =====

async function addTracking(htmlBody: string, sendId: Id<"emailSends">): Promise<string> {
  // Get base URL - in production this should be set in Convex environment
  const baseUrl = "https://mannileads.vercel.app";

  // Add tracking pixel (1x1 transparent gif)
  const trackingPixel = `<img src="${baseUrl}/api/track/open/${sendId}" width="1" height="1" alt="" style="display:block;border:0;" />`;

  // Replace all <a> tags with tracked links
  let tracked = htmlBody;
  const linkRegex = /<a\s+([^>]*href=["']([^"']+)["'][^>]*)>/gi;
  tracked = tracked.replace(linkRegex, (match, attrs, url) => {
    // Skip if already a tracking URL
    if (url.includes("/api/track/click/")) return match;
    const trackedUrl = `${baseUrl}/api/track/click/${sendId}?url=${encodeURIComponent(url)}`;
    return `<a ${attrs.replace(url, trackedUrl)}>`;
  });

  // Append tracking pixel at the end
  tracked += `\n${trackingPixel}`;

  return tracked;
}

// ===== SMTP INTEGRATION (Nodemailer) =====

interface SMTPParams {
  host: string;
  port: number;
  user: string;
  password: string;
  tls: boolean;
  from: string;
  to: string;
  subject: string;
  htmlBody: string;
}

async function sendViaSMTP(params: SMTPParams): Promise<any> {
  const nodemailer = await import("nodemailer");

  const transporter = nodemailer.createTransport({
    host: params.host,
    port: params.port,
    secure: params.port === 465, // true for 465, false for 587 (STARTTLS)
    auth: {
      user: params.user,
      pass: params.password,
    },
    tls: {
      rejectUnauthorized: true,
    },
  });

  const info = await transporter.sendMail({
    from: params.from,
    to: params.to,
    subject: params.subject,
    html: params.htmlBody,
  });

  return info;
}

// ===== LEGACY SES INTEGRATION (auskommentiert als Fallback) =====
/*
interface SESParams {
  accessKey: string;
  secretKey: string;
  region: string;
  from: string;
  to: string;
  subject: string;
  htmlBody: string;
}

async function sendViaSES(params: SESParams): Promise<any> {
  const { SESv2Client, SendEmailCommand } = await import("@aws-sdk/client-sesv2");
  const client = new SESv2Client({
    region: params.region,
    credentials: {
      accessKeyId: params.accessKey,
      secretAccessKey: params.secretKey,
    },
  });
  const command = new SendEmailCommand({
    FromEmailAddress: params.from,
    Destination: { ToAddresses: [params.to] },
    Content: {
      Simple: {
        Subject: { Data: params.subject, Charset: "UTF-8" },
        Body: { Html: { Data: params.htmlBody, Charset: "UTF-8" } },
      },
    },
  });
  const response = await client.send(command);
  return response;
}
*/

// ===== TEMPLATE RENDERING =====

function renderTemplate(template: string, data: Record<string, any>): string {
  let rendered = template;
  for (const [key, value] of Object.entries(data)) {
    const placeholder = new RegExp(`{{${key}}}`, "g");
    rendered = rendered.replace(placeholder, String(value || ""));
  }
  return rendered;
}
