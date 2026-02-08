#!/usr/bin/env python3
"""
ManniLeads Scraper v2 — Impressum-First-Ansatz
Sucht lokale Unternehmen via Brave Search, extrahiert Kontaktdaten aus dem
Impressum der Firmenwebsite und schreibt Ergebnisse in die Convex-Datenbank.

v2-Änderungen:
- 67+ Skip-Domains (Portale/Verzeichnisse)
- Impressum-First: Kein Impressum = kein Lead
- Firmenname aus Impressum (nicht Brave-Titel)
- HTML-Stripping & Entity-Decoding
- Social-Media Share-Button-Filter
- Duplikat-Erkennung per Root-Domain
- Telefon/Email-Validierung mit Blacklists
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
from typing import Optional, List, Dict, Tuple

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

PLZ_ORT_MAP = {
    "19053": "Schwerin", "19055": "Schwerin", "19057": "Schwerin",
    "19059": "Schwerin", "19061": "Schwerin", "19063": "Schwerin",
}

CONVEX_URL = "https://energetic-civet-402.convex.cloud"
CONVEX_API_KEY = "ml_scraper_2026_xR9kT4mQ"

STATE_FILE = Path(__file__).parent / "scraper_state.json"
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
RATE_LIMIT_SECONDS = 1.1

# ---- Skip-Domains (67 aus Audit + Original-Liste) ----

SKIP_DOMAINS = [
    # Original-Liste
    "wikipedia", "gelbeseiten", "yelp", "facebook", "instagram",
    "linkedin", "xing", "kununu", "indeed", "stepstone",
    "google.com/maps", "tripadvisor", "jameda", "doctolib",
    "planity.com", "treatwell.de", "11880.com",
    # Audit: Verzeichnisse & Branchenbücher
    "branchenbuch-schwerin.de", "dasoertliche.de", "bundes-telefonbuch.de",
    "meinestadt.de", "fmfm.de", "goyellow.de", "golocal.de", "kaufda.de",
    "handwerker-anzeiger.de", "11880-immobilienmakler.com", "dastelefonbuch.de",
    "weshoplocal.de", "misterwhat.de", "plzplz.de",
    # Audit: Bewertungs- & Vergleichsportale
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
    # Audit: Buchungs-/Reiseportale
    "booking.com", "trivago.de", "hrs.de", "hotel.de",
    "hotel-hostel-unterkunft.de", "kongress.de", "fair-hotels.de",
    "cologne-in.de", "finde-unterkunft.de",
    # Audit: Stadtportale
    "schwerin.de", "schweriner.de", "mecklenburg-schwerin.de",
    "wohinheuteschwerin.de",
    # Audit: Überregionale Portale
    "immobilienscout24.de", "gymsider.com", "misterspex.de", "praktiker.de",
    "baeckerei-in-der-naehe.de", "brunch-lunch-dinner.de", "restaurantnet.de",
    "cybo.com", "wanderlog.com", "marcopolo.de", "bvbb.de",
    "volle-deckung.de", "nordkurier.de", "fleurop.de",
    "koepmarkt-schwerin.de", "schlosspark-center.de", "9gg.de", "m-vp.de",
]

# ---- Blacklists ----

BLACKLIST_EMAILS = [
    "support@apotheken.de", "support@kaufda.de", "info@eduxx.de",
    "a.kirchner@ceramex-media.de", "info@elektriker.org", "info@maler.org",
    "info@dachdecker.com", "info@auto-werkstatt.de", "info@trivago.com",
    "info@fachanwalt.de", "service@rechtecheck.de", "kontakt@123media.site",
    "adressredaktion@stiftung-gesundheit.de", "mp.datenschutz@ece.com",
    "gutentag@buero-vip.de", "info@handwerker-anzeiger.de",
    "werkstattmeister@repareo.de", "kundenberatung@fahrschulenmap.de",
    "info@fahrschule.de", "support@schedulista.com",
    "lizenzen@schluetersche.de", "info@sehen.de", "contact@shopfully.com",
    "support@zones.sk", "info@koelnerbranchen.de", "info@auctores.de",
    "service@gmbh-seibel.de", "info@ds-destinationsolutions.comst.com",
    "bewerbung@firststop.de",
]

BLACKLIST_EMAIL_DOMAINS = [
    "example.com", "example.org", "example.net",
    "sentry.io", "wixpress.com", "webpack.js",
]

BLACKLIST_PHONES = [
    "071125821", "03060989", "0158440", "0421258", "051060",
    "0729659877394", "0042366", "079974582", "033388909006",
    "0076559", "07141974", "008547008547",
]

# ---- Logging ----

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("scraper")

# ---- Utility Functions ----

def strip_html(text: str) -> str:
    """Strip HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_root_domain(url: str) -> str:
    """Extract root domain from URL (e.g. 'www.example.co.uk' -> 'example.co.uk')."""
    try:
        parsed = urllib.parse.urlparse(url if '://' in url else f'https://{url}')
        host = parsed.netloc or parsed.path.split('/')[0]
        host = host.lower().split(':')[0]  # remove port
        # Remove www.
        if host.startswith('www.'):
            host = host[4:]
        return host
    except Exception:
        return url.lower()


