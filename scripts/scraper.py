#!/usr/bin/env python3
"""
ManniLeads Scraper v3 — Gemini-Powered
Sucht lokale Unternehmen via Brave Search, holt Impressum + Startseite,
lässt Gemini Flash alle Felder befüllen, schreibt in Convex.

Flow pro Lead:
1. Brave Search → URLs finden
2. Hauptseite fetchen → 1000 Zeichen Text extrahieren
3. Impressum-Seite finden + fetchen → Text extrahieren
4. Beides an Gemini Flash → strukturiertes JSON mit allen Feldern
5. Email-Dedup prüfen + in Convex schreiben
"""

import argparse
import html
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

DEFAULT_STADT = "Schwerin"
DEFAULT_PLZ = ["19053", "19055", "19057", "19059", "19061", "19063"]
DEFAULT_BRANCHEN = [
    "Friseur", "Restaurant", "Autowerkstatt", "Zahnarzt", "Rechtsanwalt",
    "Steuerberater", "Immobilienmakler", "Handwerker", "Elektriker",
    "Maler", "Dachdecker", "Fitnessstudio", "Bäckerei", "Apotheke",
    "Optiker", "Physiotherapie", "Hotel", "Café", "Blumenladen", "Fahrschule"
]

# Wird dynamisch befüllt über --stadt Flag
PLZ_ORT_MAP = {
    "19053": "Schwerin", "19055": "Schwerin", "19057": "Schwerin",
    "19059": "Schwerin", "19061": "Schwerin", "19063": "Schwerin",
}

CONVEX_URL = "https://energetic-civet-402.convex.cloud"
STATE_FILE = Path(__file__).parent / "scraper_state.json"
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = "google/gemini-3-flash-preview"
RATE_LIMIT_SECONDS = 1.1  # Brave Free Tier

# ---- Skip-Domains ----

SKIP_DOMAINS = [
    "wikipedia", "gelbeseiten", "yelp", "facebook", "instagram",
    "linkedin", "xing", "kununu", "indeed", "stepstone",
    "google.com/maps", "tripadvisor", "jameda", "doctolib",
    "planity.com", "treatwell.de", "11880.com",
    "branchenbuch-schwerin.de", "dasoertliche.de", "bundes-telefonbuch.de",
    "meinestadt.de", "fmfm.de", "goyellow.de", "golocal.de", "kaufda.de",
    "handwerker-anzeiger.de", "11880-immobilienmakler.com", "dastelefonbuch.de",
    "weshoplocal.de", "misterwhat.de", "plzplz.de",
    "arzt-auskunft.de", "qimeda.de", "docinsider.de", "fachanwalt.de",
    "rechtecheck.de", "rechtsanwalt-regional.de", "sehen.de", "o-pal.de",
    "brillen-sehhilfen.de", "apotheken.de", "ihreapotheken.de",
    "meineapotheke.de", "px.de", "lymphologicum.de", "elektriker.org",
    "maler.org", "dachdecker.com", "dachdecker.org", "auto-werkstatt.de",
    "elektriker-und-elektroniker.de", "elektrikerportal.com",
    "elektriker-24std.de", "elektro-portal.de", "wasserwaermeluft.de",
    "bessere-handwerker.de", "my-hammer.de", "my-profi-maler.de",
    "maler-schwerin.de", "repareo.de", "fahrschulenmap.de", "fahrschulen.de",
    "handelsangebote.de",
    "booking.com", "trivago.de", "hrs.de", "hotel.de",
    "hotel-hostel-unterkunft.de", "kongress.de", "fair-hotels.de",
    "cologne-in.de", "finde-unterkunft.de",
    "schwerin.de", "schweriner.de", "mecklenburg-schwerin.de",
    "wohinheuteschwerin.de",
    "immobilienscout24.de", "gymsider.com", "misterspex.de", "praktiker.de",
    "baeckerei-in-der-naehe.de", "brunch-lunch-dinner.de", "restaurantnet.de",
    "cybo.com", "wanderlog.com", "marcopolo.de", "bvbb.de",
    "volle-deckung.de", "nordkurier.de", "fleurop.de",
    "koepmarkt-schwerin.de", "schlosspark-center.de", "9gg.de", "m-vp.de",
    "11880-steuerberater.com", "wuestenrot-immobilien.de",
]

