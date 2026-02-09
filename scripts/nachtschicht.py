#!/usr/bin/env python3
"""
Nachtschicht-Script: 50 PLZ um Schwerin herum scrapen.
Läuft als nohup-Prozess, schreibt Fortschritt in Log.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 50 PLZ: Schwerin (6) + Umland (44)
# Schwerin direkt
SCHWERIN = [
    ("19053", "Schwerin"),
    ("19055", "Schwerin"),
    ("19057", "Schwerin"),
    ("19059", "Schwerin"),
    ("19061", "Schwerin"),
    ("19063", "Schwerin"),
]

# Nahes Umland (direkt angrenzend, <15km)
NAHES_UMLAND = [
    ("19065", "Raben Steinfeld"),
    ("19067", "Leezen"),
    ("19069", "Lübstorf"),
    ("19071", "Brüsewitz"),
    ("19073", "Wittenförden"),
    ("19075", "Pampow"),
    ("19077", "Rastow"),
    ("19079", "Banzkow"),
]

# Weiteres Umland (15-40km)
WEITERES_UMLAND = [
    ("19086", "Crivitz"),
    ("19089", "Crivitz"),
    ("19205", "Gadebusch"),
    ("19209", "Lützow"),
    ("19230", "Hagenow"),
    ("19243", "Wittenburg"),
    ("19246", "Zarrentin"),
    ("19258", "Boizenburg"),
    ("19260", "Vellahn"),
    ("19288", "Ludwigslust"),
    ("19294", "Eldena"),
    ("19300", "Grabow"),
    ("19306", "Neustadt-Glewe"),
    ("19309", "Lenzen"),
    ("19322", "Wittenberge"),
    ("19336", "Bad Wilsnack"),
    ("19348", "Perleberg"),
    ("19370", "Parchim"),
    ("19372", "Spornitz"),
    ("19374", "Domsühl"),
    ("19376", "Matzlow"),
    ("19386", "Lübz"),
    ("19395", "Plau am See"),
    ("19399", "Goldberg"),
    ("19406", "Sternberg"),
    ("19412", "Brüel"),
    ("19417", "Warin"),
    ("23936", "Grevesmühlen"),
    ("23942", "Dassow"),
    ("23946", "Boltenhagen"),
    ("23952", "Wismar"),
    ("23966", "Wismar"),
    ("23968", "Wismar"),
    ("23970", "Wismar"),
    ("23972", "Dorf Mecklenburg"),
    ("23974", "Neuburg"),
    ("23992", "Neukloster"),
    ("23996", "Bad Kleinen"),
    ("18209", "Bad Doberan"),
    ("18225", "Kühlungsborn"),
]

ALL_PLZ = SCHWERIN + NAHES_UMLAND + WEITERES_UMLAND

SCRAPER = Path(__file__).parent / "scraper.py"
LOG_DIR = Path("/tmp")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_batch(plz_list, stadt_map, batch_name):
    """Run scraper for a batch of PLZ."""
    plz_str = ",".join([p for p, _ in plz_list])
    
    # Update PLZ_ORT_MAP via --stadt won't work for mixed cities
    # Instead we'll modify the scraper's PLZ_ORT_MAP dynamically
    # Write a temp config
    config = {p: s for p, s in plz_list}
    config_file = Path(__file__).parent / "plz_config.json"
    config_file.write_text(json.dumps(config, ensure_ascii=False))
    
    log(f"Starte Batch '{batch_name}': {len(plz_list)} PLZ ({plz_str[:60]}...)")
    
    cmd = [
        sys.executable, "-u", str(SCRAPER),
        "--plz", plz_str,
        "-o", str(LOG_DIR / f"leads_{batch_name}.json"),
    ]
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode == 0:
        log(f"Batch '{batch_name}' erfolgreich abgeschlossen")
    else:
        log(f"Batch '{batch_name}' beendet mit Code {result.returncode}")

def main():
    log("=" * 60)
    log("NACHTSCHICHT GESTARTET")
    log(f"Gesamt: {len(ALL_PLZ)} PLZ × 20 Branchen = {len(ALL_PLZ) * 20} Kombinationen")
    log("=" * 60)
    
    # Run as single scraper call with all PLZ
    # The scraper has state tracking, so it resumes on crash
    plz_str = ",".join([p for p, _ in ALL_PLZ])
    
    # Write PLZ-Stadt mapping for the scraper to use
    config = {p: s for p, s in ALL_PLZ}
    config_file = Path(__file__).parent / "plz_config.json"
    config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2))
    log(f"PLZ-Config geschrieben: {config_file}")
    
    cmd = [
        sys.executable, "-u", str(SCRAPER),
        "--plz", plz_str,
        "-o", str(LOG_DIR / "leads_nachtschicht.json"),
    ]
    
    log(f"Starte Scraper: {' '.join(cmd[:6])}...")
    subprocess.run(cmd)
    
    log("NACHTSCHICHT BEENDET")

if __name__ == "__main__":
    main()
