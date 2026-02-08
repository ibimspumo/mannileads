import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// ---- Queries ----

export const list = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("leads").collect();
  },
});

export const get = query({
  args: { id: v.id("leads") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const stats = query({
  args: {},
  handler: async (ctx) => {
    const leads = await ctx.db.query("leads").collect();
    const total = leads.length;
    const avgScore = total > 0 ? Math.round(leads.reduce((s, l) => s + l.score, 0) / total) : 0;
    const mitKontakt = leads.filter((l) => l.ansprechpartner).length;

    const segments = { HOT: 0, WARM: 0, COLD: 0, DISQUALIFIED: 0 };
    const statuses: Record<string, number> = {};
    const branchen: Record<string, number> = {};
    const scoreDistribution = [0, 0, 0, 0, 0]; // 0-20, 21-40, 41-60, 61-80, 81-100

    for (const l of leads) {
      segments[l.segment]++;
      statuses[l.status] = (statuses[l.status] || 0) + 1;
      if (l.branche) branchen[l.branche] = (branchen[l.branche] || 0) + 1;
      const bucket = Math.min(Math.floor(l.score / 20), 4);
      scoreDistribution[bucket]++;
    }

    return { total, avgScore, mitKontakt, segments, statuses, branchen, scoreDistribution };
  },
});

// ---- Mutations ----

const leadFields = {
  firma: v.string(),
  website: v.string(),
  branche: v.string(),
  groesse: v.string(),
  plz: v.string(),
  ort: v.string(),
  ansprechpartner: v.string(),
  position: v.string(),
  email: v.string(),
  telefon: v.string(),
  websiteQualitaet: v.number(),
  socialMedia: v.boolean(),
  socialMediaLinks: v.string(),
  googleBewertung: v.string(),
  websiteText: v.optional(v.string()),
  score: v.number(),
  kiZusammenfassung: v.string(),
  segment: v.union(v.literal("HOT"), v.literal("WARM"), v.literal("COLD"), v.literal("DISQUALIFIED")),
  segmentManuell: v.boolean(),
  tags: v.array(v.string()),
  // KI-Analyse (optional, wird von analyze.py gesetzt)
  kiAnalysiert: v.optional(v.boolean()),
  kiAnalysiertAm: v.optional(v.string()),
  kiZielgruppe: v.optional(v.string()),
  kiOnlineAuftritt: v.optional(v.string()),
  kiSchwaechen: v.optional(v.string()),
  kiChancen: v.optional(v.string()),
  kiWettbewerb: v.optional(v.string()),
  kiAnsprache: v.optional(v.string()),
  kiAnspracheSig: v.optional(v.string()),
  kiScore: v.optional(v.number()),
  kiScoreBegruendung: v.optional(v.string()),
  kiSegment: v.optional(v.string()),
  status: v.union(
    v.literal("Neu"),
    v.literal("Kontaktiert"),
    v.literal("Interessiert"),
    v.literal("Angebot"),
    v.literal("Gewonnen"),
    v.literal("Verloren")
  ),
  notizen: v.string(),
  history: v.array(v.object({ timestamp: v.string(), aktion: v.string(), details: v.string() })),
  erstelltAm: v.string(),
  bearbeitetAm: v.string(),
};

export const create = mutation({
  args: leadFields,
  handler: async (ctx, args) => {
    return await ctx.db.insert("leads", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("leads"),
    ...leadFields,
  },
  handler: async (ctx, args) => {
    const { id, ...data } = args;
    await ctx.db.replace(id, data);
  },
});

export const remove = mutation({
  args: { id: v.id("leads") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

export const bulkCreate = mutation({
  args: {
    leads: v.array(v.object(leadFields)),
  },
  handler: async (ctx, args) => {
    // Alle existierenden Leads laden für Duplikat-Check
    const existing = await ctx.db.query("leads").collect();
    const existingKeys = new Set(
      existing.map((l) => `${l.firma.toLowerCase().trim()}|${l.plz}|${l.website.toLowerCase().trim()}`)
    );
    // Email-Dedup: jede Email darf nur einmal existieren
    const existingEmails = new Set(
      existing.filter((l) => l.email).map((l) => l.email.toLowerCase().trim())
    );

    const ids = [];
    let skipped = 0;
    for (const lead of args.leads) {
      // Check firma+plz+website
      const key = `${lead.firma.toLowerCase().trim()}|${lead.plz}|${lead.website.toLowerCase().trim()}`;
      if (existingKeys.has(key)) {
        skipped++;
        continue;
      }
      // Check email uniqueness
      const email = lead.email?.toLowerCase().trim();
      if (email && existingEmails.has(email)) {
        skipped++;
        continue;
      }
      existingKeys.add(key);
      if (email) existingEmails.add(email);
      const id = await ctx.db.insert("leads", lead);
      ids.push(id);
    }
    return ids;
  },
});

export const clearAll = mutation({
  args: {},
  handler: async (ctx) => {
    const all = await ctx.db.query("leads").collect();
    for (const lead of all) {
      await ctx.db.delete(lead._id);
    }
    return { deleted: all.length };
  },
});

export const replaceAll = mutation({
  args: {
    leads: v.array(v.object(leadFields)),
  },
  handler: async (ctx, args) => {
    // Delete all existing
    const existing = await ctx.db.query("leads").collect();
    for (const lead of existing) {
      await ctx.db.delete(lead._id);
    }
    // Insert new
    const ids = [];
    for (const lead of args.leads) {
      const id = await ctx.db.insert("leads", lead);
      ids.push(id);
    }
    return ids;
  },
});