def is_skip_domain(url: str) -> bool:
    """Check if URL belongs to a skip domain."""
    url_lower = url.lower()
    for d in SKIP_DOMAINS:
        if d in url_lower:
            return True
    return False


def is_valid_email(email: str) -> bool:
    """Validate email: not blacklisted, not example.com, looks real."""
    email_lower = email.lower().strip()
    if email_lower in BLACKLIST_EMAILS:
        return False
    domain = email_lower.split('@')[-1] if '@' in email_lower else ''
    if domain in BLACKLIST_EMAIL_DOMAINS:
        return False
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_lower):
        return False
    # Reject emails with weird patterns
    if 'def.omfcthkdbwca' in email_lower:
        return False
    return True


def is_valid_phone(phone: str) -> bool:
    """Validate phone number."""
    digits = re.sub(r'\D', '', phone)
    # Too short
    if len(digits) < 8:
        return False
    # All zeros or mostly zeros
    if digits.replace('0', '') == '' or len(digits.replace('0', '')) <= 1:
        return False
    # Blacklisted portal numbers
    for bl in BLACKLIST_PHONES:
        if digits.startswith(bl.replace(' ', '')):
            return False
    return True


# ---- State-Tracking ----

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            log.warning("State-Datei beschädigt, starte frisch")
    return {"completed": {}, "scraped_urls": [], "stats": {"total_leads": 0, "total_searches": 0, "last_run": None}}


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


# ---- Brave Search API Key ----

def load_brave_key() -> str:
    key = os.environ.get("BRAVE_API_KEY", "").strip()
    if key:
        return key
    key_paths = [
        Path.home() / ".openclaw" / "workspace" / "scripts" / ".brave_search_key",
        Path(__file__).parent.parent.parent / "scripts" / ".brave_search_key",
    ]
    for p in key_paths:
        if p.exists():
            lines = [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.strip().startswith("#")]
            if lines:
                return lines[0]
    log.error("Kein Brave Search API Key gefunden!")
    sys.exit(1)


# ---- Brave Search ----

def brave_search(query: str, api_key: str, count: int = 10) -> List[dict]:
    headers = {"X-Subscription-Token": api_key, "Accept": "application/json"}
    params = {"q": query, "count": count, "country": "de", "search_lang": "de"}
    try:
        resp = requests.get(BRAVE_ENDPOINT, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("web", {}).get("results", [])
    except requests.RequestException as e:
        log.warning(f"Brave Search Fehler für '{query}': {e}")
        return []


# ---- Website-Analyse ----

def fetch_page(url: str, timeout: int = 10) -> Optional[str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ManniLeads/2.0)"}
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def find_impressum_url(base_url: str, main_html: str) -> Optional[str]:
    """Find impressum/kontakt link on the page."""
    patterns = [
        r'href=["\']([^"\']*impressum[^"\']*)["\']',
        r'href=["\']([^"\']*imprint[^"\']*)["\']',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, main_html, re.IGNORECASE)
        for match in matches:
            url = _resolve_url(base_url, match)
            if url:
                return url
    return None


def find_kontakt_url(base_url: str, main_html: str) -> Optional[str]:
    """Find kontakt/contact link."""
    patterns = [
        r'href=["\']([^"\']*kontakt[^"\']*)["\']',
        r'href=["\']([^"\']*contact[^"\']*)["\']',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, main_html, re.IGNORECASE)
        for match in matches:
            # Skip mailto: links
            if match.startswith('mailto:'):
                continue
            url = _resolve_url(base_url, match)
            if url:
                return url
    return None


def _resolve_url(base_url: str, href: str) -> Optional[str]:
    """Resolve a relative URL to absolute."""
    if not href or href.startswith('#') or href.startswith('javascript:'):
        return None
    if href.startswith('http'):
        return href
    if href.startswith('/'):
        parsed = urllib.parse.urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{href}"
    # Relative
    if '/' in base_url:
        base = base_url.rsplit('/', 1)[0]
        return f"{base}/{href}"
    return None


def extract_impressum_text(html_content: str) -> str:
    """Extract text from an impressum page, cleaned."""
    if not html_content:
        return ""
    # Remove script/style blocks
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Convert <br>, <p>, <div> to newlines
    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|div|h[1-6]|li|tr)>', '\n', text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()


