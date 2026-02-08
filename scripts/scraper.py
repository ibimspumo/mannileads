#!/usr/bin/env python3
"""
ManniLeads Scraper — Stufe 1: Daten sammeln
Sucht lokale Unternehmen via Brave Search, extrahiert Kontaktdaten und
schreibt Ergebnisse in die Convex-Datenbank.

Verwendung:
  python3 scripts/scraper.py                           # Default: Schwerin
  python3 scripts/scraper.py --plz 19053,19055         # Bestimmte PLZ
  python3 scripts/scraper.py --branchen "Friseur,Arzt" # Bestimmte Branchen
  python3 scripts/scraper.py --dry-run                 # Nur suchen, nicht in DB
  python3 scripts/scraper.py --output results.json     # Zusätzlich als JSON
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

try:
    import requests
except ImportError:
    print("FEHLER: 'requests' nicht installiert. Bitte: pip3 install requests")
    sys.exit(1)

# ---- Konfiguration ----

DEFAULT_PLZ = ["19053", "19055", "19057", "19059", "19061", "19063"]
DEFAULT_BRANCHEN = [
    "Friseur", "Restaurant", "Autowerkstatt", "Zahnarzt", "Rechtsanwalt",
    "Steuerberater", "Immobilienmakler", "Handwerker", "Elektriker",
    "Maler", "Dachdecker", "Fitnessstudio", "Bäckerei", "Apotheke",
    "Optiker", "Physiotherapie", "Hotel", "Café", "Blumenladen", "Fahrschule"
]

# Schwerin als Default-Ort für die PLZ-Region
PLZ_ORT_MAP = {
    "19053": "Schwerin", "19055": "Schwerin", "19057": "Schwerin",
    "19059": "Schwerin", "19061": "Schwerin", "19063": "Schwerin",
}

CONVEX_URL = "https://energetic-civet-402.convex.cloud"
CONVEX_API_KEY = "ml_scraper_2026_xR9kT4mQ"

STATE_FILE = Path(__file__).parent / "scraper_state.json"
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
RATE_LIMIT_SECONDS = 1.1  # etwas über 1s für Sicherheit

# ---- Logging ----

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("scraper")

# ---- State-Tracking ----

def load_state() -> dict:
    """Lädt den Scraper-State (welche PLZ×Branche schon abgearbeitet)."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            log.warning("State-Datei beschädigt, starte frisch")
    return {
        "completed": {},   # {"19053": ["Friseur", "Restaurant", ...]}
        "scraped_urls": [], # Alle bisher gescrapten URLs
        "stats": {
            "total_leads": 0,
            "total_searches": 0,
            "last_run": None,
        }
    }


