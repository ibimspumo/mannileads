#!/usr/bin/env python3
"""
ManniLeads Analyse — Stufe 2: KI-Klassifizierung
Holt Leads aus Convex, analysiert sie mit Gemini Flash (OpenRouter)
und schreibt die Ergebnisse zurück.

Verwendung:
  python3 scripts/analyze.py                    # Alle unanalysierten
  python3 scripts/analyze.py --limit 10         # Nur 10 Stück
  python3 scripts/analyze.py --reanalyze        # Auch bereits analysierte
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

try:
    import requests
except ImportError:
    print("FEHLER: 'requests' nicht installiert. Bitte: pip3 install requests")
    sys.exit(1)

# ---- Konfiguration ----

CONVEX_URL = "https://energetic-civet-402.convex.cloud"
CONVEX_API_KEY = "ml_scraper_2026_xR9kT4mQ"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemini-2.5-flash"

# ---- Logging ----

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("analyze")

# ---- API Keys laden ----

def load_openrouter_key() -> str:
    """Lädt den OpenRouter API Key."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    
    key_path = Path.home() / ".openclaw" / "workspace" / "scripts" / ".openrouter_key"
    if key_path.exists():
        content = key_path.read_text().strip()
        if content:
            return content
    
    log.error("Kein OpenRouter API Key gefunden!")
    log.error("Setze OPENROUTER_API_KEY oder trage Key in scripts/.openrouter_key ein")
    sys.exit(1)


# ---- Convex API ----

def fetch_leads_from_convex() -> List[dict]:
    """Holt alle Leads aus Convex."""
    url = f"{CONVEX_URL}/api/leads"
    headers = {"X-API-Key": CONVEX_API_KEY}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("leads", [])
    except requests.RequestException as e:
        log.error(f"Convex API Fehler: {e}")
        return []


def update_lead_in_convex(lead_id: str, updates: dict) -> bool:
    """Aktualisiert einen Lead in Convex."""
    url = f"{CONVEX_URL}/api/leads"
    headers = {
        "X-API-Key": CONVEX_API_KEY,
        "Content-Type": "application/json",
    }
    
    payload = {"id": lead_id, **updates}
    
    try:
        resp = requests.patch(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        log.error(f"Update-Fehler für {lead_id}: {e}")
        return False


# ---- KI-Analyse ----

def build_analysis_prompt(lead: dict) -> str:
    """Erstellt den Analyse-Prompt für das LLM."""
    return f"""Du bist ein Experte für lokale Unternehmens-Akquise in Deutschland.
Analysiere den folgenden Lead und liefere eine strukturierte Bewertung.

LEAD-DATEN:
- Firma: {lead.get('firma', 'Unbekannt')}
- Branche: {lead.get('branche', 'Unbekannt')}
- PLZ/Ort: {lead.get('plz', '')} {lead.get('ort', '')}
- Website: {lead.get('website', 'Keine')}
- Website-Qualität: {lead.get('websiteQualitaet', 0)}/5
- E-Mail: {lead.get('email', 'Keine')}
- Telefon: {lead.get('telefon', 'Keine')}
- Ansprechpartner: {lead.get('ansprechpartner', 'Unbekannt')}
- Position: {lead.get('position', 'Unbekannt')}
- Social Media: {lead.get('socialMedia', False)}
- Social Media Links: {lead.get('socialMediaLinks', 'Keine')}
- Google-Bewertung: {lead.get('googleBewertung', 'Keine')}
- Bisheriger Score: {lead.get('score', 0)}
- Notizen: {lead.get('notizen', '')[:300]}

AUFGABE:
Analysiere dieses Unternehmen als potenziellen Kunden für eine Digitalagentur 
(Webdesign, SEO, Social Media Marketing, Online-Präsenz).

Antworte NUR mit einem JSON-Objekt (kein Markdown, kein Text drumrum):
{{
  "zusammenfassung": "2-3 Sätze über das Unternehmen und seine Online-Präsenz",
  "score": <0-100, begründeter Score>,
  "score_begruendung": "Kurze Begründung für den Score",
  "segment": "<HOT|WARM|COLD|DISQUALIFIED>",
  "tags": ["tag1", "tag2", "tag3"],
  "akquise_chance": "Einschätzung der Akquise-Chance und empfohlene Ansprache"
}}

SCORING-RICHTLINIEN:
- 80-100 (HOT): Klarer Bedarf, erreichbar, Budget wahrscheinlich
- 50-79 (WARM): Potenzial vorhanden, aber Unsicherheiten
- 20-49 (COLD): Wenig Potenzial oder schwer erreichbar
- 0-19 (DISQUALIFIED): Kein sinnvoller Lead (z.B. bereits top Website, falsche Branche)"""


def analyze_lead_with_llm(lead: dict, api_key: str) -> Optional[dict]:
    """Analysiert einen Lead mit Gemini Flash via OpenRouter."""
    prompt = build_analysis_prompt(lead)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 800,
    }
    
    try:
        resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        content = data["choices"][0]["message"]["content"].strip()
        
        # JSON aus Antwort extrahieren (falls in Markdown-Block)
        if "```" in content:
            json_match = content.split("```")[1]
            if json_match.startswith("json"):
                json_match = json_match[4:]
            content = json_match.strip()
        
        result = json.loads(content)
        return result
        
    except json.JSONDecodeError as e:
        log.warning(f"JSON-Parse-Fehler: {e}")
        log.debug(f"Antwort: {content[:500]}")
        return None
    except requests.RequestException as e:
        log.error(f"OpenRouter API Fehler: {e}")
        return None
    except (KeyError, IndexError) as e:
        log.error(f"Unerwartete API-Antwort: {e}")
        return None


