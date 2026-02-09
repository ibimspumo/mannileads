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
    // Analyse (Scraper)
    score: v.number(),
    kiZusammenfassung: v.string(),
    segment: v.union(v.literal("HOT"), v.literal("WARM"), v.literal("COLD"), v.literal("DISQUALIFIED")),
    segmentManuell: v.boolean(),
    tags: v.array(v.string()),
    // KI-Analyse (Gemini)
    kiAnalysiert: v.optional(v.boolean()),
    kiAnalysiertAm: v.optional(v.string()),
    kiZielgruppe: v.optional(v.string()),        // Wer sind deren Kunden?
    kiOnlineAuftritt: v.optional(v.string()),     // Bewertung des Online-Auftritts
    kiSchwaechen: v.optional(v.string()),          // Wo hapert's? (= unser Ansatzpunkt)
    kiChancen: v.optional(v.string()),             // Konkrete Chancen für AgentZ
    kiWettbewerb: v.optional(v.string()),          // Wettbewerbssituation
    kiAnsprache: v.optional(v.string()),           // Vorgeschlagener Pitch/Ansprache (AgentZ)
    kiAnspracheSig: v.optional(v.string()),        // Pitch für Schwerin ist Geil Werbung
    kiScore: v.optional(v.number()),               // KI-Score 0-100
    kiScoreBegruendung: v.optional(v.string()),    // Warum dieser Score?
    kiSegment: v.optional(v.string()),             // KI-Segment-Empfehlung
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

  // Aggregierte Stats - wird inkrementell aktualisiert bei jedem Lead-Insert/Update/Delete
  // Singleton: es gibt genau ein Dokument mit key="global"
  leadStats: defineTable({
    key: v.string(), // "global"
    total: v.number(),
    scoreSum: v.number(),
    mitKontakt: v.number(),
    segmentHot: v.number(),
    segmentWarm: v.number(),
    segmentCold: v.number(),
    segmentDisqualified: v.number(),
    statusNeu: v.number(),
    statusKontaktiert: v.number(),
    statusInteressiert: v.number(),
    statusAngebot: v.number(),
    statusGewonnen: v.number(),
    statusVerloren: v.number(),
    scoreDist0: v.number(), // 0-19
    scoreDist1: v.number(), // 20-39
    scoreDist2: v.number(), // 40-59
    scoreDist3: v.number(), // 60-79
    scoreDist4: v.number(), // 80-100
    // Branchen as JSON string (Convex doesn't allow umlaut keys in objects)
    branchenJson: v.string(),
    updatedAt: v.string(),
  }).index("by_key", ["key"]),

  // Coverage-Tracking: welche PLZ × Branche Kombinationen wurden gescrapt
  coverage: defineTable({
    plz: v.string(),
    ort: v.string(),
    branche: v.string(),
    kategorie: v.string(),
    // Ergebnisse
    suchergebnisse: v.number(),    // Anzahl Brave-Ergebnisse
    leadsGefunden: v.number(),     // Davon als Lead gespeichert
    leadsGefiltert: v.number(),    // Davon gefiltert (Spam, kein Impressum, etc.)
    // Timing
    gescraptAm: v.string(),
    dauerSekunden: v.optional(v.number()),
  })
    .index("by_plz", ["plz"])
    .index("by_branche", ["branche"])
    .index("by_plz_branche", ["plz", "branche"]),
});