def save_state(state: dict):
    """Speichert den Scraper-State."""
    state["stats"]["last_run"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def mark_completed(state: dict, plz: str, branche: str):
    """Markiert eine PLZ×Branche-Kombi als abgearbeitet."""
    if plz not in state["completed"]:
        state["completed"][plz] = []
    if branche not in state["completed"][plz]:
        state["completed"][plz].append(branche)


def is_completed(state: dict, plz: str, branche: str) -> bool:
    """Prüft ob eine PLZ×Branche-Kombi schon abgearbeitet ist."""
    return branche in state["completed"].get(plz, [])


def add_scraped_url(state: dict, url: str):
    """Merkt sich eine gescrapte URL."""
    if url not in state["scraped_urls"]:
        state["scraped_urls"].append(url)


# ---- Brave Search API Key laden ----

def load_brave_key() -> str:
    """Lädt den Brave API Key aus Datei oder Environment Variable."""
    # Environment Variable hat Vorrang
    key = os.environ.get("BRAVE_API_KEY", "").strip()
    if key:
        return key
    
    # Datei prüfen
    key_paths = [
        Path.home() / ".openclaw" / "workspace" / "scripts" / ".brave_search_key",
        Path(__file__).parent.parent.parent / "scripts" / ".brave_search_key",
    ]
    for p in key_paths:
        if p.exists():
            content = p.read_text().strip()
            # Ignoriere Kommentare und Platzhalter
            lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
            if lines:
                return lines[0]
    
    log.error("Kein Brave Search API Key gefunden!")
    log.error("Setze BRAVE_API_KEY oder trage Key in scripts/.brave_search_key ein")
    log.error("Registrierung: https://brave.com/search/api/")
    sys.exit(1)


# ---- Brave Search ----

def brave_search(query: str, api_key: str, count: int = 10) -> List[dict]:
    """Führt eine Brave Search Suche durch."""
    headers = {"X-Subscription-Token": api_key, "Accept": "application/json"}
    params = {"q": query, "count": count, "country": "de", "search_lang": "de"}
    
    try:
        resp = requests.get(BRAVE_ENDPOINT, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("web", {}).get("results", [])
        return results
    except requests.RequestException as e:
        log.warning(f"Brave Search Fehler für '{query}': {e}")
        return []


# ---- Website-Analyse ----

def fetch_page(url: str, timeout: int = 10) -> Optional[str]:
    """Holt den HTML-Inhalt einer Seite."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ManniLeads/1.0)"}
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def find_impressum_url(base_url: str, html: str) -> Optional[str]:
    """Sucht nach Impressum/Kontakt-Links auf der Seite."""
    patterns = [
        r'href=["\']([^"\']*(?:impressum|imprint|kontakt|contact|about|ueber-uns)[^"\']*)["\']'
    ]
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            if match.startswith("http"):
                return match
            elif match.startswith("/"):
                parsed = urllib.parse.urlparse(base_url)
                return f"{parsed.scheme}://{parsed.netloc}{match}"
    return None


def extract_emails(text: str) -> List[str]:
    """Extrahiert E-Mail-Adressen aus Text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    # Filtere offensichtliche Nicht-Emails
    filtered = [e for e in emails if not any(x in e.lower() for x in [
        '.png', '.jpg', '.gif', '.css', '.js', 'wixpress', 'sentry', 'webpack'
    ])]
    return list(set(filtered))[:3]  # Max 3


def extract_phones(text: str) -> List[str]:
    """Extrahiert Telefonnummern aus Text."""
    patterns = [
        r'(?:Tel\.?|Telefon|Phone|Fon|Mobil|Handy)[:\s]*([+\d\s\-/()]{8,20})',
        r'(?:\+49|0)\s*\d{2,4}[\s\-/]*\d{3,8}[\s\-/]*\d{0,6}',
    ]
    phones = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        phones.extend(matches)
    # Bereinigen
    cleaned = []
    for phone in phones:
        phone = re.sub(r'[^\d+\-/() ]', '', phone).strip()
        if len(re.sub(r'\D', '', phone)) >= 6:
            cleaned.append(phone)
    return list(set(cleaned))[:2]


def extract_names(text: str) -> List[dict]:
    """Versucht Ansprechpartner-Namen zu extrahieren."""
    # Typische Muster: "Geschäftsführer: Max Mustermann"
    patterns = [
        r'(?:Geschäftsführ(?:er|erin|ung)|Inhaber(?:in)?|Leitung|Ansprechpartner(?:in)?|CEO|Gründer(?:in)?)[:\s]+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)',
        r'(?:Dr\.|Prof\.|Dipl\.)[^<\n]{0,5}([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)',
    ]
    names = []
    for p in patterns:
        matches = re.finditer(p, text)
        for m in matches:
            name = m.group(1).strip() if m.lastindex else m.group(0).strip()
            if 3 < len(name) < 50:
                # Position erraten
                full_match = m.group(0)
                position = ""
                for title in ["Geschäftsführer", "Geschäftsführerin", "Inhaber", "Inhaberin", "CEO", "Gründer"]:
                    if title.lower() in full_match.lower():
                        position = title
                        break
                names.append({"name": name, "position": position})
    return names[:1]  # Nur den ersten/besten


def extract_social_media(html: str) -> dict:
    """Findet Social-Media-Links."""
    social = {}
    patterns = {
        "facebook": r'href=["\']([^"\']*facebook\.com/[^"\']+)["\']',
        "instagram": r'href=["\']([^"\']*instagram\.com/[^"\']+)["\']',
        "linkedin": r'href=["\']([^"\']*linkedin\.com/[^"\']+)["\']',
    }
    for platform, pattern in patterns.items():
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            social[platform] = match.group(1)
    return social


def assess_website_quality(url: str, html: Optional[str]) -> int:
    """Bewertet die Website-Qualität (1-5)."""
    score = 1  # Basis
    
    if not html:
        return 1
    
    # SSL?
    if url.startswith("https"):
        score += 1
    
    # Impressum vorhanden?
    if re.search(r'impressum|imprint', html, re.IGNORECASE):
        score += 1
    
    # Social Media Links?
    if re.search(r'facebook\.com|instagram\.com|linkedin\.com', html, re.IGNORECASE):
        score += 0.5
    
    # Responsive Meta-Tag?
    if 'viewport' in html.lower():
        score += 0.5
    
    return min(int(round(score)), 5)


def calculate_score(lead: dict) -> int:
    """Berechnet einen vorläufigen Lead-Score (0-100)."""
    score = 30  # Basis: Firma existiert und hat Website
    
    # Website-Qualität (max +20)
    score += lead.get("websiteQualitaet", 1) * 4
    
    # Hat Kontaktdaten (max +20)
    if lead.get("email"):
        score += 10
    if lead.get("telefon"):
        score += 5
    if lead.get("ansprechpartner"):
        score += 5
    
    # Social Media (+10)
    if lead.get("socialMedia"):
        score += 10
    
    # Google-Bewertung (+10)
    bewertung = lead.get("googleBewertung", "")
    if bewertung:
        try:
            rating = float(bewertung.split("/")[0].replace(",", "."))
            if rating >= 4.0:
                score += 10
            elif rating >= 3.0:
                score += 5
        except (ValueError, IndexError):
            pass
    
    return min(max(score, 0), 100)


def determine_segment(score: int) -> str:
    """Bestimmt das Segment basierend auf dem Score."""
    if score >= 70:
        return "HOT"
    elif score >= 50:
        return "WARM"
    elif score >= 30:
        return "COLD"
    else:
        return "DISQUALIFIED"


# ---- Convex API ----

def push_to_convex(leads: List[dict]) -> bool:
    """Schreibt Leads via HTTP API in Convex."""
    if not leads:
        return True
    
    url = f"{CONVEX_URL}/api/leads/bulk"
    headers = {
        "X-API-Key": CONVEX_API_KEY,
        "Content-Type": "application/json",
    }
    
    try:
        # In Batches von 20 senden
        batch_size = 20
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            resp = requests.post(url, json={"leads": batch}, headers=headers, timeout=30)
            resp.raise_for_status()
            log.info(f"  Batch {i//batch_size + 1}: {len(batch)} Leads geschrieben")
        return True
    except requests.RequestException as e:
        log.error(f"Convex API Fehler: {e}")
        if hasattr(e, 'response') and e.response is not None:
            log.error(f"  Response: {e.response.text[:500]}")
        return False


# ---- Lead-Erstellung ----

def create_lead_from_result(result: dict, branche: str, plz: str) -> dict:
    """Erstellt ein Lead-Objekt aus einem Brave-Suchergebnis."""
    url = result.get("url", "")
    title = result.get("title", "")
    snippet = result.get("description", "")
    
    # Firmenname aus Title extrahieren (oft: "Firmenname - Beschreibung")
    firma = title.split(" - ")[0].split(" | ")[0].split(" – ")[0].strip()
    if len(firma) > 100:
        firma = firma[:100]
    
    ort = PLZ_ORT_MAP.get(plz, "")
    
    # Google-Bewertung aus Snippet
    google_rating = ""
    rating_match = re.search(r'(\d[,.]?\d?)\s*/\s*5|(\d[,.]?\d?)\s*Sterne', snippet)
    if rating_match:
        google_rating = rating_match.group(1) or rating_match.group(2)
        google_rating = f"{google_rating}/5"
    
    now = datetime.now().isoformat()
    
    lead = {
        "firma": firma,
        "website": url,
        "branche": branche,
        "groesse": "",
        "plz": plz,
        "ort": ort,
        "ansprechpartner": "",
        "position": "",
        "email": "",
        "telefon": "",
        "websiteQualitaet": 1,
        "socialMedia": False,
        "socialMediaLinks": "",
        "googleBewertung": google_rating,
        "score": 0,
        "kiZusammenfassung": "",
        "segment": "COLD",
        "segmentManuell": False,
        "tags": [branche],
        "status": "Neu",
        "notizen": f"Automatisch erfasst via Scraper. Snippet: {snippet[:200]}",
        "history": [{
            "timestamp": now,
            "aktion": "Erstellt",
            "details": f"Via Scraper (Brave Search, PLZ {plz})"
        }],
        "erstelltAm": now,
        "bearbeitetAm": now,
    }
    
    return lead


def enrich_lead(lead: dict) -> dict:
    """Reichert einen Lead mit Daten von der Website an."""
    url = lead["website"]
    if not url:
        return lead
    
    log.info(f"  Analysiere: {url}")
    html = fetch_page(url)
    if not html:
        return lead
    
    # Website-Qualität
    lead["websiteQualitaet"] = assess_website_quality(url, html)
    
    # Social Media
    social = extract_social_media(html)
    if social:
        lead["socialMedia"] = True
        lead["socialMediaLinks"] = json.dumps(social)
    
    # Impressum suchen und analysieren
    impressum_url = find_impressum_url(url, html)
    text_to_analyze = html
    
    if impressum_url and impressum_url != url:
        time.sleep(0.5)  # Kurze Pause
        impressum_html = fetch_page(impressum_url)
        if impressum_html:
            text_to_analyze = impressum_html
    
    # Kontaktdaten extrahieren
    emails = extract_emails(text_to_analyze)
    if emails:
        lead["email"] = emails[0]
    
    phones = extract_phones(text_to_analyze)
    if phones:
        lead["telefon"] = phones[0]
    
    names = extract_names(text_to_analyze)
    if names:
        lead["ansprechpartner"] = names[0]["name"]
        lead["position"] = names[0].get("position", "")
    
    # Score berechnen
    lead["score"] = calculate_score(lead)
    lead["segment"] = determine_segment(lead["score"])
    
    return lead


# ---- Hauptlogik ----

def run_scraper(plz_list: List[str], branchen: List[str], dry_run: bool = False, output_file: Optional[str] = None, reset_state: bool = False):
    """Hauptfunktion: Sucht und sammelt Leads."""
    api_key = load_brave_key()
    
    # State laden
    state = load_state()
    if reset_state:
        state = {"completed": {}, "scraped_urls": [], "stats": {"total_leads": 0, "total_searches": 0, "last_run": None}}
        log.info("State zurückgesetzt")
    
    total_combinations = len(plz_list) * len(branchen)
    
    # Bereits erledigte zählen
    skipped = sum(1 for plz in plz_list for branche in branchen if is_completed(state, plz, branche))
    remaining = total_combinations - skipped
    
    log.info(f"Start: {len(plz_list)} PLZ × {len(branchen)} Branchen = {total_combinations} Kombinationen")
    if skipped > 0:
        log.info(f"  Überspringe {skipped} bereits abgearbeitete (State-File)")
        log.info(f"  Noch {remaining} offen")
    
    if remaining == 0:
        log.info("Alles schon abgearbeitet! (--reset-state zum Zurücksetzen)")
        return []
    
    all_leads: List[dict] = []
    seen: set = set()  # Duplikat-Check: (firma_lower, plz)
    # Bereits gescrapte URLs aus State übernehmen
    seen_urls: set = set(state.get("scraped_urls", []))
    last_request_time = 0.0
    search_count = 0
    
    try:
        for plz in plz_list:
            for branche in branchen:
                # Skip wenn schon abgearbeitet
                if is_completed(state, plz, branche):
                    continue
                
                query = f"{branche} {plz} {PLZ_ORT_MAP.get(plz, '')}"
                log.info(f"Suche [{search_count+1}/{remaining}]: {query}")
                
                # Rate Limiting
                elapsed = time.time() - last_request_time
                if elapsed < RATE_LIMIT_SECONDS:
                    time.sleep(RATE_LIMIT_SECONDS - elapsed)
                
                results = brave_search(query, api_key, count=10)
                last_request_time = time.time()
                search_count += 1
                
                if not results:
                    log.warning(f"  Keine Ergebnisse für: {query}")
                    mark_completed(state, plz, branche)
                    continue
                
                log.info(f"  {len(results)} Ergebnisse gefunden")
                
                for result in results:
                    url = result.get("url", "")
                    title = result.get("title", "")
                    
                    # URL schon gescraped?
                    if url in seen_urls:
                        continue
                    
                    # Offensichtliche Nicht-Firmen filtern
                    skip_domains = ["wikipedia", "gelbeseiten", "yelp", "facebook", "instagram",
                                   "linkedin", "xing", "kununu", "indeed", "stepstone",
                                   "google.com/maps", "tripadvisor", "jameda", "doctolib",
                                   "planity.com", "treatwell.de", "11880.com"]
                    if any(d in url.lower() for d in skip_domains):
                        continue
                    
                    # Lead erstellen
                    lead = create_lead_from_result(result, branche, plz)
                    
                    # Duplikat-Check
                    dup_key = (lead["firma"].lower()[:50], plz)
                    if dup_key in seen:
                        continue
                    seen.add(dup_key)
                    
                    # Website analysieren (mit Rate Limiting)
                    elapsed = time.time() - last_request_time
                    if elapsed < 0.5:
                        time.sleep(0.5 - elapsed)
                    
                    lead = enrich_lead(lead)
                    last_request_time = time.time()
                    
                    all_leads.append(lead)
                    seen_urls.add(url)
                    add_scraped_url(state, url)
                    log.info(f"  ✓ {lead['firma']} — Score: {lead['score']}, Segment: {lead['segment']}")
                
                # Diese Kombi als erledigt markieren
                mark_completed(state, plz, branche)
                state["stats"]["total_searches"] += 1
                
                # State nach jeder Kombi speichern (Resume-Fähigkeit)
                if not dry_run:
                    save_state(state)
    
    except KeyboardInterrupt:
        log.info("\n⚠️  Abgebrochen! State gespeichert — nächster Run macht hier weiter.")
        save_state(state)
        raise
    
    # Zusammenfassung
    log.info(f"\n{'='*50}")
    log.info(f"Ergebnis: {len(all_leads)} Leads gesammelt")
    segments = {}
    for lead in all_leads:
        segments[lead["segment"]] = segments.get(lead["segment"], 0) + 1
    for seg, count in sorted(segments.items()):
        log.info(f"  {seg}: {count}")
    
    # JSON speichern
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_leads, f, ensure_ascii=False, indent=2)
        log.info(f"JSON gespeichert: {output_file}")
    
    # In Convex schreiben
    if not dry_run and all_leads:
        log.info("Schreibe in Convex-Datenbank...")
        success = push_to_convex(all_leads)
        if success:
            log.info("✓ Alle Leads in Convex geschrieben")
            state["stats"]["total_leads"] += len(all_leads)
        else:
            log.error("✗ Fehler beim Schreiben in Convex")
            fallback = f"scraper_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(fallback, "w", encoding="utf-8") as f:
                json.dump(all_leads, f, ensure_ascii=False, indent=2)
            log.info(f"Fallback gespeichert: {fallback}")
    elif dry_run:
        log.info("(Dry-Run — nicht in DB geschrieben)")
    
    # State final speichern
    save_state(state)
    
    # State-Übersicht
    completed_count = sum(len(v) for v in state["completed"].values())
    log.info(f"\n📊 State: {completed_count} PLZ×Branche-Kombos abgearbeitet, {state['stats']['total_leads']} Leads gesamt")
    log.info(f"   State-File: {STATE_FILE}")
    
    return all_leads


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(
        description="ManniLeads Scraper — Lokale Unternehmen finden und analysieren"
    )
    parser.add_argument("--plz", type=str, default=None,
                       help="Komma-getrennte PLZ-Liste (Default: Schwerin)")
    parser.add_argument("--branchen", type=str, default=None,
                       help="Komma-getrennte Branchen-Liste")
    parser.add_argument("--dry-run", action="store_true",
                       help="Nur suchen, nicht in DB schreiben")
    parser.add_argument("--output", "-o", type=str, default=None,
                       help="Ergebnisse zusätzlich als JSON speichern")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Ausführliche Ausgabe")
    parser.add_argument("--reset-state", action="store_true",
                       help="State zurücksetzen (alles nochmal scrapen)")
    parser.add_argument("--show-state", action="store_true",
                       help="Aktuellen State anzeigen und beenden")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # State anzeigen
    if args.show_state:
        state = load_state()
        completed_count = sum(len(v) for v in state["completed"].values())
        print(f"\n📊 Scraper-State ({STATE_FILE})")
        print(f"   Abgearbeitete Kombos: {completed_count}")
        print(f"   Gescrapte URLs: {len(state.get('scraped_urls', []))}")
        print(f"   Gesamt-Leads: {state['stats']['total_leads']}")
        print(f"   Letzter Run: {state['stats']['last_run'] or 'nie'}")
        if state["completed"]:
            print(f"\n   PLZ-Fortschritt:")
            for plz, branches in sorted(state["completed"].items()):
                print(f"     {plz}: {len(branches)} Branchen ✓")
        return
    
    plz_list = args.plz.split(",") if args.plz else DEFAULT_PLZ
    branchen = [b.strip() for b in args.branchen.split(",")] if args.branchen else DEFAULT_BRANCHEN
    
    log.info("=" * 50)
    log.info("ManniLeads Scraper v1.0")
    log.info("=" * 50)
    
    leads = run_scraper(plz_list, branchen, dry_run=args.dry_run, output_file=args.output, reset_state=args.reset_state)
    
    log.info(f"\nFertig! {len(leads)} Leads verarbeitet.")


if __name__ == "__main__":
    main()
