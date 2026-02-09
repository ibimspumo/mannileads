#!/usr/bin/env python3
"""
ManniLeads Enrich — Nachträgliche KI-Analyse für Leads ohne Pitch.
Holt Leads ohne kiAnsprache aus Convex, fetcht Website nochmal, 
lässt Gemini analysieren, patched den Lead in Convex.
"""

import json
import logging
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip3 install requests")
    sys.exit(1)

# Importiere Funktionen aus scraper.py
sys.path.insert(0, str(Path(__file__).parent))
from scraper import (
    collect_website_data, analyze_with_gemini, CONVEX_URL, 
    OPENROUTER_URL, GEMINI_MODEL, _load_branchen
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

# Load API key
_key_file = Path(__file__).parent.parent.parent / "scripts" / ".openrouter_key"
if not _key_file.exists():
    _key_file = Path(__file__).parent / ".openrouter_key"
if not _key_file.exists():
    # Try workspace root
    _key_file = Path("/Users/manfredbellmann/.openclaw/workspace/scripts/.openrouter_key")

OPENROUTER_KEY = _key_file.read_text().strip() if _key_file.exists() else ""


def get_leads_without_pitch() -> list:
    """Hole alle Leads ohne KI-Analyse aus Convex."""
    resp = requests.post(f"{CONVEX_URL}/api/query", json={
        "path": "leads:list", "args": {}
    }, headers={"Content-Type": "application/json"}, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    if result.get("status") != "success":
        log.error(f"Convex query failed: {result}")
        return []
    
    leads = result.get("value", [])
    # Filter: kein kiAnsprache oder leer
    return [l for l in leads if not l.get("kiAnsprache")]


def update_lead(lead_id: str, ki_data: dict) -> bool:
    """Update einen Lead in Convex mit KI-Daten."""
    # Map Gemini output to Convex fields
    update_fields = {}
    field_map = {
        "kiZusammenfassung": "kiZusammenfassung",
        "kiZielgruppe": "kiZielgruppe",
        "kiOnlineAuftritt": "kiOnlineAuftritt",
        "kiSchwaechen": "kiSchwaechen",
        "kiChancen": "kiChancen",
        "kiAnsprache": "kiAnsprache",
        "kiAnspracheSig": "kiAnspracheSig",
        "kiScore": "kiScore",
        "kiScoreBegruendung": "kiScoreBegruendung",
        "tags": "tags",
    }
    
    for gemini_key, convex_key in field_map.items():
        val = ki_data.get(gemini_key)
        if val is not None:
            update_fields[convex_key] = val
    
    if not update_fields:
        return False
    
    update_fields["kiAnalysiert"] = True
    update_fields["kiAnalysiertAm"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Score + Segment
    ki_score = ki_data.get("kiScore", 50)
    if isinstance(ki_score, str):
        try: ki_score = int(ki_score)
        except: ki_score = 50
    ki_score = max(0, min(100, ki_score))
    update_fields["kiScore"] = ki_score
    update_fields["score"] = ki_score
    
    if ki_score >= 70:
        update_fields["segment"] = "HOT"
        update_fields["kiSegment"] = "HOT"
    elif ki_score >= 50:
        update_fields["segment"] = "WARM"
        update_fields["kiSegment"] = "WARM"
    elif ki_score >= 30:
        update_fields["segment"] = "COLD"
        update_fields["kiSegment"] = "COLD"
    else:
        update_fields["segment"] = "DISQUALIFIED"
        update_fields["kiSegment"] = "DISQUALIFIED"

    resp = requests.post(f"{CONVEX_URL}/api/mutation", json={
        "path": "leads:patch", "args": {"id": lead_id, **update_fields}
    }, headers={"Content-Type": "application/json"}, timeout=30)
    
    result = resp.json()
    return result.get("status") == "success"


def main():
    if not OPENROUTER_KEY:
        log.error("OpenRouter Key nicht gefunden!")
        sys.exit(1)
    
    leads = get_leads_without_pitch()
    log.info(f"Leads ohne KI-Analyse: {len(leads)}")
    
    if not leads:
        log.info("Nichts zu tun!")
        return
    
    enriched = 0
    failed = 0
    skipped = 0
    
    for i, lead in enumerate(leads):
        firma = lead.get("firma", "?")
        website = lead.get("website", "")
        branche = lead.get("branche", "")
        plz = lead.get("plz", "")
        ort = lead.get("ort", "")
        lead_id = lead.get("_id", "")
        
        log.info(f"[{i+1}/{len(leads)}] {firma} ({website})")
        
        if not website or not website.startswith("http"):
            log.warning(f"  Keine gültige Website, überspringe")
            skipped += 1
            continue
        
        # Website nochmal fetchen
        time.sleep(0.5)
        website_data = collect_website_data(website)
        if website_data is None:
            log.warning(f"  Website nicht erreichbar oder kein Impressum")
            skipped += 1
            continue
        
        # Gemini analysieren
        time.sleep(0.3)
        gemini_data = analyze_with_gemini(website_data, branche, plz, ort, OPENROUTER_KEY)
        if gemini_data is None:
            log.warning(f"  Gemini-Analyse fehlgeschlagen")
            failed += 1
            continue
        
        # Update in Convex
        if update_lead(lead_id, gemini_data):
            score = gemini_data.get("kiScore", "?")
            log.info(f"  ✓ Enriched! Score: {score}")
            enriched += 1
        else:
            log.warning(f"  ✗ Convex-Update fehlgeschlagen")
            failed += 1
    
    log.info(f"\n{'='*60}")
    log.info(f"ERGEBNIS: {enriched} enriched, {failed} fehlgeschlagen, {skipped} übersprungen")


if __name__ == "__main__":
    main()