# ---- Logging ----

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("scraper")

# ---- API Keys ----

def load_brave_key() -> str:
    key = os.environ.get("BRAVE_API_KEY", "").strip()
    if key:
        return key
    p = Path(__file__).parent / ".brave_search_key"
    if p.exists():
        lines = [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
        if lines:
            return lines[0]
    log.error("Kein Brave Search API Key gefunden!")
    sys.exit(1)


def load_openrouter_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    paths = [
        Path(__file__).parent / ".openrouter_key",
        Path.home() / ".openclaw" / "workspace" / "scripts" / ".openrouter_key",
    ]
    for p in paths:
        if p.exists():
            lines = [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
            if lines:
                return lines[0]
    log.error("Kein OpenRouter API Key gefunden!")
    sys.exit(1)


# ---- Utility ----

def strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|div|h[1-6]|li|tr)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)
    return text.strip()


def get_root_domain(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url if '://' in url else f'https://{url}')
        host = parsed.netloc or parsed.path.split('/')[0]
        host = host.lower().split(':')[0]
        if host.startswith('www.'):
            host = host[4:]
        return host
    except Exception:
        return url.lower()


def is_skip_domain(url: str) -> bool:
    url_lower = url.lower()
    for d in SKIP_DOMAINS:
        if d in url_lower:
            return True
    return False