# ---- Impressum Data Extraction ----

def extract_company_name(impressum_text: str) -> str:
    """Extract company name from impressum text."""
    # Pattern 1: Legal forms (GmbH, UG, AG, e.K., OHG, KG, GbR, e.V., etc.)
    legal_forms = r'(?:GmbH(?:\s*&\s*Co\.?\s*KG)?|UG(?:\s*\(haftungsbeschränkt\))?|AG|e\.?\s*K\.?|OHG|KG|GbR|e\.?\s*V\.?|mbH|Inh\.)'
    # Look for "Name + LegalForm"
    pattern = rf'([A-ZÄÖÜ][^\n]{{2,60}}\s+{legal_forms})'
    match = re.search(pattern, impressum_text)
    if match:
        return match.group(1).strip()

    # Pattern 2: After label patterns
    label_patterns = [
        r'(?:Angaben\s+gemäß|Verantwortlich|Betreiber|Firma|Firmenname|Diensteanbieter|Anbieter)\s*(?:i\.?\s*S\.?\s*d\.?\s*§?\s*\d+\s*\w*)?\s*:?\s*\n?\s*(.+?)(?:\n|$)',
    ]
    for p in label_patterns:
        match = re.search(p, impressum_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up: remove leading labels that might have been captured
            name = re.sub(r'^(?:Firmenname|Firma|Inhaber(?:/in)?|Betreiber)\s*:?\s*', '', name, flags=re.IGNORECASE).strip()
            if 3 < len(name) < 80 and not name.startswith('http'):
                return name

    # Pattern 3: Inhaber/inhaberin with name as company (solo businesses)
    match = re.search(r'(?:Inh(?:aber(?:/in|in)?)?\.?)\s*:?\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+(?:\s+e\.?\s*K\.?)?)', impressum_text)
    if match:
        return match.group(1).strip()

    # Pattern 4: First substantial line after "Impressum" heading
    imp_match = re.search(r'Impressum\s*\n(.+?)(?:\n|$)', impressum_text, re.IGNORECASE)
    if imp_match:
        candidate = imp_match.group(1).strip()
        if 3 < len(candidate) < 80 and not any(x in candidate.lower() for x in ['angaben', 'gemäß', 'nach', 'verantwortlich', '§', 'impressum']):
            return candidate

    return ""


def extract_contact_person(impressum_text: str) -> Tuple[str, str]:
    """Extract contact person name and position from impressum."""
    patterns = [
        (r'Geschäftsführ(?:er|erin|ung)\s*:?\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})', "Geschäftsführer"),
        (r'Inhaber(?:in)?\s*:?\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})', "Inhaber"),
        (r'Vertretungsberechtigt(?:er?)?\s*:?\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})', "Geschäftsführer"),
        (r'Verantwortlich(?:er?)?\s*(?:i\.?\s*S\.?\s*d\.?)?\s*:?\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})', "Verantwortlicher"),
        (r'(?:Dr\.|Prof\.)\s*(?:med\.?\s*)?([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})', ""),
    ]
    for pattern, position in patterns:
        match = re.search(pattern, impressum_text)
        if match:
            name = match.group(1).strip()
            # Clean: only take the name, stop at newlines or non-name words
            name = name.split('\n')[0].strip()
            # Remove trailing words that aren't names (Telefon, Email, Fax, etc.)
            name = re.sub(r'\s+(?:Telefon|Tel|Fax|Email|E-Mail|Mobil|Handy|Adresse|Straße|Str).*$', '', name, flags=re.IGNORECASE).strip()
            if 3 < len(name) < 50:
                return name, position
    return "", ""


def extract_emails_from_text(text: str) -> List[str]:
    """Extract valid emails from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    valid = [e for e in emails if is_valid_email(e)]
    # Deduplicate preserving order
    seen = set()
    result = []
    for e in valid:
        el = e.lower()
        if el not in seen:
            seen.add(el)
            result.append(e)
    return result[:3]


def extract_phones_from_text(text: str) -> List[str]:
    """Extract valid phone numbers from text."""
    patterns = [
        r'(?:Tel\.?|Telefon|Phone|Fon|Ruf)\s*:?\s*([+\d\s\-/()]{8,25})',
        r'(?:Mobil|Handy|Funk)\s*:?\s*([+\d\s\-/()]{8,25})',
        r'((?:\+49|0)\s*\(?\d{2,5}\)?\s*[\d\s\-/]{4,15})',
    ]
    phones = []
    for p in patterns:
        for match in re.finditer(p, text, re.IGNORECASE):
            phone = match.group(1).strip() if match.lastindex else match.group(0).strip()
            # Clean trailing punctuation
            phone = re.sub(r'[\-/\s]+$', '', phone).strip()
            if is_valid_phone(phone):
                phones.append(phone)
    # Deduplicate
    seen = set()
    result = []
    for p in phones:
        digits = re.sub(r'\D', '', p)
        if digits not in seen:
            seen.add(digits)
            result.append(p)
    return result[:2]


def extract_social_media(html_content: str, firm_domain: str) -> dict:
    """Extract social media links, filtering share buttons and portal links."""
    social = {}
    patterns = {
        "facebook": r'href=["\']([^"\']*facebook\.com/[^"\']+)["\']',
        "instagram": r'href=["\']([^"\']*instagram\.com/[^"\']+)["\']',
        "linkedin": r'href=["\']([^"\']*linkedin\.com/[^"\']+)["\']',
    }
    for platform, pattern in patterns.items():
        for match in re.finditer(pattern, html_content, re.IGNORECASE):
            url = match.group(1)
            # Skip share buttons
            if '/sharer/' in url or '/share?' in url or 'share.php' in url:
                continue
            # Skip if it's a generic/portal link (very short path or just /page/)
            social[platform] = url
            break  # Take first valid one per platform
    return social


# ---- Impressum-First Analysis ----

def analyze_website(url: str) -> Optional[dict]:
    """
    Analyze a website with Impressum-First approach.
    Returns None if no impressum found (= skip this lead).
    Returns dict with extracted data if impressum exists.
    """
    log.info(f"  Analysiere: {url}")
    main_html = fetch_page(url)
    if not main_html:
        log.debug(f"  → Seite nicht erreichbar")
        return None

    firm_domain = get_root_domain(url)

    # Step 1: Find Impressum
    impressum_html = None
    impressum_url = find_impressum_url(url, main_html)

    if impressum_url:
        time.sleep(0.3)
        impressum_html = fetch_page(impressum_url)

    # Check if main page IS the impressum (some single-pagers)
    main_has_impressum = bool(re.search(
        r'(?:Angaben\s+gemäß|Impressum|Verantwortlich\s+(?:i\.\s*S\.|gemäß)|Betreiber\s*:)',
        main_html, re.IGNORECASE
    ))

    if not impressum_html and not main_has_impressum:
        # Try kontakt page as fallback
        kontakt_url = find_kontakt_url(url, main_html)
        if kontakt_url:
            time.sleep(0.3)
            kontakt_html = fetch_page(kontakt_url)
            if kontakt_html and re.search(r'(?:Angaben|Impressum|Verantwortlich|Inhaber|Geschäftsführer)', kontakt_html, re.IGNORECASE):
                impressum_html = kontakt_html

    if not impressum_html and not main_has_impressum:
        log.info(f"  → Kein Impressum gefunden, überspringe")
        return None

    # Step 2: Extract data from impressum
    imp_text = extract_impressum_text(impressum_html or main_html)

    # Also try extracting from main page for emails/phones if impressum didn't have them
    main_text = extract_impressum_text(main_html) if main_html else ""

    # Company name from impressum
    firma = extract_company_name(imp_text)
    if not firma and main_has_impressum:
        firma = extract_company_name(main_text)

    # Contact person
    ansprechpartner, position = extract_contact_person(imp_text)
    if not ansprechpartner:
        ansprechpartner, position = extract_contact_person(main_text)

    # Emails from impressum first, then main page, then kontakt
    emails = extract_emails_from_text(imp_text)
    if not emails:
        emails = extract_emails_from_text(main_text)
    if not emails:
        # Try kontakt page
        kontakt_url = find_kontakt_url(url, main_html)
        if kontakt_url:
            time.sleep(0.3)
            kontakt_html = fetch_page(kontakt_url)
            if kontakt_html:
                emails = extract_emails_from_text(extract_impressum_text(kontakt_html))

    # Phones from impressum first, then main page
    phones = extract_phones_from_text(imp_text)
    if not phones:
        phones = extract_phones_from_text(main_text)

    # Social media from main page
    social = extract_social_media(main_html, firm_domain)

    # Website quality
    quality = assess_website_quality(url, main_html)

    # Extract visible text for LLM analysis
    website_text = extract_visible_text(main_html, max_chars=1000)

    return {
        "firma": firma,
        "email": emails[0] if emails else "",
        "telefon": phones[0] if phones else "",
        "ansprechpartner": ansprechpartner,
        "position": position,
        "social": social,
        "websiteQualitaet": quality,
        "websiteText": website_text,
    }


def extract_visible_text(html_content: str, max_chars: int = 1000) -> str:
    """Extract visible text content from HTML for LLM analysis."""
    if not html_content:
        return ""
    # Remove script, style, nav, header, footer blocks
    text = re.sub(r'<(?:script|style|nav|header|footer|noscript)[^>]*>.*?</(?:script|style|nav|header|footer|noscript)>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    # Convert block elements to newlines
    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|div|h[1-6]|li|tr|section|article)>', '\n', text, flags=re.IGNORECASE)
    # Strip all remaining tags
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)
    # Remove very short lines (menus, buttons)
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 20]
    text = '\n'.join(lines)
    return text[:max_chars].strip()


def assess_website_quality(url: str, html_content: Optional[str]) -> int:
    if not html_content:
        return 1
    score = 1
    if url.startswith("https"):
        score += 1
    if re.search(r'impressum|imprint', html_content, re.IGNORECASE):
        score += 1
    if re.search(r'facebook\.com|instagram\.com|linkedin\.com', html_content, re.IGNORECASE):
        score += 0.5
    if 'viewport' in html_content.lower():
        score += 0.5
    return min(int(round(score)), 5)


def calculate_score(lead: dict) -> int:
    score = 30
    score += lead.get("websiteQualitaet", 1) * 4
    if lead.get("email"):
        score += 10
    if lead.get("telefon"):
        score += 5
    if lead.get("ansprechpartner"):
        score += 5
    if lead.get("socialMedia"):
        score += 10
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
    if score >= 70:
        return "HOT"
    elif score >= 50:
        return "WARM"
    elif score >= 30:
        return "COLD"
    return "DISQUALIFIED"


# ---- Convex API ----

def push_to_convex(leads: List[dict]) -> bool:
    if not leads:
        return True
    url = f"{CONVEX_URL}/api/mutation"
    headers = {"Content-Type": "application/json"}
    try:
        batch_size = 20
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            payload = {"path": "leads:bulkCreate", "args": {"leads": batch}}
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            if result.get("status") == "success":
                ids = result.get("value", [])
                log.info(f"  Batch {i//batch_size + 1}: {len(ids)} Leads geschrieben")
            else:
                log.warning(f"  Batch {i//batch_size + 1}: Antwort: {result}")
        return True
    except requests.RequestException as e:
        log.error(f"Convex API Fehler: {e}")
        if hasattr(e, 'response') and e.response is not None:
            log.error(f"  Response: {e.response.text[:500]}")
        return False


# ---- Lead-Erstellung ----

def create_lead(result: dict, branche: str, plz: str, website_data: dict) -> dict:
    """Create a lead from Brave result + website analysis data."""
    url = result.get("url", "")
    snippet = strip_html(result.get("description", ""))
    brave_title = strip_html(result.get("title", ""))
    ort = PLZ_ORT_MAP.get(plz, "")

    # Firma: prefer impressum, fallback to cleaned Brave title
    firma = website_data.get("firma", "").strip()
    # Clean up any remaining label prefixes
    firma = re.sub(r'^(?:Firmenname|Firma|Inhaber(?:/in)?|Betreiber|Diensteanbieter|Anbieter|Verantwortlich(?:er?)?|Angaben\s+gemäß[^:]*)\s*:?\s*', '', firma, flags=re.IGNORECASE).strip()
    # Remove trailing address/contact info that got captured
    firma = firma.split('\n')[0].strip()
    firma = re.sub(r'\s+(?:Telefon|Tel|Straße|Str\.|Adresse|PLZ|Postfach|Fax).*$', '', firma, flags=re.IGNORECASE).strip()
    if not firma:
        # Fallback: clean Brave title
        firma = brave_title.split(" - ")[0].split(" | ")[0].split(" – ")[0].strip()
    if len(firma) > 100:
        firma = firma[:100]

    # Google rating from snippet
    google_rating = ""
    rating_match = re.search(r'(\d[,.]?\d?)\s*/\s*5|(\d[,.]?\d?)\s*Sterne', snippet)
    if rating_match:
        google_rating = (rating_match.group(1) or rating_match.group(2)) + "/5"

    now = datetime.now().isoformat()
    social = website_data.get("social", {})

    lead = {
        "firma": firma,
        "website": url,
        "branche": branche,
        "groesse": "",
        "plz": plz,
        "ort": ort,
        "ansprechpartner": website_data.get("ansprechpartner", ""),
        "position": website_data.get("position", ""),
        "email": website_data.get("email", ""),
        "telefon": website_data.get("telefon", ""),
        "websiteQualitaet": website_data.get("websiteQualitaet", 1),
        "socialMedia": bool(social),
        "socialMediaLinks": json.dumps(social) if social else "",
        "googleBewertung": google_rating,
        "score": 0,
        "kiZusammenfassung": "",
        "segment": "COLD",
        "segmentManuell": False,
        "tags": [branche],
        "status": "Neu",
        "websiteText": website_data.get("websiteText", ""),
        "notizen": f"Scraper v2. Snippet: {snippet[:200]}",
        "history": [{"timestamp": now, "aktion": "Erstellt", "details": f"Via Scraper v2 (PLZ {plz})"}],
        "erstelltAm": now,
        "bearbeitetAm": now,
    }

    lead["score"] = calculate_score(lead)
    lead["segment"] = determine_segment(lead["score"])
    return lead


# ---- Hauptlogik ----

def run_scraper(plz_list: List[str], branchen: List[str], dry_run: bool = False,
                output_file: Optional[str] = None, reset_state: bool = False):
    api_key = load_brave_key()
    state = load_state()
    if reset_state:
        state = {"completed": {}, "scraped_urls": [], "stats": {"total_leads": 0, "total_searches": 0, "last_run": None}}
        log.info("State zurückgesetzt")

    total_combinations = len(plz_list) * len(branchen)
    skipped = sum(1 for plz in plz_list for branche in branchen if is_completed(state, plz, branche))
    remaining = total_combinations - skipped

    log.info(f"Start: {len(plz_list)} PLZ × {len(branchen)} Branchen = {total_combinations} Kombinationen")
    if skipped > 0:
        log.info(f"  Überspringe {skipped} bereits abgearbeitete")
    if remaining == 0:
        log.info("Alles schon abgearbeitet! (--reset-state zum Zurücksetzen)")
        return []

    all_leads: List[dict] = []
    seen_domains: set = set()  # Duplikat-Check per root domain
    seen_urls: set = set(state.get("scraped_urls", []))
    last_request_time = 0.0
    search_count = 0
    skipped_no_impressum = 0
    skipped_portal = 0
    skipped_duplicate = 0

    try:
        for plz in plz_list:
            for branche in branchen:
                if is_completed(state, plz, branche):
                    continue

                query = f"{branche} {plz} {PLZ_ORT_MAP.get(plz, '')}"
                log.info(f"Suche [{search_count+1}/{remaining}]: {query}")

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

                combo_leads: List[dict] = []
                for result in results:
                    url = result.get("url", "")

                    # Already scraped?
                    if url in seen_urls:
                        continue

                    # Skip portal domains
                    if is_skip_domain(url):
                        skipped_portal += 1
                        log.debug(f"  ✗ Portal übersprungen: {url}")
                        continue

                    # Duplicate check per root domain
                    root = get_root_domain(url)
                    if root in seen_domains:
                        skipped_duplicate += 1
                        log.debug(f"  ✗ Duplikat (gleiche Domain): {root}")
                        continue

                    # Rate limiting for website fetch
                    elapsed = time.time() - last_request_time
                    if elapsed < 0.5:
                        time.sleep(0.5 - elapsed)

                    # Impressum-First: analyze website
                    website_data = analyze_website(url)
                    last_request_time = time.time()

                    if website_data is None:
                        skipped_no_impressum += 1
                        continue

                    # Create lead
                    lead = create_lead(result, branche, plz, website_data)
                    combo_leads.append(lead)
                    seen_domains.add(root)
                    seen_urls.add(url)
                    state.setdefault("scraped_urls", []).append(url)
                    log.info(f"  ✓ {lead['firma']} — Score: {lead['score']}, Segment: {lead['segment']}, Email: {'✓' if lead['email'] else '✗'}, Tel: {'✓' if lead['telefon'] else '✗'}")

                # Push to Convex
                if combo_leads and not dry_run:
                    success = push_to_convex(combo_leads)
                    if success:
                        state["stats"]["total_leads"] += len(combo_leads)

                all_leads.extend(combo_leads)
                mark_completed(state, plz, branche)
                state["stats"]["total_searches"] += 1
                save_state(state)

    except KeyboardInterrupt:
        log.info("\n⚠️  Abgebrochen! State gespeichert.")
        save_state(state)
        raise

    # Summary
    log.info(f"\n{'='*50}")
    log.info(f"Ergebnis: {len(all_leads)} Leads gesammelt")
    log.info(f"  Portale übersprungen: {skipped_portal}")
    log.info(f"  Kein Impressum: {skipped_no_impressum}")
    log.info(f"  Duplikate: {skipped_duplicate}")

    with_email = sum(1 for l in all_leads if l.get("email"))
    with_phone = sum(1 for l in all_leads if l.get("telefon"))
    with_contact = sum(1 for l in all_leads if l.get("ansprechpartner"))
    log.info(f"  Mit Email: {with_email}/{len(all_leads)}")
    log.info(f"  Mit Telefon: {with_phone}/{len(all_leads)}")
    log.info(f"  Mit Ansprechpartner: {with_contact}/{len(all_leads)}")

    segments = {}
    for lead in all_leads:
        segments[lead["segment"]] = segments.get(lead["segment"], 0) + 1
    for seg, count in sorted(segments.items()):
        log.info(f"  {seg}: {count}")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_leads, f, ensure_ascii=False, indent=2)
        log.info(f"JSON gespeichert: {output_file}")

    if not dry_run and all_leads:
        log.info("(Leads bereits während des Scrapings in Convex geschrieben)")
    elif dry_run:
        log.info("(Dry-Run — nicht in DB geschrieben)")

    save_state(state)
    return all_leads


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(description="ManniLeads Scraper v2 — Impressum-First")
    parser.add_argument("--plz", type=str, default=None)
    parser.add_argument("--branchen", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", "-o", type=str, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--reset-state", action="store_true")
    parser.add_argument("--show-state", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.show_state:
        state = load_state()
        completed_count = sum(len(v) for v in state["completed"].values())
        print(f"\n📊 Scraper-State ({STATE_FILE})")
        print(f"   Abgearbeitete Kombos: {completed_count}")
        print(f"   Gescrapte URLs: {len(state.get('scraped_urls', []))}")
        print(f"   Gesamt-Leads: {state['stats']['total_leads']}")
        print(f"   Letzter Run: {state['stats']['last_run'] or 'nie'}")
        return

    plz_list = args.plz.split(",") if args.plz else DEFAULT_PLZ
    branchen = [b.strip() for b in args.branchen.split(",")] if args.branchen else DEFAULT_BRANCHEN

    log.info("=" * 50)
    log.info("ManniLeads Scraper v2.0 — Impressum-First")
    log.info("=" * 50)

    leads = run_scraper(plz_list, branchen, dry_run=args.dry_run,
                       output_file=args.output, reset_state=args.reset_state)
    log.info(f"\nFertig! {len(leads)} Leads verarbeitet.")


if __name__ == "__main__":
    main()
