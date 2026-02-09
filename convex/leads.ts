import { query, mutation, action, internalQuery, internalMutation } from "./_generated/server";
import { v } from "convex/values";
import { internal } from "./_generated/api";

// ---- Helpers ----

function sanitizeKey(s: string): string {
  const map: Record<string, string> = {
    "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue",
    "\u00c4": "Ae", "\u00d6": "Oe", "\u00dc": "Ue", "\u00df": "ss",
  };
  return s.replace(/[^\x20-\x7E]/g, (c) => map[c] || "_");
}

function scoreBucket(score: number): number {
  return Math.min(Math.floor(score / 20), 4);
}

function segmentField(seg: string): string {
  const m: Record<string, string> = { HOT: "segmentHot", WARM: "segmentWarm", COLD: "segmentCold", DISQUALIFIED: "segmentDisqualified" };
  return m[seg] || "segmentCold";
}

function statusField(st: string): string {
  const m: Record<string, string> = { Neu: "statusNeu", Kontaktiert: "statusKontaktiert", Interessiert: "statusInteressiert", Angebot: "statusAngebot", Gewonnen: "statusGewonnen", Verloren: "statusVerloren" };
  return m[st] || "statusNeu";
}

// Get or create the singleton stats doc
async function getOrCreateStats(ctx: any) {
  const existing = await ctx.db.query("leadStats").withIndex("by_key", (q: any) => q.eq("key", "global")).first();
  if (existing) return existing;
  const id = await ctx.db.insert("leadStats", {
    key: "global", total: 0, scoreSum: 0, mitKontakt: 0,
    segmentHot: 0, segmentWarm: 0, segmentCold: 0, segmentDisqualified: 0,
    statusNeu: 0, statusKontaktiert: 0, statusInteressiert: 0, statusAngebot: 0, statusGewonnen: 0, statusVerloren: 0,
    scoreDist0: 0, scoreDist1: 0, scoreDist2: 0, scoreDist3: 0, scoreDist4: 0,
    branchenJson: "{}", updatedAt: new Date().toISOString(),
  });
  return await ctx.db.get(id);
}

// Add a lead's contribution to stats
function addToStats(stats: any, lead: any, factor: number) {
  stats.total += factor;
  stats.scoreSum += (typeof lead.score === "number" ? lead.score : 0) * factor;
  if (lead.ansprechpartner && lead.ansprechpartner.length > 0) stats.mitKontakt += factor;
  const sf = segmentField(lead.segment);
  stats[sf] = (stats[sf] || 0) + factor;
  const stf = statusField(lead.status);
  stats[stf] = (stats[stf] || 0) + factor;
  const bucket = `scoreDist${scoreBucket(typeof lead.score === "number" ? lead.score : 0)}`;
  stats[bucket] = (stats[bucket] || 0) + factor;
  // Branchen
  const branchen = JSON.parse(stats.branchenJson || "{}");
  if (lead.branche) {
    branchen[lead.branche] = (branchen[lead.branche] || 0) + factor;
    if (branchen[lead.branche] <= 0) delete branchen[lead.branche];
  }
  stats.branchenJson = JSON.stringify(branchen);
  stats.updatedAt = new Date().toISOString();
}

// ---- Queries ----

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

// O(1) stats from pre-aggregated singleton - instant regardless of lead count
export const stats = query({
  args: {},
  handler: async (ctx) => {
    const s = await ctx.db.query("leadStats").withIndex("by_key", (q) => q.eq("key", "global")).first();
    if (!s) return {
      total: 0, avgScore: 0, mitKontakt: 0,
      segments: { HOT: 0, WARM: 0, COLD: 0, DISQUALIFIED: 0 },
      statuses: {}, branchen: {}, scoreDistribution: [0,0,0,0,0],
    };
    // Parse branchen and sanitize keys for safe transport
    const rawBranchen = JSON.parse(s.branchenJson || "{}");
    const branchen: Record<string, number> = {};
    for (const [k, v] of Object.entries(rawBranchen)) {
      branchen[sanitizeKey(k)] = v as number;
    }
    return {
      total: s.total,
      avgScore: s.total > 0 ? Math.round(s.scoreSum / s.total) : 0,
      mitKontakt: s.mitKontakt,
      segments: { HOT: s.segmentHot, WARM: s.segmentWarm, COLD: s.segmentCold, DISQUALIFIED: s.segmentDisqualified },
      statuses: {
        ...(s.statusNeu > 0 ? { Neu: s.statusNeu } : {}),
        ...(s.statusKontaktiert > 0 ? { Kontaktiert: s.statusKontaktiert } : {}),
        ...(s.statusInteressiert > 0 ? { Interessiert: s.statusInteressiert } : {}),
        ...(s.statusAngebot > 0 ? { Angebot: s.statusAngebot } : {}),
        ...(s.statusGewonnen > 0 ? { Gewonnen: s.statusGewonnen } : {}),
        ...(s.statusVerloren > 0 ? { Verloren: s.statusVerloren } : {}),
      },
      branchen,
      scoreDistribution: [s.scoreDist0, s.scoreDist1, s.scoreDist2, s.scoreDist3, s.scoreDist4],
    };
  },
});