def extract_text(html_content: str, max_chars: int = 2000) -> str:
    """Extract readable text from HTML."""
    if not html_content:
        return ""
    text = re.sub(r'<(?:script|style|nav|noscript)[^>]*>.*?</(?:script|style|nav|noscript)>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|div|h[1-6]|li|tr|section|article)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 10]
    text = '\n'.join(lines)
    return text[:max_chars].strip()


# ---- State Tracking ----

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            log.warning("State-Datei beschädigt, starte frisch")
    return {"completed": {}, "scraped_urls": [], "known_emails": [], "stats": {"total_leads": 0, "total_searches": 0, "last_run": None}}


def save_state(state: dict):
    state["stats"]["last_run"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def mark_completed(state: dict, plz: str, branche: str):
    if plz not in state["completed"]:
        state["completed"][plz] = []
    if branche not in state["completed"][plz]:
        state["completed"][plz].append(branche)


def is_completed(state: dict, plz: str, branche: str) -> bool:
    return branche in state["completed"].get(plz, [])


# ---- Brave Search ----

def brave_search(query: str, api_key: str, count: int = 10) -> List[dict]:
    headers = {"X-Subscription-Token": api_key, "Accept": "application/json"}
    params = {"q": query, "count": count, "country": "de", "search_lang": "de"}
    try:
        resp = requests.get(BRAVE_ENDPOINT, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("web", {}).get("results", [])
    except requests.RequestException as e:
        log.warning(f"Brave Search Fehler: {e}")
        return []


# ---- Website Fetching ----

def fetch_page(url: str, timeout: int = 10) -> Optional[str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ManniLeads/3.0)"}
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def find_impressum_url(base_url: str, page_html: str) -> Optional[str]:
    patterns = [
        r'href=["\']([^"\']*impressum[^"\']*)["\']',
        r'href=["\']([^"\']*imprint[^"\']*)["\']',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, page_html, re.IGNORECASE)
        for match in matches:
            resolved = resolve_url(base_url, match)
            if resolved:
                return resolved
    return None


def resolve_url(base_url: str, href: str) -> Optional[str]:
    if not href or href.startswith('#') or href.startswith('javascript:'):
        return None
    if href.startswith('http'):
        return href
    if href.startswith('/'):
        parsed = urllib.parse.urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{href}"
    base = base_url.rsplit('/', 1)[0]
    return f"{base}/{href}"


def collect_website_data(url: str) -> Optional[Dict[str, str]]:
    """
    Fetch main page + impressum page, return raw text data.
    Returns None if site unreachable.
    """
    log.info(f"  Fetche: {url}")
    main_html = fetch_page(url)
    if not main_html:
        log.info(f"  → Nicht erreichbar")
        return None

    # Extract main page text (max 4000 chars — genug für Leistungen/Beschreibung)
    main_text = extract_text(main_html, max_chars=4000)

    # Find and fetch impressum
    impressum_text = ""
    impressum_url = find_impressum_url(url, main_html)
    if impressum_url:
        time.sleep(0.3)
        imp_html = fetch_page(impressum_url)
        if imp_html:
            impressum_text = extract_text(imp_html, max_chars=3000)

    # If no separate impressum page, check if main page has impressum content
    if not impressum_text:
        if re.search(r'(?:Angaben\s+gemäß|Impressum|Verantwortlich\s+(?:i\.\s*S\.|gemäß))', main_html, re.IGNORECASE):
            impressum_text = extract_text(main_html, max_chars=3000)

    if not impressum_text:
        log.info(f"  → Kein Impressum gefunden")
        return None

    # Extract social media links (raw, for Gemini to parse)
    social_links = []
    for platform in ['facebook.com', 'instagram.com', 'linkedin.com', 'tiktok.com', 'youtube.com']:
        matches = re.findall(rf'href=["\']([^"\']*{re.escape(platform)}[^"\']*)["\']', main_html, re.IGNORECASE)
        for m in matches:
            if '/sharer/' not in m and '/share?' not in m and 'share.php' not in m:
                social_links.append(m)
                break

    return {
        "url": url,
        "main_text": main_text,
        "impressum_text": impressum_text,
        "social_links": social_links,
        "has_https": url.startswith("https"),
        "has_viewport": 'viewport' in main_html.lower(),
    }


# ---- Gemini Analysis ----

GEMINI_PROMPT = """Du bist ein Datenextraktions-Experte. Analysiere die folgenden Website-Daten eines lokalen Unternehmens und extrahiere strukturierte Informationen.

WEBSITE: {url}
BRANCHE (gesucht): {branche}
PLZ: {plz}
ORT: {ort}

=== STARTSEITE (Auszug) ===
{main_text}

=== IMPRESSUM ===
{impressum_text}

=== SOCIAL MEDIA LINKS ===
{social_links}

---

Extrahiere folgende Felder als JSON. Wenn ein Feld nicht ermittelbar ist, setze einen leeren String "".
WICHTIG: 
- "firma" = der ECHTE Firmenname aus dem Impressum (NICHT "Impressum", "Datenschutz", "§5 TMG" oder ähnliche Überschriften!)
- "email" = geschäftliche Kontakt-Email im Format name@domain.de (NICHT "Email Protected", "[email protected]", info@portal.de oder support@plattform.de — wenn keine echte Email erkennbar, leerer String!)
- "telefon" = Telefonnummer mit Vorwahl
- "ansprechpartner" = Name des Inhabers/Geschäftsführers
- "position" = Rolle (z.B. "Geschäftsführer", "Inhaber", "Zahnarzt")
- "kiZusammenfassung" = 1-2 Sätze was die Firma macht
- "kiZielgruppe" = Wer sind deren Kunden?
- "kiOnlineAuftritt" = Kurzbewertung der Website (1-2 Sätze: modern/veraltet, mobil-optimiert, Inhalte)
- "kiSchwaechen" = Schwächen im Online-Auftritt (wo könnten wir als Social-Media-Agentur helfen?)
- "kiChancen" = Konkrete Chancen für eine Social-Media-Agentur (Video, Reels, Ads, etc.)
- "kiAnsprache" = NUR ein kurzes persönliches Intro (3-4 Sätze) für AgentZ Media. Beginnt mit Anrede ("Hallo Herr/Frau [Name],\n\n" oder "Sehr geehrte Damen und Herren,\n\n"). Dann kurz erklären wer AgentZ ist (siehe INFO unten) und persönlichen Bezug herstellen: warum täglicher Video-Content für genau diese Firma relevant wäre. KEIN Abschluss, KEINE Grußformel, KEIN "Beste Grüße". Wird als Variable in eine Email-Vorlage eingesetzt.

INFO zu AgentZ Media:
AgentZ Media ist eine Content-Agentur aus Schwerin. Unser Motto: "Reichweite durch Content, nicht durch Werbung!" Wir produzieren für Unternehmen täglich Kurzvideos (TikTok, Instagram Reels, YouTube Shorts). 365 Videos pro Jahr, komplett Done-for-you: von der Idee über den Dreh bis zum Upload. Der Kunde muss sich um nichts kümmern. Keine Bilder, keine Stockfotos, sondern echte, authentische Kurzvideos. Organische Reichweite statt bezahlte Werbung. Monatliche Pauschale, transparent und fair.
- "kiAnspracheSig" = NUR ein kurzes persönliches Intro (3-4 Sätze) für Banner-Werbung auf schwerinistgeil.de. Anrede + Absatz, dann kurz erklären was SIG ist (satirische Nachrichtenseite rund um Schwerin, humorvolle Artikel über lokale Themen, die gezielt Schweriner ansprechen). Dann persönlicher Bezug: warum Bannerwerbung auf SIG für diese Firma sinnvoll wäre. KEIN Abschluss, KEINE Grußformel. Wird als Variable in eine Email-Vorlage eingesetzt.

STILREGELN für kiAnsprache und kiAnspracheSig:
- Zwischen Anrede und Text IMMER einen Absatz (echtes Newline \n\n), z.B.: "Hallo Herr Müller,\n\nwir sind AgentZ Media..."
- KEINE langen Bindestriche (— oder –), stattdessen Kommas oder Punkte verwenden
- KEINE Emojis, niemals
- Natürlicher deutscher Schreibstil, soll sich NICHT wie KI lesen
- Locker-professionell, nicht steif oder übertrieben förmlich
- Kurze Sätze bevorzugen
- KEIN "Bilder posten", KEIN "Instagram und Facebook" als Hauptfokus. TikTok und Kurzvideos sind der Kern!
- "tags" = Array mit 2-5 passenden Tags zur Kategorisierung. Beispiele: "Einzelunternehmer", "Filiale/Kette", "Premium", "Budget", "Social-Media-aktiv", "Social-Media-schwach", "Website-modern", "Website-veraltet", "Gastronomie", "Gesundheit", "Handwerk", "Dienstleistung", "Einzelhandel", "B2B", "B2C". Wähle die passendsten.
- "istEchteFirma" = true wenn es ein echtes lokales Unternehmen ist, false wenn es ein Portal/Verzeichnis/überregionale Kette ist
- "kiScore" = Bewertung 0-100 wie gut dieser Lead für eine Social-Media-Agentur ist. SEI DIFFERENZIERT, nicht immer 85! Orientierung:
  90-100: Perfekter Lead (lokales Unternehmen, B2C, keine Social-Media-Präsenz, hoher Bedarf an Sichtbarkeit)
  70-89: Guter Lead (lokales Unternehmen mit Potenzial, etwas Social Media aber ausbaufähig)
  50-69: Mittelmäßig (hat schon Social Media oder wenig Bedarf, z.B. Arztpraxen die nicht werben müssen)
  30-49: Schwach (Filialen/Ketten die zentral gesteuert werden, sehr kleine Betriebe)
  0-29: Ungeeignet (kein sinnvoller Ansatzpunkt für Social-Media-Agentur)
- "kiScoreBegruendung" = 1-2 Sätze warum dieser Score vergeben wurde. Was spricht für/gegen diesen Lead?

INFO zu schwerinistgeil.de (SIG):
Schwerin ist Geil ist eine neue satirische Nachrichtenwebsite über Schwerin — wie "Der Postillon" aber lokal für Schwerin. Tägliche Satire-Artikel über lokale Themen, Stadtpolitik, Alltagsabsurditäten. Zielgruppe: Schweriner zwischen 20-50 Jahren.
Wir verkaufen BANNER-WERBEPLÄTZE (KEINE Sponsored Posts oder Advertorials!). Ähnlich wie bei Google Ads: Banner oberhalb/innerhalb der Seite, die sich natürlich in den Content einfügen. Vorteil: gezielt lokale Schweriner erreichen.
WICHTIG für den Pitch: KEINE konkreten Reichweiten-Zahlen nennen (keine "tausende Leser" o.ä.)! Die Seite ist neu. Stattdessen den Vorteil der lokalen Zielgruppe und die Passgenauigkeit für das jeweilige Unternehmen betonen.

Antworte NUR mit validem JSON, keine Erklärungen:
{{
  "firma": "",
  "email": "",
  "telefon": "",
  "ansprechpartner": "",
  "position": "",
  "kiZusammenfassung": "",
  "kiZielgruppe": "",
  "kiOnlineAuftritt": "",
  "kiSchwaechen": "",
  "kiChancen": "",
  "kiAnsprache": "",
  "kiAnspracheSig": "",
  "tags": ["Beispiel-Tag1", "Beispiel-Tag2"],
  "istEchteFirma": true,
  "kiScore": 50,
  "kiScoreBegruendung": ""
}}"""


def analyze_with_gemini(website_data: dict, branche: str, plz: str, ort: str, api_key: str) -> Optional[dict]:
    """Send website data to Gemini Flash and get structured lead data back."""
    prompt = GEMINI_PROMPT.format(
        url=website_data["url"],
        branche=branche,
        plz=plz,
        ort=ort,
        main_text=website_data["main_text"][:4000],
        impressum_text=website_data["impressum_text"][:3000],
        social_links="\n".join(website_data.get("social_links", [])) or "(keine gefunden)",
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GEMINI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    try:
        resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Parse JSON from response (handle markdown code blocks)
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

        data = json.loads(content)
        return data

    except (requests.RequestException, json.JSONDecodeError, KeyError, IndexError) as e:
        log.warning(f"  Gemini-Fehler: {e}")
        return None


# ---- Lead Building ----

def build_lead(gemini_data: dict, website_data: dict, branche: str, plz: str, ort: str, snippet: str) -> dict:
    """Build a Convex-ready lead from Gemini output + website metadata."""
    now = datetime.now().isoformat()

    # Score: use Gemini's score, adjust for data completeness
    ki_score = gemini_data.get("kiScore", 50)
    if isinstance(ki_score, str):
        try:
            ki_score = int(ki_score)
        except ValueError:
            ki_score = 50
    ki_score = max(0, min(100, ki_score))

    # Segment from score
    if ki_score >= 70:
        segment = "HOT"
    elif ki_score >= 50:
        segment = "WARM"
    elif ki_score >= 30:
        segment = "COLD"
    else:
        segment = "DISQUALIFIED"

    social_links = website_data.get("social_links", [])

    # Website quality
    quality = 1
    if website_data.get("has_https"):
        quality += 1
    if website_data.get("has_viewport"):
        quality += 1
    if social_links:
        quality += 1
    if gemini_data.get("email"):
        quality += 1
    quality = min(quality, 5)

    return {
        "firma": (gemini_data.get("firma") or "").strip()[:100],
        "website": website_data["url"],
        "branche": branche,
        "groesse": "",
        "plz": plz,
        "ort": ort,
        "ansprechpartner": (gemini_data.get("ansprechpartner") or "").strip(),
        "position": (gemini_data.get("position") or "").strip(),
        "email": (gemini_data.get("email") or "").strip().lower(),
        "telefon": (gemini_data.get("telefon") or "").strip(),
        "websiteQualitaet": quality,
        "socialMedia": bool(social_links),
        "socialMediaLinks": json.dumps(dict(zip(
            [s.split('.com')[0].split('/')[-1] for s in social_links],
            social_links
        ))) if social_links else "",
        "googleBewertung": "",
        "websiteText": website_data.get("main_text", "")[:500],
        "score": ki_score,
        "kiZusammenfassung": (gemini_data.get("kiZusammenfassung") or "").strip(),
        "segment": segment,
        "segmentManuell": False,
        "tags": gemini_data.get("tags", [branche]) if isinstance(gemini_data.get("tags"), list) else [branche],
        "status": "Neu",
        "kiAnalysiert": True,
        "kiAnalysiertAm": now,
        "kiZielgruppe": (gemini_data.get("kiZielgruppe") or "").strip(),
        "kiOnlineAuftritt": (gemini_data.get("kiOnlineAuftritt") or "").strip(),
        "kiSchwaechen": (gemini_data.get("kiSchwaechen") or "").strip(),
        "kiChancen": (gemini_data.get("kiChancen") or "").strip(),
        "kiWettbewerb": "",
        "kiAnsprache": (gemini_data.get("kiAnsprache") or "").strip(),
        "kiAnspracheSig": (gemini_data.get("kiAnspracheSig") or "").strip(),
        "kiScore": ki_score,
        "kiScoreBegruendung": (gemini_data.get("kiScoreBegruendung") or "").strip(),
        "kiSegment": segment,
        "notizen": f"Scraper v3 (Gemini). Snippet: {strip_html(snippet)[:200]}",
        "history": [{"timestamp": now, "aktion": "Erstellt", "details": f"Scraper v3 + Gemini Flash (PLZ {plz})"}],
        "erstelltAm": now,
        "bearbeitetAm": now,
    }


# ---- Convex API ----

def push_to_convex(leads: List[dict]) -> bool:
    if not leads:
        return True
    url = f"{CONVEX_URL}/api/mutation"
    headers = {"Content-Type": "application/json"}
    try:
        payload = {"path": "leads:bulkCreate", "args": {"leads": leads}}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") == "success":
            ids = result.get("value", [])
            log.info(f"  → {len(ids)} Leads in Convex geschrieben (Dedup: {len(leads) - len(ids)} übersprungen)")
            return True
        else:
            log.warning(f"  Convex-Antwort: {result}")
            return False
    except requests.RequestException as e:
        log.error(f"Convex API Fehler: {e}")
        return False


# ---- Hauptlogik ----

def run_scraper(plz_list: List[str], branchen: List[str], dry_run: bool = False,
                output_file: Optional[str] = None, reset_state: bool = False):
    brave_key = load_brave_key()
    openrouter_key = load_openrouter_key()
    state = load_state()

    if reset_state:
        state = {"completed": {}, "scraped_urls": [], "known_emails": [], "stats": {"total_leads": 0, "total_searches": 0, "last_run": None}}
        log.info("State zurückgesetzt")

    total_combos = len(plz_list) * len(branchen)
    skipped = sum(1 for plz in plz_list for branche in branchen if is_completed(state, plz, branche))
    remaining = total_combos - skipped

    log.info(f"Start: {len(plz_list)} PLZ × {len(branchen)} Branchen = {total_combos} Kombinationen")
    if skipped > 0:
        log.info(f"  Überspringe {skipped} bereits abgearbeitete")
    if remaining == 0:
        log.info("Alles schon abgearbeitet! (--reset-state zum Zurücksetzen)")
        return

    seen_domains = set()
    seen_urls = set(state.get("scraped_urls", []))
    known_emails = set(state.get("known_emails", []))
    all_leads = []
    last_brave_time = 0.0
    search_count = 0
    stats = {"portal_skip": 0, "no_impressum": 0, "duplicate_domain": 0, "duplicate_email": 0, "not_real_firm": 0, "gemini_fail": 0}

    try:
        for plz in plz_list:
            for branche in branchen:
                if is_completed(state, plz, branche):
                    continue

                ort = PLZ_ORT_MAP.get(plz, "")
                query = f"{branche} {plz} {ort}"
                log.info(f"\nSuche [{search_count+1}/{remaining}]: {query}")

                # Brave rate limit
                elapsed = time.time() - last_brave_time
                if elapsed < RATE_LIMIT_SECONDS:
                    time.sleep(RATE_LIMIT_SECONDS - elapsed)

                results = brave_search(query, brave_key, count=10)
                last_brave_time = time.time()
                search_count += 1

                if not results:
                    log.warning(f"  Keine Ergebnisse")
                    mark_completed(state, plz, branche)
                    continue

                log.info(f"  {len(results)} Ergebnisse")
                combo_leads = []

                for result in results:
                    url = result.get("url", "")
                    snippet = result.get("description", "")

                    if url in seen_urls:
                        continue

                    if is_skip_domain(url):
                        stats["portal_skip"] += 1
                        continue

                    root = get_root_domain(url)
                    if root in seen_domains:
                        stats["duplicate_domain"] += 1
                        continue

                    # Step 1: Fetch website data
                    time.sleep(0.4)
                    website_data = collect_website_data(url)
                    if website_data is None:
                        stats["no_impressum"] += 1
                        seen_urls.add(url)
                        continue

                    # Step 2: Gemini analysis
                    time.sleep(0.3)
                    gemini_data = analyze_with_gemini(website_data, branche, plz, ort, openrouter_key)
                    if gemini_data is None:
                        stats["gemini_fail"] += 1
                        seen_urls.add(url)
                        continue

                    # Check if Gemini says it's a real firm
                    if not gemini_data.get("istEchteFirma", True):
                        log.info(f"  ✗ Kein echtes Unternehmen laut Gemini: {url}")
                        stats["not_real_firm"] += 1
                        seen_urls.add(url)
                        seen_domains.add(root)
                        continue

                    # Validate email format
                    raw_email = (gemini_data.get("email") or "").strip()
                    if raw_email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', raw_email):
                        log.info(f"  ⚠ Ungültige Email verworfen: '{raw_email}'")
                        gemini_data["email"] = ""

                    # Check firma name
                    firma = (gemini_data.get("firma") or "").strip()
                    if not firma or len(firma) < 3:
                        log.info(f"  ✗ Kein Firmenname extrahiert: {url}")
                        seen_urls.add(url)
                        continue

                    # Email dedup
                    email = (gemini_data.get("email") or "").strip().lower()
                    if email and email in known_emails:
                        log.info(f"  ✗ Email-Duplikat ({email}): {firma}")
                        stats["duplicate_email"] += 1
                        seen_urls.add(url)
                        seen_domains.add(root)
                        continue

                    # Build lead
                    lead = build_lead(gemini_data, website_data, branche, plz, ort, snippet)
                    combo_leads.append(lead)
                    seen_domains.add(root)
                    seen_urls.add(url)
                    if email:
                        known_emails.add(email)
                        state.setdefault("known_emails", []).append(email)
                    state.setdefault("scraped_urls", []).append(url)

                    seg_icon = {"HOT": "🔥", "WARM": "🟡", "COLD": "🔵", "DISQUALIFIED": "⚫"}.get(lead["segment"], "")
                    log.info(f"  ✓ {seg_icon} {firma} — Score: {lead['score']}, Email: {'✓' if email else '✗'}, Tel: {'✓' if lead['telefon'] else '✗'}, Kontakt: {lead['ansprechpartner'] or '✗'}")

                # Push combo to Convex
                if combo_leads and not dry_run:
                    push_to_convex(combo_leads)
                    state["stats"]["total_leads"] += len(combo_leads)

                all_leads.extend(combo_leads)
                mark_completed(state, plz, branche)
                state["stats"]["total_searches"] += 1
                save_state(state)

    except KeyboardInterrupt:
        log.info("\n⚠️  Abgebrochen! State gespeichert.")
        save_state(state)

    # Summary
    log.info(f"\n{'='*60}")
    log.info(f"ERGEBNIS: {len(all_leads)} Leads gesammelt")
    log.info(f"  Portale übersprungen: {stats['portal_skip']}")
    log.info(f"  Kein Impressum: {stats['no_impressum']}")
    log.info(f"  Duplikat (Domain): {stats['duplicate_domain']}")
    log.info(f"  Duplikat (Email): {stats['duplicate_email']}")
    log.info(f"  Kein echtes Unternehmen: {stats['not_real_firm']}")
    log.info(f"  Gemini-Fehler: {stats['gemini_fail']}")
    log.info(f"---")
    with_email = sum(1 for l in all_leads if l.get("email"))
    with_phone = sum(1 for l in all_leads if l.get("telefon"))
    with_contact = sum(1 for l in all_leads if l.get("ansprechpartner"))
    log.info(f"  Mit Email: {with_email}/{len(all_leads)}")
    log.info(f"  Mit Telefon: {with_phone}/{len(all_leads)}")
    log.info(f"  Mit Ansprechpartner: {with_contact}/{len(all_leads)}")

    segments = {}
    for lead in all_leads:
        segments[lead["segment"]] = segments.get(lead["segment"], 0) + 1
    for seg in ["HOT", "WARM", "COLD", "DISQUALIFIED"]:
        if seg in segments:
            log.info(f"  {seg}: {segments[seg]}")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_leads, f, ensure_ascii=False, indent=2)
        log.info(f"\nJSON gespeichert: {output_file}")

    save_state(state)
    log.info(f"Fertig! {len(all_leads)} Leads verarbeitet.")


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(description="ManniLeads Scraper v3 — Gemini-Powered")
    parser.add_argument("--stadt", type=str, default=None, help="Stadtname (z.B. 'Rostock'). Setzt automatisch PLZ_ORT_MAP.")
    parser.add_argument("--plz", type=str, default=None, help="Kommagetrennte PLZ-Liste")
    parser.add_argument("--branchen", type=str, default=None, help="Kommagetrennte Branchen")
    parser.add_argument("--dry-run", action="store_true", help="Nicht in Convex schreiben")
    parser.add_argument("--output", "-o", type=str, default=None, help="JSON-Ausgabedatei")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--reset-state", action="store_true", help="State zurücksetzen")
    parser.add_argument("--show-state", action="store_true", help="State anzeigen")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.show_state:
        state = load_state()
        completed_count = sum(len(v) for v in state["completed"].values())
        print(f"\n📊 Scraper-State ({STATE_FILE})")
        print(f"   Abgearbeitete Kombos: {completed_count}")
        print(f"   Gescrapte URLs: {len(state.get('scraped_urls', []))}")
        print(f"   Bekannte Emails: {len(state.get('known_emails', []))}")
        print(f"   Gesamt-Leads: {state['stats']['total_leads']}")
        print(f"   Letzter Run: {state['stats']['last_run'] or 'nie'}")
        return

    plz_list = args.plz.split(",") if args.plz else DEFAULT_PLZ
    branchen = [b.strip() for b in args.branchen.split(",")] if args.branchen else DEFAULT_BRANCHEN

    # Dynamische Stadt: PLZ_ORT_MAP updaten
    if args.stadt:
        global PLZ_ORT_MAP
        for plz in plz_list:
            PLZ_ORT_MAP[plz] = args.stadt
        log.info(f"Stadt: {args.stadt} (PLZ: {', '.join(plz_list)})")

    log.info("=" * 60)
    log.info("ManniLeads Scraper v3.0 — Gemini-Powered")
    log.info("=" * 60)

    run_scraper(plz_list, branchen, dry_run=args.dry_run,
                output_file=args.output, reset_state=args.reset_state)


if __name__ == "__main__":
    main()
