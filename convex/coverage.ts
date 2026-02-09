import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// ---- Queries ----

export const getAll = query({
  handler: async (ctx) => {
    return await ctx.db.query("coverage").collect();
  },
});

export const getByPlz = query({
  args: { plz: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("coverage")
      .withIndex("by_plz", (q) => q.eq("plz", args.plz))
      .collect();
  },
});

export const stats = query({
  handler: async (ctx) => {
    const all = await ctx.db.query("coverage").collect();
    const plzSet = new Set(all.map((c) => c.plz));
    const branchenSet = new Set(all.map((c) => c.branche));
    return {
      totalCombos: all.length,
      plzCount: plzSet.size,
      branchenCount: branchenSet.size,
      totalSuchergebnisse: all.reduce((s, c) => s + c.suchergebnisse, 0),
      totalLeadsGefunden: all.reduce((s, c) => s + c.leadsGefunden, 0),
      totalLeadsGefiltert: all.reduce((s, c) => s + c.leadsGefiltert, 0),
    };
  },
});

// ---- Mutations ----

export const upsert = mutation({
  args: {
    plz: v.string(),
    ort: v.string(),
    branche: v.string(),
    kategorie: v.string(),
    suchergebnisse: v.number(),
    leadsGefunden: v.number(),
    leadsGefiltert: v.number(),
    gescraptAm: v.string(),
    dauerSekunden: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    // Check if exists
    const existing = await ctx.db
      .query("coverage")
      .withIndex("by_plz_branche", (q) => q.eq("plz", args.plz).eq("branche", args.branche))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        suchergebnisse: args.suchergebnisse,
        leadsGefunden: args.leadsGefunden,
        leadsGefiltert: args.leadsGefiltert,
        gescraptAm: args.gescraptAm,
        dauerSekunden: args.dauerSekunden,
      });
      return existing._id;
    }

    return await ctx.db.insert("coverage", args);
  },
});

export const bulkUpsert = mutation({
  args: {
    items: v.array(
      v.object({
        plz: v.string(),
        ort: v.string(),
        branche: v.string(),
        kategorie: v.string(),
        suchergebnisse: v.number(),
        leadsGefunden: v.number(),
        leadsGefiltert: v.number(),
        gescraptAm: v.string(),
        dauerSekunden: v.optional(v.number()),
      })
    ),
  },
  handler: async (ctx, args) => {
    let created = 0;
    let updated = 0;
    for (const item of args.items) {
      const existing = await ctx.db
        .query("coverage")
        .withIndex("by_plz_branche", (q) => q.eq("plz", item.plz).eq("branche", item.branche))
        .first();

      if (existing) {
        await ctx.db.patch(existing._id, {
          suchergebnisse: item.suchergebnisse,
          leadsGefunden: item.leadsGefunden,
          leadsGefiltert: item.leadsGefiltert,
          gescraptAm: item.gescraptAm,
          dauerSekunden: item.dauerSekunden,
        });
        updated++;
      } else {
        await ctx.db.insert("coverage", item);
        created++;
      }
    }
    return { created, updated };
  },
});

export const clearAll = mutation({
  handler: async (ctx) => {
    const all = await ctx.db.query("coverage").collect();
    for (const item of all) {
      await ctx.db.delete(item._id);
    }
    return { deleted: all.length };
  },
});
