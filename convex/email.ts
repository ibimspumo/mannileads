import { v } from "convex/values";
import { mutation, query, action, internalQuery } from "./_generated/server";
import { api, internal } from "./_generated/api";
import type { Id } from "./_generated/dataModel";

// ===== EMAIL ACCOUNTS =====

export const listAccounts = query({
  handler: async (ctx) => {
    return await ctx.db.query("emailAccounts").order("desc").collect();
  },
});

export const getAccount = query({
  args: { id: v.id("emailAccounts") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const createAccount = mutation({
  args: {
    name: v.string(),
    fromEmail: v.string(),
    fromName: v.string(),
    signatureHtml: v.string(),
    smtpHost: v.optional(v.string()),
    smtpPort: v.optional(v.number()),
    smtpUser: v.optional(v.string()),
    smtpPassword: v.optional(v.string()),
    smtpTls: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const now = new Date().toISOString();
    return await ctx.db.insert("emailAccounts", {
      ...args,
      active: true,
      verified: false,
      totalSent: 0,
      createdAt: now,
      updatedAt: now,
    });
  },
});

export const updateAccount = mutation({
  args: {
    id: v.id("emailAccounts"),
    name: v.optional(v.string()),
    fromEmail: v.optional(v.string()),
    fromName: v.optional(v.string()),
    signatureHtml: v.optional(v.string()),
    smtpHost: v.optional(v.string()),
    smtpPort: v.optional(v.number()),
    smtpUser: v.optional(v.string()),
    smtpPassword: v.optional(v.string()),
    smtpTls: v.optional(v.boolean()),
    active: v.optional(v.boolean()),
    verified: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    return await ctx.db.patch(id, {
      ...updates,
      updatedAt: new Date().toISOString(),
    });
  },
});

export const deleteAccount = mutation({
  args: { id: v.id("emailAccounts") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

// ===== EMAIL TEMPLATES =====

export const listTemplates = query({
  handler: async (ctx) => {
    return await ctx.db.query("emailTemplates").order("desc").collect();
  },
});

export const getTemplate = query({
  args: { id: v.id("emailTemplates") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const createTemplate = mutation({
  args: {
    name: v.string(),
    subject: v.string(),
    htmlBody: v.string(),
    placeholders: v.array(v.string()),
  },
  handler: async (ctx, args) => {
    const now = new Date().toISOString();
    return await ctx.db.insert("emailTemplates", {
      ...args,
      createdAt: now,
      updatedAt: now,
    });
  },
});

export const updateTemplate = mutation({
  args: {
    id: v.id("emailTemplates"),
    name: v.optional(v.string()),
    subject: v.optional(v.string()),
    htmlBody: v.optional(v.string()),
    placeholders: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    return await ctx.db.patch(id, {
      ...updates,
      updatedAt: new Date().toISOString(),
    });
  },
});

export const deleteTemplate = mutation({
  args: { id: v.id("emailTemplates") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

// ===== EMAIL CAMPAIGNS =====

export const listCampaigns = query({
  handler: async (ctx) => {
    const campaigns = await ctx.db.query("emailCampaigns").order("desc").collect();
    // Enrich with account + template info
    const enriched = await Promise.all(
      campaigns.map(async (c) => ({
        ...c,
        account: await ctx.db.get(c.accountId),
        template: await ctx.db.get(c.templateId),
      }))
    );
    return enriched;
  },
});

export const getCampaign = query({
  args: { id: v.id("emailCampaigns") },
  handler: async (ctx, args) => {
    const campaign = await ctx.db.get(args.id);
    if (!campaign) return null;
    return {
      ...campaign,
      account: await ctx.db.get(campaign.accountId),
      template: await ctx.db.get(campaign.templateId),
    };
  },
});

export const createCampaign = mutation({
  args: {
    name: v.string(),
    templateId: v.id("emailTemplates"),
    accountId: v.id("emailAccounts"),
    filtersJson: v.string(),
  },
  handler: async (ctx, args) => {
    const now = new Date().toISOString();
    return await ctx.db.insert("emailCampaigns", {
      ...args,
      status: "draft",
      totalLeads: 0,
      totalQueued: 0,
      totalSent: 0,
      totalDelivered: 0,
      totalOpened: 0,
      totalClicked: 0,
      totalBounced: 0,
      totalComplained: 0,
      createdAt: now,
    });
  },
});

export const updateCampaign = mutation({
  args: {
    id: v.id("emailCampaigns"),
    name: v.optional(v.string()),
    templateId: v.optional(v.id("emailTemplates")),
    accountId: v.optional(v.id("emailAccounts")),
    filtersJson: v.optional(v.string()),
    status: v.optional(
      v.union(
        v.literal("draft"),
        v.literal("queued"),
        v.literal("sending"),
        v.literal("sent"),
        v.literal("paused")
      )
    ),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    return await ctx.db.patch(id, updates);
  },
});

export const deleteCampaign = mutation({
  args: { id: v.id("emailCampaigns") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

// ===== CAMPAIGN STATS UPDATE =====

export const updateCampaignStats = mutation({
  args: {
    campaignId: v.id("emailCampaigns"),
  },
  handler: async (ctx, args) => {
    const sends = await ctx.db
      .query("emailSends")
      .withIndex("by_campaign", (q) => q.eq("campaignId", args.campaignId))
      .collect();

    const stats = {
      totalQueued: sends.filter((s) => s.status === "queued").length,
      totalSent: sends.filter((s) =>
        ["sent", "delivered", "opened", "clicked"].includes(s.status)
      ).length,
      totalDelivered: sends.filter((s) =>
        ["delivered", "opened", "clicked"].includes(s.status)
      ).length,
      totalOpened: sends.filter((s) => ["opened", "clicked"].includes(s.status)).length,
      totalClicked: sends.filter((s) => s.status === "clicked").length,
      totalBounced: sends.filter((s) => s.status === "bounced").length,
      totalComplained: sends.filter((s) => s.status === "complained").length,
    };

    const openRate = stats.totalDelivered > 0 ? stats.totalOpened / stats.totalDelivered : 0;
    const clickRate = stats.totalOpened > 0 ? stats.totalClicked / stats.totalOpened : 0;
    const bounceRate = stats.totalSent > 0 ? stats.totalBounced / stats.totalSent : 0;

    await ctx.db.patch(args.campaignId, {
      ...stats,
      openRate,
      clickRate,
      bounceRate,
    });
  },
});

// ===== EMAIL SENDS =====

export const listSends = query({
  args: {
    campaignId: v.optional(v.id("emailCampaigns")),
    status: v.optional(v.string()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let sends;
    if (args.campaignId) {
      sends = await ctx.db
        .query("emailSends")
        .withIndex("by_campaign", (q) => q.eq("campaignId", args.campaignId!))
        .order("desc")
        .take(args.limit || 100);
    } else if (args.status) {
      sends = await ctx.db
        .query("emailSends")
        .withIndex("by_status", (q) => q.eq("status", args.status as any))
        .order("desc")
        .take(args.limit || 100);
    } else {
      sends = await ctx.db
        .query("emailSends")
        .order("desc")
        .take(args.limit || 100);
    }
    return sends;
  },
});

export const getSend = query({
  args: { id: v.id("emailSends") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const updateSendStatus = mutation({
  args: {
    id: v.id("emailSends"),
    status: v.union(
      v.literal("queued"),
      v.literal("sending"),
      v.literal("sent"),
      v.literal("delivered"),
      v.literal("opened"),
      v.literal("clicked"),
      v.literal("bounced"),
      v.literal("complained"),
      v.literal("failed")
    ),
    timestamp: v.optional(v.string()),
    sesMessageId: v.optional(v.string()),
    errorMessage: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, status, timestamp, sesMessageId, errorMessage } = args;
    const now = timestamp || new Date().toISOString();
    const updates: any = { status };

    if (sesMessageId) updates.sesMessageId = sesMessageId;
    if (errorMessage) updates.errorMessage = errorMessage;

    if (status === "sent") updates.sentAt = now;
    if (status === "delivered") updates.deliveredAt = now;
    if (status === "opened") updates.openedAt = now;
    if (status === "clicked") updates.clickedAt = now;
    if (status === "bounced") updates.bouncedAt = now;

    await ctx.db.patch(id, updates);

    // Update campaign stats
    const send = await ctx.db.get(id);
    if (send) {
      await ctx.scheduler.runAfter(0, api.email.updateCampaignStats, {
        campaignId: send.campaignId,
      });
    }
  },
});

// ===== EMAIL EVENTS =====

export const createEvent = mutation({
  args: {
    sendId: v.id("emailSends"),
    type: v.union(
      v.literal("open"),
      v.literal("click"),
      v.literal("bounce"),
      v.literal("complaint")
    ),
    metadata: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const eventId = await ctx.db.insert("emailEvents", {
      ...args,
      timestamp: new Date().toISOString(),
    });

    // Update send status if this is first event of this type
    const send = await ctx.db.get(args.sendId);
    if (!send) return eventId;

    if (args.type === "open" && !send.openedAt) {
      await ctx.scheduler.runAfter(0, api.email.updateSendStatus, {
        id: args.sendId,
        status: "opened",
      });
    } else if (args.type === "click" && !send.clickedAt) {
      await ctx.scheduler.runAfter(0, api.email.updateSendStatus, {
        id: args.sendId,
        status: "clicked",
      });
    } else if (args.type === "bounce" && !send.bouncedAt) {
      await ctx.scheduler.runAfter(0, api.email.updateSendStatus, {
        id: args.sendId,
        status: "bounced",
      });
    } else if (args.type === "complaint" && send.status !== "complained") {
      await ctx.scheduler.runAfter(0, api.email.updateSendStatus, {
        id: args.sendId,
        status: "complained",
      });
    }

    return eventId;
  },
});

export const listEvents = query({
  args: {
    sendId: v.optional(v.id("emailSends")),
    type: v.optional(v.string()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let events;
    if (args.sendId) {
      events = await ctx.db
        .query("emailEvents")
        .withIndex("by_send", (q) => q.eq("sendId", args.sendId!))
        .order("desc")
        .take(args.limit || 100);
    } else if (args.type) {
      events = await ctx.db
        .query("emailEvents")
        .withIndex("by_type", (q) => q.eq("type", args.type as any))
        .order("desc")
        .take(args.limit || 100);
    } else {
      events = await ctx.db
        .query("emailEvents")
        .order("desc")
        .take(args.limit || 100);
    }
    return events;
  },
});

// ===== FILTER OPTIONS =====

// Internal query to gather unique branchen/plz from one page
export const _filterOptionsPage = internalQuery({
  args: {
    cursor: v.union(v.string(), v.null()),
  },
  handler: async (ctx, args) => {
    const result = await ctx.db.query("leads").paginate({
      numItems: 500,
      cursor: (args.cursor ?? null) as any,
    });
    const branchen = new Set<string>();
    const plzSet = new Set<string>();
    for (const l of result.page) {
      if (l.branche && l.branche.trim()) branchen.add(l.branche);
      if (l.plz && l.plz.trim()) plzSet.add(l.plz);
    }
    return {
      branchen: Array.from(branchen),
      plz: Array.from(plzSet),
      nextCursor: result.isDone ? null : (result.continueCursor as string),
    };
  },
});

// Action: get all unique branchen and PLZ values
export const getFilterOptions = action({
  args: {},
  handler: async (ctx) => {
    const allBranchen = new Set<string>();
    const allPLZ = new Set<string>();
    let cursor: string | null = null;
    let done = false;

    while (!done) {
      const result: any = await ctx.runQuery(internal.email._filterOptionsPage, { cursor });
      for (const b of result.branchen) allBranchen.add(b);
      for (const p of result.plz) allPLZ.add(p);
      if (!result.nextCursor) {
        done = true;
      } else {
        cursor = result.nextCursor;
      }
    }

    return {
      branchen: Array.from(allBranchen).sort(),
      plz: Array.from(allPLZ).sort(),
    };
  },
});

// ===== EMAIL PREVIEW WITH SIGNATURE =====

export const previewEmailWithSignature = query({
  args: {
    templateId: v.id("emailTemplates"),
    accountId: v.id("emailAccounts"),
    leadId: v.id("leads"),
  },
  handler: async (ctx, args) => {
    const template = await ctx.db.get(args.templateId);
    const lead = await ctx.db.get(args.leadId);
    const account = await ctx.db.get(args.accountId);
    if (!template || !lead || !account) return null;

    const subject = renderTemplate(template.subject, lead);
    let htmlBody = renderTemplate(template.htmlBody, lead);

    // Append signature if present
    if (account.signatureHtml) {
      htmlBody += '<br/>' + account.signatureHtml;
    }

    return {
      subject,
      htmlBody,
      lead,
      account: {
        fromName: account.fromName,
        fromEmail: account.fromEmail,
        name: account.name,
      },
    };
  },
});

// testConnection moved to emailActions.ts ("use node" required for nodemailer)

// ===== CAMPAIGN LEAD COUNTING =====

// Internal query to paginate through leads
export const _countLeadsPage = internalQuery({
  args: {
    cursor: v.union(v.string(), v.null()),
    branche: v.optional(v.string()),
    plz: v.optional(v.string()),
    segment: v.optional(v.string()),
    status: v.optional(v.string()),
    scoreMin: v.number(),
    scoreMax: v.number(),
    previewLimit: v.number(),
  },
  handler: async (ctx, args) => {
    const result = await ctx.db.query("leads").paginate({
      numItems: 500,
      cursor: (args.cursor ?? null) as any,
    });
    let count = 0;
    const preview: any[] = [];
    for (const l of result.page) {
      if (!l.email || l.email.trim() === '') continue;
      if (args.branche && l.branche !== args.branche) continue;
      if (args.plz && !l.plz.startsWith(args.plz)) continue;
      if (args.segment && l.segment !== args.segment) continue;
      if (args.status && l.status !== args.status) continue;
      if (l.score < args.scoreMin || l.score > args.scoreMax) continue;
      count++;
      if (preview.length < args.previewLimit) {
        preview.push({ _id: l._id, firma: l.firma, email: l.email, ort: l.ort, branche: l.branche });
      }
    }
    return { count, preview, nextCursor: result.isDone ? null : (result.continueCursor as string) };
  },
});

// Action: count all matching leads for campaign targeting
export const countLeadsForCampaign = action({
  args: {
    branche: v.optional(v.string()),
    plz: v.optional(v.string()),
    segment: v.optional(v.string()),
    status: v.optional(v.string()),
    scoreMin: v.optional(v.number()),
    scoreMax: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let totalCount = 0;
    const allPreview: any[] = [];
    let cursor: string | null = null;
    let done = false;

    while (!done) {
      const result: any = await ctx.runQuery(internal.email._countLeadsPage, {
        cursor,
        branche: args.branche,
        plz: args.plz,
        segment: args.segment,
        status: args.status,
        scoreMin: args.scoreMin ?? 0,
        scoreMax: args.scoreMax ?? 100,
        previewLimit: 10 - allPreview.length,
      });
      totalCount += result.count;
      allPreview.push(...result.preview);
      if (!result.nextCursor) {
        done = true;
      } else {
        cursor = result.nextCursor;
      }
    }

    return { count: totalCount, preview: allPreview.slice(0, 10) };
  },
});

// ===== CAMPAIGN UTILITIES =====

// Render template with lead data
function renderTemplate(template: string, data: Record<string, any>): string {
  let rendered = template;
  for (const [key, value] of Object.entries(data)) {
    const placeholder = new RegExp(`{{${key}}}`, "g");
    let val = value;
    if (val == null) val = "";
    else if (Array.isArray(val)) val = val.join(", ");
    else val = String(val).replace(/\n/g, "<br>");
    rendered = rendered.replace(placeholder, val);
  }
  return rendered;
}

// Preview email for a lead
export const previewEmail = query({
  args: {
    templateId: v.id("emailTemplates"),
    leadId: v.id("leads"),
  },
  handler: async (ctx, args) => {
    const template = await ctx.db.get(args.templateId);
    const lead = await ctx.db.get(args.leadId);
    if (!template || !lead) return null;

    const subject = renderTemplate(template.subject, lead);
    const htmlBody = renderTemplate(template.htmlBody, lead);

    return { subject, htmlBody, lead };
  },
});
