# 🔍 ManniLeads — Automatische Lead-Generierung

> Firmen finden, analysieren, speichern. Automatisch.

## Was ist das?

ManniLeads ist ein automatisierter Lead-Scraper mit CRM-Dashboard. Er findet lokale Unternehmen in bestimmten Regionen, analysiert sie und speichert sie in einer Datenbank — bereit zum Kontaktieren.

**Erster Use-Case:** Potenzielle Werbekunden für [schwerinistgeil.de](https://schwerinistgeil.de)

## Tech-Stack

| Komponente | Technologie |
|---|---|
| **Frontend** | SvelteKit 5 + Tailwind CSS |
| **Backend/DB** | Convex (Real-Time, serverless) |
| **Hosting** | Vercel (auto-deploy bei Push) |
| **Suche** | Brave Search API (direkt, kein LLM nötig) |
| **Analyse** | Gemini Flash via OpenRouter (~0.001€/Lead) |
| **Sprache** | TypeScript |

## Architektur

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐
│ Brave Search │────▶│ Python Script │────▶│  Convex   │
│    API       │     │ (Scrape +    │     │ (Database) │
└─────────────┘     │  Regex Parse) │     └─────┬─────┘
                    └──────┬───────┘           │
                           │                    │
                    ┌──────▼───────┐     ┌─────▼─────┐
                    │ Gemini Flash  │     │ SvelteKit  │
                    │ (Analyse nur) │     │ Dashboard  │
                    └──────────────┘     └───────────┘
```

**90% ohne KI:** Suche + Crawling komplett ohne LLM. Nur die finale Firmen-Analyse nutzt Gemini Flash.

## Suchstrategie

- **PLZ × Branche** Kombinationen für maximale Abdeckung
- Schwerin: PLZ 19053, 19055, 19057, 19059, 19061, 19063
- ~15-20 Branchen pro PLZ = bis zu 1.800 potenzielle Leads
- Rotierend: 3-5 Queries pro Run (alle 30 Min)
- Dedup: Keine Duplikate in der DB

## Datenbank

~50 Felder pro Lead:
- **Stammdaten:** Firma, Branche, Adresse, Kontakt, Website
- **Ansprechpartner:** Name, Position, Email, LinkedIn
- **Online-Präsenz:** Social Media, Google-Bewertungen, Website-Qualität
- **Lead-Scoring:** KI-basierter Score (1-100), Status-Tracking
- **Werbepotenzial:** Relevanz, Budget-Schätzung, Empfehlung

## Features (geplant)

- [ ] Dashboard mit Login
- [ ] Firmen-Liste mit Filtern (PLZ, Branche, Score, Status)
- [ ] Detail-Ansicht pro Firma
- [ ] Automatischer Scraper (Cron, alle 30 Min)
- [ ] KI-Analyse pro Lead (Gemini Flash)
- [ ] Export (CSV)
- [ ] Scraping-Fortschritt-Tracker
- [ ] Statistiken & Charts

## Setup

```bash
# Dependencies
npm install

# Convex
npx convex dev

# Dev Server
npm run dev
```

## Team

- **Timo** ([@ibimspumo](https://github.com/ibimspumo)) — Konzept & Richtung
- **Manfred** ([@agentz-manfred](https://github.com/agentz-manfred)) — Entwicklung & Automatisierung

---

*Ein AgentZ Projekt 🚀*
