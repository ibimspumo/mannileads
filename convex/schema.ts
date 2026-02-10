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
    .index("by_plz", ["plz"])
    .index("by_email", ["email"])
    .index("by_website", ["website"]),

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

  // ===== EMAIL INTEGRATION =====

  // Email Accounts — Multi-Account SES Config
  emailAccounts: defineTable({
    name: v.string(),               // "Schwerin ist Geil", "okapi Design", etc.
    fromEmail: v.string(),          // kontakt@schwerinistgeil.de
    fromName: v.string(),           // "Manfred Bellmann"
    signatureHtml: v.string(),      // HTML Signatur
    // SES Credentials (encrypted in production, plain for now)
    sesAccessKey: v.string(),
    sesSecretKey: v.string(),
    sesRegion: v.string(),          // us-east-1
    // Status
    active: v.boolean(),
    verified: v.boolean(),          // SES Domain/Email verified?
    // Stats
    totalSent: v.number(),
    lastSentAt: v.optional(v.string()),
    // Meta
    createdAt: v.string(),
    updatedAt: v.string(),
  })
    .index("by_active", ["active"])
    .index("by_email", ["fromEmail"]),

  // Email Templates — Kampagnen-Templates
  emailTemplates: defineTable({
    name: v.string(),
    subject: v.string(),            // Mit Platzhaltern: "Hallo {{ansprechpartner}}"
    htmlBody: v.string(),           // HTML mit {{firma}}, {{branche}}, etc.
    // Platzhalter-Info für UI
    placeholders: v.array(v.string()), // ["firma", "ansprechpartner", "branche", ...]
    // Meta
    createdAt: v.string(),
    updatedAt: v.string(),
    createdBy: v.optional(v.string()),
  }),

  // Email Campaigns — Kampagnen
  emailCampaigns: defineTable({
    name: v.string(),
    templateId: v.id("emailTemplates"),
    accountId: v.id("emailAccounts"),
    // Targeting/Filters (als JSON gespeichert)
    filtersJson: v.string(),        // { branche: "Restaurant", plz: "19055", score: { min: 60 } }
    // Status
    status: v.union(
      v.literal("draft"),
      v.literal("queued"),
      v.literal("sending"),
      v.literal("sent"),
      v.literal("paused")
    ),
    // Stats
    totalLeads: v.number(),         // Gefilterte Leads
    totalQueued: v.number(),
    totalSent: v.number(),
    totalDelivered: v.number(),
    totalOpened: v.number(),
    totalClicked: v.number(),
    totalBounced: v.number(),
    totalComplained: v.number(),
    // Rates (calculated)
    openRate: v.optional(v.number()),
    clickRate: v.optional(v.number()),
    bounceRate: v.optional(v.number()),
    // Timing
    createdAt: v.string(),
    startedAt: v.optional(v.string()),
    completedAt: v.optional(v.string()),
  })
    .index("by_status", ["status"])
    .index("by_account", ["accountId"])
    .index("by_template", ["templateId"]),

  // Email Sends — Einzelne Email-Versand-Jobs
  emailSends: defineTable({
    campaignId: v.id("emailCampaigns"),
    leadId: v.id("leads"),
    accountId: v.id("emailAccounts"),
    // Email-Inhalt (rendered)
    to: v.string(),
    subject: v.string(),
    htmlBody: v.string(),           // Mit eingefügtem Tracking-Pixel + ersetzten Links
    // Status
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
    // SES Response
    sesMessageId: v.optional(v.string()),
    errorMessage: v.optional(v.string()),
    // Timestamps
    queuedAt: v.string(),
    sentAt: v.optional(v.string()),
    deliveredAt: v.optional(v.string()),
    openedAt: v.optional(v.string()),
    clickedAt: v.optional(v.string()),
    bouncedAt: v.optional(v.string()),
  })
    .index("by_campaign", ["campaignId"])
    .index("by_lead", ["leadId"])
    .index("by_status", ["status"])
    .index("by_queued", ["queuedAt"]),

  // Email Events — Tracking Events (Opens, Clicks, Bounces)
  emailEvents: defineTable({
    sendId: v.id("emailSends"),
    type: v.union(
      v.literal("open"),
      v.literal("click"),
      v.literal("bounce"),
      v.literal("complaint")
    ),
    // Metadata
    metadata: v.optional(v.string()), // JSON: { url: "...", userAgent: "...", ip: "..." }
    // Timestamps
    timestamp: v.string(),
  })
    .index("by_send", ["sendId"])
    .index("by_type", ["type"])
    .index("by_timestamp", ["timestamp"]),
});
