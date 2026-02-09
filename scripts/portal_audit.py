#!/usr/bin/env python3
"""
Portal-Audit für ManniLeads
Analysiert alle Leads aus Convex und findet Portal-Domains die noch nicht auf der Skip-Liste sind.
"""

import json
import subprocess
import re
from urllib.parse import urlparse
from collections import Counter
from pathlib import Path

# Bestehende SKIP_DOMAINS aus scraper.py
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
    "online-tischreservierung.de", "cafes-in-der-nahe.de", "nochoffen.de",
    "finderr.de", "yellowmap.de", "onlineplan.info", "immosuchmaschine.de",
    "anwaltsverzeichnis.de", "steuer-berater.de", "behoerdenverzeichnis.mv-serviceportal.de",
    "steuerberater-tipps.de",
    "fahrschule-online.de", "blume2000.de", "blumenversand-edelweiss.de",
    "abvz.de", "deutschebiz.de",
    "stadtbranchenbuch.com", "branchenbuch24.com", "branchenbuchdeutschland.de",
    "coiffeur-24.de", "total-lokal.de", "exilon.de", "plusbranchenbuch.com",
    "letitshine.de",
    "werkenntdenbesten.de", "meinprospekt.de",
    "hoeffner.de", "sb-moebel-boss.de", "moebel-boss.de", "xxxlutz.de",
    "porta.de", "poco.de", "roller.de", "ikea.com", "otto.de",
    "amazon.de", "ebay.de", "real.de", "kaufland.de", "lidl.de", "aldi",
    "mediamarkt.de", "saturn.de", "expert.de", "conrad.de",
    "obi.de", "bauhaus.info", "toom.de", "hornbach.de",
    "studienkreis.de", "kayak.de", "finanzberater.net", "experten-branchenbuch.de",
    "erstenachhilfe.de", "billiger-mietwagen.de", "anwaltinfos.de",
    "mcmakler.de", "von-poll.com", "jacasa.de", "sprachschule-aktiv.de",
    "musikschulen.de", "starcar.de",
    "bauunternehmen.org", "schlosser-portal.de", "kennstdueinen.de",
    "dienstleistung-rostock.de", "zimmerer-portal.de", "tischler-schreiner.org",
    "trockenbau-regional.de", "trockenbauunternehmen.net", "fliesenleger.net",
    "schreiner-tischler.de", "starofservice.de", "therapie.de",
    "mobile.de", "sixt.de", "lieferando.de", "tui.com", "visit-mv.com",
    "volkswagen.de", "vw-rostock.de",
]

PORTAL_KEYWORDS = [
    "branchenbuch", "portal", "verzeichnis", "vergleich", "bewertung",
    "finden", "suche", "gewerbe", "firmen", "anbieter", "dienstleister",
    "check24", "billiger", "vergleich", "online-", "bewertungsportal",
    "regional", "stadt-", "-in-der-naehe", "lokal", "findest", "branchenportal"
]