// Internal: fetch one filtered page
export const _listPage = internalQuery({
  args: {
    cursor: v.union(v.string(), v.null()),
    segment: v.optional(v.string()),
    branche: v.optional(v.string()),
    searchQuery: v.optional(v.string()),
    status: v.optional(v.string()),
    scoreMin: v.optional(v.number()),
    scoreMax: v.optional(v.number()),
    plz: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const result = await ctx.db.query("leads").paginate({
      numItems: 500,
      cursor: (args.cursor ?? null) as any,
    });
    const filtered: any[] = [];
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
      filtered.push(l);
    }
    return { filtered, nextCursor: result.isDone ? null : (result.continueCursor as string) };
  },
});

// Action: paginated + filtered list across all leads
export const listPaginated = action({
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
    const allFiltered: any[] = [];

    let cursor: string | null = null;
    let done = false;
    while (!done) {
      const result: any = await ctx.runQuery(internal.leads._listPage, {
        cursor,
        segment: args.segment,
        branche: args.branche,
        searchQuery: args.searchQuery,
        status: args.status,
        scoreMin: args.scoreMin,
        scoreMax: args.scoreMax,
        plz: args.plz,
      });
      allFiltered.push(...result.filtered);
      cursor = result.nextCursor;
      done = cursor === null;
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
    const id = await ctx.db.insert("leads", args);
    // Update aggregated stats
    const s = await getOrCreateStats(ctx);
    addToStats(s, args, 1);
    await ctx.db.replace(s._id, { ...s, _id: undefined, _creationTime: undefined } as any);
    return id;
  },
});

export const update = mutation({
  args: {
    id: v.id("leads"),
    ...leadFields,
  },
  handler: async (ctx, args) => {
    const { id, ...data } = args;
    const old = await ctx.db.get(id);
    await ctx.db.replace(id, data);
    // Update stats: remove old contribution, add new
    if (old) {
      const s = await getOrCreateStats(ctx);
      addToStats(s, old, -1);
      addToStats(s, data, 1);
      await ctx.db.replace(s._id, { ...s, _id: undefined, _creationTime: undefined } as any);
    }
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
    const old = await ctx.db.get(args.id);
    await ctx.db.delete(args.id);
    if (old) {
      const s = await getOrCreateStats(ctx);
      addToStats(s, old, -1);
      await ctx.db.replace(s._id, { ...s, _id: undefined, _creationTime: undefined } as any);
    }
  },
});

export const bulkCreate = mutation({
  args: {
    leads: v.array(v.object(leadFields)),
  },
  handler: async (ctx, args) => {
    // Dedup-Check via paginated read
    const existingKeys = new Set<string>();
    const existingEmails = new Set<string>();
    let cursor: any = null;
    let done = false;
    while (!done) {
      const pg: any = cursor
        ? await ctx.db.query("leads").paginate({ numItems: 500, cursor })
        : await ctx.db.query("leads").paginate({ numItems: 500, cursor: null as any });
      for (const l of pg.page) {
        existingKeys.add(`${l.firma.toLowerCase().trim()}|${l.plz}|${l.website.toLowerCase().trim()}`);
        if (l.email) existingEmails.add(l.email.toLowerCase().trim());
      }
      done = pg.isDone;
      cursor = pg.continueCursor;
    }

    const s = await getOrCreateStats(ctx);
    const ids = [];
    let skipped = 0;
    for (const lead of args.leads) {
      const key = `${lead.firma.toLowerCase().trim()}|${lead.plz}|${lead.website.toLowerCase().trim()}`;
      if (existingKeys.has(key)) { skipped++; continue; }
      const email = lead.email?.toLowerCase().trim();
      if (email && existingEmails.has(email)) { skipped++; continue; }
      existingKeys.add(key);
      if (email) existingEmails.add(email);
      const id = await ctx.db.insert("leads", lead);
      addToStats(s, lead, 1);
      ids.push(id);
    }
    await ctx.db.replace(s._id, { ...s, _id: undefined, _creationTime: undefined } as any);
    return ids;
  },
});

