import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  leads: defineTable({
    // Firma
    firma: v.string(),
    website: v.string(),
    branche: v.string(),
    groesse: v.string(),
    plz: v.string(),
    ort: v.string(),
    // Kontakt
    ansprechpartner: v.string(),
    position: v.string(),
    email: v.string(),
    telefon: v.string(),
    // Online-Präsenz
    websiteQualitaet: v.number(),
    socialMedia: v.boolean(),
    socialMediaLinks: v.string(),
    googleBewertung: v.string(),
    // Website-Content (für KI-Analyse)
    websiteText: v.optional(v.string()),
    // Analyse
    score: v.number(),
    kiZusammenfassung: v.string(),
    segment: v.union(v.literal("HOT"), v.literal("WARM"), v.literal("COLD"), v.literal("DISQUALIFIED")),
    segmentManuell: v.boolean(),
    tags: v.array(v.string()),
    // Status
    status: v.union(
      v.literal("Neu"),
      v.literal("Kontaktiert"),
      v.literal("Interessiert"),
      v.literal("Angebot"),
      v.literal("Gewonnen"),
      v.literal("Verloren")
    ),
    // Notizen
    notizen: v.string(),
    // History
    history: v.array(
      v.object({
        timestamp: v.string(),
        aktion: v.string(),
        details: v.string(),
      })
    ),
    // Timestamps
    erstelltAm: v.string(),
    bearbeitetAm: v.string(),
  })
    .index("by_segment", ["segment"])
    .index("by_status", ["status"])
    .index("by_score", ["score"])
    .index("by_branche", ["branche"])
    .index("by_plz", ["plz"]),
});