def get_all_leads():
    """Alle Leads aus Convex holen"""
    print("📥 Hole alle Leads aus Convex...")
    
    import requests
    
    url = "https://energetic-civet-402.convex.cloud/api/query"
    payload = {
        "path": "leads:list",
        "args": {}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'value' in data:
            leads = data['value']
        elif isinstance(data, list):
            leads = data
        else:
            leads = []
        
        print(f"✓ {len(leads)} Leads abgerufen")
        return leads
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Leads: {e}")
        return []

def extract_domain(url):
    """Domain aus URL extrahieren"""
    if not url:
        return None
    
    # Normalize URL
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except:
        return None

def is_likely_portal(domain):
    """Prüft ob eine Domain wie ein Portal aussieht"""
    domain_lower = domain.lower()
    
    # Check against keywords
    for keyword in PORTAL_KEYWORDS:
        if keyword in domain_lower:
            return True
    
    # Check if it's too generic (e.g., friseur-24.de statt "salon-mueller.de")
    parts = domain_lower.replace('.de', '').replace('.com', '').split('-')
    generic_terms = ['24', '365', 'online', 'digital', 'info', 'service', 'portal', 'finder', 'suche']
    if any(term in parts for term in generic_terms):
        return True
    
    return False

def main():
    print("🔍 Portal-Audit — ManniLeads in Convex\n")
    print("=" * 80)
    
    # 1. Leads holen
    leads = get_all_leads()
    if not leads:
        print("❌ Keine Leads gefunden!")
        return
    
    # 2. Websites extrahieren
    print(f"\n📊 Analysiere {len(leads)} Leads...")
    websites = []
    domains = []
    
    for lead in leads:
        website = lead.get('website', '')
        if website:
            websites.append(website)
            domain = extract_domain(website)
            if domain:
                domains.append(domain)
    
    print(f"✓ {len(websites)} Leads haben eine Website")
    print(f"✓ {len(domains)} gültige Domains extrahiert")
    
    # 3. Domains zählen
    domain_counts = Counter(domains)
    
    # 4. Häufige Domains (>3x)
    frequent_domains = {d: c for d, c in domain_counts.items() if c > 3}
    print(f"\n🔥 {len(frequent_domains)} Domains kommen mehr als 3x vor (verdächtig!)")
    
    # 5. Portal-Prüfung
    suspected_portals = []
    new_portals = []  # Noch nicht in SKIP_DOMAINS
    
    for domain, count in domain_counts.items():
        # Check if already in SKIP_DOMAINS
        is_known = any(skip in domain for skip in SKIP_DOMAINS)
        
        # Check if looks like portal
        looks_like_portal = is_likely_portal(domain)
        
        if looks_like_portal or count > 3:
            suspected_portals.append({
                'domain': domain,
                'count': count,
                'known': is_known,
                'looks_like_portal': looks_like_portal
            })
            
            if not is_known:
                new_portals.append({
                    'domain': domain,
                    'count': count,
                    'reason': 'Häufig + Portal-Muster' if looks_like_portal else f'{count}x vorkommen'
                })
    
    # 6. Report erstellen
    report_path = Path("/Users/manfredbellmann/.openclaw/workspace/mannileads/scripts/portal_audit_report.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Portal-Audit Report — ManniLeads\n\n")
        f.write(f"**Erstellt:** {subprocess.check_output(['date']).decode().strip()}\n\n")
        f.write("---\n\n")
        
        f.write("## 📊 Zusammenfassung\n\n")
        f.write(f"- **Leads geprüft:** {len(leads)}\n")
        f.write(f"- **Unique Domains:** {len(set(domains))}\n")
        f.write(f"- **Verdächtige Domains:** {len(suspected_portals)}\n")
        f.write(f"- **NEUE Portale (nicht in SKIP_DOMAINS):** {len(new_portals)}\n")
        f.write(f"- **Betroffene Leads:** {sum(p['count'] for p in new_portals)}\n\n")
        
        f.write("---\n\n")
        
        # Neue Portale (Hauptfokus!)
        f.write("## 🚨 NEUE Portal-Domains (nicht in SKIP_DOMAINS)\n\n")
        if new_portals:
            f.write("Diese Domains sollten zur SKIP_DOMAINS Liste hinzugefügt werden:\n\n")
            f.write("| Domain | Anzahl Leads | Grund |\n")
            f.write("|--------|-------------|-------|\n")
            
            for p in sorted(new_portals, key=lambda x: x['count'], reverse=True):
                f.write(f"| `{p['domain']}` | {p['count']} | {p['reason']} |\n")
            
            f.write("\n### 📝 Kopiervorlage für scraper.py\n\n")
            f.write("```python\n")
            f.write("# Neu hinzufügen:\n")
            for p in sorted(new_portals, key=lambda x: x['count'], reverse=True):
                f.write(f'    "{p["domain"]}",\n')
            f.write("```\n\n")
        else:
            f.write("✅ Keine neuen Portal-Domains gefunden! Alle bekannten Portale werden bereits gefiltert.\n\n")
        
        f.write("---\n\n")
        
        # Domains mit >3 Leads (alle, auch bekannte)
        f.write("## ⚠️ Domains mit mehr als 3 Leads\n\n")
        f.write("Echte lokale Firmen haben normalerweise eigene Domains. Wenn eine Domain oft vorkommt, ist es wahrscheinlich ein Portal.\n\n")
        f.write("| Domain | Anzahl | Status |\n")
        f.write("|--------|--------|--------|\n")
        
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 3:
                is_known = any(skip in domain for skip in SKIP_DOMAINS)
                status = "✅ Bereits gefiltert" if is_known else "🚨 NEU!"
                f.write(f"| `{domain}` | {count} | {status} |\n")
        
        f.write("\n---\n\n")
        
        # Alle verdächtigen Domains
        f.write("## 🔍 Alle verdächtigen Domains (Portal-Muster)\n\n")
        f.write("Domains die Portal-Keywords enthalten oder generisch klingen:\n\n")
        f.write("| Domain | Anzahl | Status |\n")
        f.write("|--------|--------|--------|\n")
        
        for p in sorted(suspected_portals, key=lambda x: x['count'], reverse=True):
            status = "✅ Bekannt" if p['known'] else "🚨 NEU"
            f.write(f"| `{p['domain']}` | {p['count']} | {status} |\n")
    
    print(f"\n✅ Report erstellt: {report_path}")
    print(f"\n🎯 Ergebnis:")
    print(f"   - {len(domains)} Domains geprüft")
    print(f"   - {len(new_portals)} NEUE Portal-Domains gefunden")
    print(f"   - {sum(p['count'] for p in new_portals)} Leads betroffen")
    
    if new_portals:
        print(f"\n📝 Top 10 neue Portale:")
        for p in sorted(new_portals, key=lambda x: x['count'], reverse=True)[:10]:
            print(f"   • {p['domain']} ({p['count']}x)")
    
    return len(new_portals), sum(p['count'] for p in new_portals), len(domains)

if __name__ == "__main__":
    main()
