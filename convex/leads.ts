import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// ---- Queries ----

// Sanitize string for Convex object keys (no non-ASCII)
function sanitizeKey(s: string): string {
  const map: Record<string, string> = {
    "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue",
    "\u00c4": "Ae", "\u00d6": "Oe", "\u00dc": "Ue", "\u00df": "ss",
  };
  return s.replace(/[^\x20-\x7E]/g, (c) => map[c] || "_");
}

export const list = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    return await ctx.db.query("leads").take(args.limit ?? 500);
  },
});

export const get = query({
  args: { id: v.id("leads") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// Stats using single paginated query to stay within 16MB + 1-pagination limits
export const stats = query({
  args: {},
  handler: async (ctx) => {
    const segments: Record<string, number> = { HOT: 0, WARM: 0, COLD: 0, DISQUALIFIED: 0 };
    const statuses: Record<string, number> = {};
    const branchenMap = new Map<string, number>();
    const scoreDistribution = [0, 0, 0, 0, 0];
    let total = 0;
    let scoreSum = 0;
    let mitKontakt = 0;

    // Single paginated query through all leads
    const result = await ctx.db.query("leads").paginate({ numItems: 8000, cursor: null as any });
    const allLeads = result.page;
    // If not done, we have >8000 leads. For now handle what we got.
    for (const l of allLeads) {
      total++;
      const sc = typeof l.score === "number" ? l.score : 0;
      scoreSum += sc;
      if (l.ansprechpartner && l.ansprechpartner.length > 0) mitKontakt++;
      const seg = l.segment as string;
      if (seg in segments) segments[seg]++;
      const st = l.status as string;
      if (st) statuses[st] = (statuses[st] || 0) + 1;
      const br = l.branche;
      if (br) branchenMap.set(br, (branchenMap.get(br) || 0) + 1);
      scoreDistribution[Math.min(Math.floor(sc / 20), 4)]++;
    }

    const branchen: Record<string, number> = {};
    for (const [k, cnt] of branchenMap) {
      branchen[sanitizeKey(k)] = cnt;
    }

    return {
      total,
      avgScore: total > 0 ? Math.round(scoreSum / total) : 0,
      mitKontakt,
      segments,
      statuses,
      branchen,
      scoreDistribution,
    };
  },
});

export const listPaginated = query({
  args: {
    page: v.number(),
    pageSize: v.optional(v.number()),
    segment: v.optional(v.string()),
    branche: v.optional(v.string()),
    searchQuery: v.optional(v.string()),
    sortBy: v.optional(v.string()),
    sortDir: v.optional(v.string()),
    status: v.optional(v.string()),
    scoreMin: v.optional(v.number()),
    scoreMax: v.optional(v.number()),
    plz: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const pageSize = args.pageSize ?? 100;
    const page = Math.max(1, args.page);

    // Single paginated query to get all leads (Convex limit: 1 pagination per function)
    const result = await ctx.db.query("leads").paginate({ numItems: 8000, cursor: null as any });
    const allFiltered: any[] = [];
    for (const l of result.page) {
      if (args.segment && l.segment !== args.segment) continue;
      if (args.branche && l.branche !== args.branche) continue;
      if (args.status && l.status !== args.status) continue;
      if (args.plz && !l.plz.startsWith(args.plz)) continue;
      if (args.scoreMin !== undefined && l.score < args.scoreMin) continue;
      if (args.scoreMax !== undefined && l.score > args.scoreMax) continue;
      if (args.searchQuery) {
        const search = args.searchQuery.toLowerCase();
        if (!l.firma.toLowerCase().includes(search) &&
            !l.ort.toLowerCase().includes(search) &&
            !l.email.toLowerCase().includes(search)) continue;
      }
      allFiltered.push(l);
    }

    // Sort
    const sortBy = (args.sortBy || "score") as string;
    const sortDir = args.sortDir === "asc" ? 1 : -1;
    allFiltered.sort((a: any, b: any) => {
      const va = a[sortBy] ?? "";
      const vb = b[sortBy] ?? "";
      if (typeof va === "number" && typeof vb === "number") return (va - vb) * sortDir;
      return String(va).localeCompare(String(vb)) * sortDir;
    });

    const total = allFiltered.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const start = (page - 1) * pageSize;
    const leads = allFiltered.slice(start, start + pageSize);

    return { leads, total, page, totalPages };
  },
});

export const topAndRecent = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 10;
    // Use score index for top leads (desc order)
    const byScore = await ctx.db.query("leads").withIndex("by_score").order("desc").take(limit);
    // Use creation time for recent leads (desc = newest first)
    const byDate = await ctx.db.query("leads").order("desc").take(limit);
    return { topLeads: byScore, recentLeads: byDate };
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

// Patch: nur übergebene Felder aktualisieren (für Enrichment)
export const patch = mutation({
  args: {
    id: v.id("leads"),
    kiZusammenfassung: v.optional(v.string()),
    kiZielgruppe: v.optional(v.string()),
    kiOnlineAuftritt: v.optional(v.string()),
    kiSchwaechen: v.optional(v.string()),
    kiChancen: v.optional(v.string()),
    kiAnsprache: v.optional(v.string()),
    kiAnspracheSig: v.optional(v.string()),
    kiScore: v.optional(v.number()),
    kiScoreBegruendung: v.optional(v.string()),
    kiSegment: v.optional(v.string()),
    kiAnalysiert: v.optional(v.boolean()),
    kiAnalysiertAm: v.optional(v.string()),
    score: v.optional(v.number()),
    segment: v.optional(v.union(v.literal("HOT"), v.literal("WARM"), v.literal("COLD"), v.literal("DISQUALIFIED"))),
    tags: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const { id, ...fields } = args;
    // Filter undefined values
    const data: Record<string, unknown> = {};
    for (const [k, val] of Object.entries(fields)) {
      if (val !== undefined) data[k] = val;
    }
    await ctx.db.patch(id, data);
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