export const clearAll = mutation({
  args: {},
  handler: async (ctx) => {
    let deleted = 0;
    let cursor: any = null;
    let done = false;
    while (!done) {
      const pg: any = cursor
        ? await ctx.db.query("leads").paginate({ numItems: 500, cursor })
        : await ctx.db.query("leads").paginate({ numItems: 500, cursor: null as any });
      for (const lead of pg.page) {
        await ctx.db.delete(lead._id);
        deleted++;
      }
      done = pg.isDone;
      cursor = pg.continueCursor;
    }
    // Reset stats
    const s = await ctx.db.query("leadStats").withIndex("by_key", (q) => q.eq("key", "global")).first();
    if (s) await ctx.db.delete(s._id);
    return { deleted };
  },
});

// Internal: rebuild stats from one page
export const _rebuildPage = internalQuery({
  args: { cursor: v.union(v.string(), v.null()) },
  handler: async (ctx, args) => {
    const result = await ctx.db.query("leads").paginate({
      numItems: 500,
      cursor: (args.cursor ?? null) as any,
    });
    const partial = {
      total: 0, scoreSum: 0, mitKontakt: 0,
      segmentHot: 0, segmentWarm: 0, segmentCold: 0, segmentDisqualified: 0,
      statusNeu: 0, statusKontaktiert: 0, statusInteressiert: 0, statusAngebot: 0, statusGewonnen: 0, statusVerloren: 0,
      scoreDist0: 0, scoreDist1: 0, scoreDist2: 0, scoreDist3: 0, scoreDist4: 0,
      branchen: {} as Record<string, number>,
    };
    for (const l of result.page) {
      partial.total++;
      partial.scoreSum += typeof l.score === "number" ? l.score : 0;
      if (l.ansprechpartner && l.ansprechpartner.length > 0) partial.mitKontakt++;
      const sf = segmentField(l.segment) as keyof typeof partial;
      (partial as any)[sf]++;
      const stf = statusField(l.status) as keyof typeof partial;
      (partial as any)[stf]++;
      const bucket = `scoreDist${scoreBucket(typeof l.score === "number" ? l.score : 0)}` as keyof typeof partial;
      (partial as any)[bucket]++;
      if (l.branche) partial.branchen[l.branche] = (partial.branchen[l.branche] || 0) + 1;
    }
    // Convert branchen to array to avoid umlaut key validation
    const branchenArr = Object.entries(partial.branchen);
    return { partial: { ...partial, branchen: undefined, branchenArr }, nextCursor: result.isDone ? null : (result.continueCursor as string) };
  },
});

// Internal: write rebuilt stats
export const _writeStats = internalMutation({
  args: { data: v.any() },
  handler: async (ctx, args) => {
    const existing = await ctx.db.query("leadStats").withIndex("by_key", (q) => q.eq("key", "global")).first();
    const doc = { ...args.data, key: "global", updatedAt: new Date().toISOString() };
    if (existing) {
      await ctx.db.replace(existing._id, doc);
    } else {
      await ctx.db.insert("leadStats", doc);
    }
  },
});

// Rebuild stats from scratch (run once after migration, or to fix drift)
export const rebuildStats = action({
  args: {},
  handler: async (ctx) => {
    const agg = {
      total: 0, scoreSum: 0, mitKontakt: 0,
      segmentHot: 0, segmentWarm: 0, segmentCold: 0, segmentDisqualified: 0,
      statusNeu: 0, statusKontaktiert: 0, statusInteressiert: 0, statusAngebot: 0, statusGewonnen: 0, statusVerloren: 0,
      scoreDist0: 0, scoreDist1: 0, scoreDist2: 0, scoreDist3: 0, scoreDist4: 0,
      branchenJson: "{}",
    };
    const branchenMap = new Map<string, number>();

    let cursor: string | null = null;
    let done = false;
    while (!done) {
      const page: any = await ctx.runQuery(internal.leads._rebuildPage, { cursor });
      const p = page.partial;
      agg.total += p.total;
      agg.scoreSum += p.scoreSum;
      agg.mitKontakt += p.mitKontakt;
      for (const k of ["segmentHot","segmentWarm","segmentCold","segmentDisqualified","statusNeu","statusKontaktiert","statusInteressiert","statusAngebot","statusGewonnen","statusVerloren","scoreDist0","scoreDist1","scoreDist2","scoreDist3","scoreDist4"]) {
        (agg as any)[k] += p[k] || 0;
      }
      for (const [k, v] of (p.branchenArr || [])) {
        branchenMap.set(k as string, (branchenMap.get(k as string) || 0) + (v as number));
      }
      cursor = page.nextCursor;
      done = cursor === null;
    }

    const branchen: Record<string, number> = {};
    for (const [k, v] of branchenMap) branchen[k] = v;
    agg.branchenJson = JSON.stringify(branchen);

    await ctx.runMutation(internal.leads._writeStats, { data: agg });
    return { total: agg.total, rebuilt: true };
  },
});
