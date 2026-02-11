import { v } from "convex/values";
import { internalMutation } from "./_generated/server";

// Internal mutation to create send (must be in non-node file)
export const createSend = internalMutation({
  args: {
    campaignId: v.id("emailCampaigns"),
    leadId: v.id("leads"),
    accountId: v.id("emailAccounts"),
    to: v.string(),
    subject: v.string(),
    htmlBody: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("emailSends", {
      ...args,
      status: "queued",
      queuedAt: new Date().toISOString(),
    });
  },
});