# ---- Hauptlogik ----

def run_analysis(limit: Optional[int] = None, reanalyze: bool = False):
    """Analysiert Leads mit KI."""
    api_key = load_openrouter_key()
    
    log.info("Lade Leads aus Convex...")
    leads = fetch_leads_from_convex()
    
    if not leads:
        log.info("Keine Leads gefunden.")
        return
    
    log.info(f"{len(leads)} Leads geladen")
    
    # Filtern: nur unanalysierte (oder alle bei --reanalyze)
    if not reanalyze:
        leads = [l for l in leads if not l.get("kiZusammenfassung")]
        log.info(f"{len(leads)} davon noch nicht analysiert")
    
    if limit:
        leads = leads[:limit]
        log.info(f"Limitiert auf {limit} Leads")
    
    if not leads:
        log.info("Nichts zu analysieren.")
        return
    
    success_count = 0
    error_count = 0
    
    for i, lead in enumerate(leads, 1):
        firma = lead.get("firma", "Unbekannt")
        lead_id = lead.get("_id")
        
        log.info(f"[{i}/{len(leads)}] Analysiere: {firma}")
        
        result = analyze_lead_with_llm(lead, api_key)
        
        if result:
            # Updates zusammenstellen
            now = datetime.now().isoformat()
            
            # Bestehende Daten für das vollständige Update zusammenstellen
            updates = {
                # Alle bestehenden Felder beibehalten
                "firma": lead.get("firma", ""),
                "website": lead.get("website", ""),
                "branche": lead.get("branche", ""),
                "groesse": lead.get("groesse", ""),
                "plz": lead.get("plz", ""),
                "ort": lead.get("ort", ""),
                "ansprechpartner": lead.get("ansprechpartner", ""),
                "position": lead.get("position", ""),
                "email": lead.get("email", ""),
                "telefon": lead.get("telefon", ""),
                "websiteQualitaet": lead.get("websiteQualitaet", 1),
                "socialMedia": lead.get("socialMedia", False),
                "socialMediaLinks": lead.get("socialMediaLinks", ""),
                "googleBewertung": lead.get("googleBewertung", ""),
                "segmentManuell": lead.get("segmentManuell", False),
                "status": lead.get("status", "Neu"),
                "erstelltAm": lead.get("erstelltAm", now),
                # KI-Analyse-Ergebnisse
                "kiZusammenfassung": result.get("zusammenfassung", ""),
                "score": result.get("score", lead.get("score", 0)),
                "segment": result.get("segment", lead.get("segment", "COLD")),
                "tags": list(set(lead.get("tags", []) + result.get("tags", []))),
                "notizen": lead.get("notizen", "") + f"\n\n[KI-Analyse {now[:10]}]\n{result.get('akquise_chance', '')}",
                "history": lead.get("history", []) + [{
                    "timestamp": now,
                    "aktion": "KI-Analyse",
                    "details": f"Score: {result.get('score', '?')}, Segment: {result.get('segment', '?')}"
                }],
                "bearbeitetAm": now,
            }
            
            # Segment nicht überschreiben wenn manuell gesetzt
            if lead.get("segmentManuell"):
                updates["segment"] = lead["segment"]
            
            if update_lead_in_convex(lead_id, updates):
                log.info(f"  ✓ Score: {result.get('score')}, Segment: {result.get('segment')}")
                success_count += 1
            else:
                log.error(f"  ✗ Update fehlgeschlagen")
                error_count += 1
        else:
            log.warning(f"  ✗ Analyse fehlgeschlagen")
            error_count += 1
        
        # Kurze Pause zwischen Anfragen
        time.sleep(0.5)
    
    log.info(f"\n{'='*50}")
    log.info(f"Analyse abgeschlossen: {success_count} erfolgreich, {error_count} Fehler")


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(
        description="ManniLeads Analyse — KI-gestützte Lead-Klassifizierung"
    )
    parser.add_argument("--limit", type=int, default=None,
                       help="Maximale Anzahl zu analysierender Leads")
    parser.add_argument("--reanalyze", action="store_true",
                       help="Auch bereits analysierte Leads neu bewerten")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Ausführliche Ausgabe")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    log.info("=" * 50)
    log.info("ManniLeads Analyse v1.0")
    log.info("=" * 50)
    
    run_analysis(limit=args.limit, reanalyze=args.reanalyze)


if __name__ == "__main__":
    main()
