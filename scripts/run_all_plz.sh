#!/bin/bash
# Kompletter Scrape: Alle PLZ × alle Branchen
# Läuft im Hintergrund, State wird gespeichert, kann jederzeit gestoppt/neugestartet werden

cd "$(dirname "$0")"
export BRAVE_API_KEY=BSAuXhoQffvTOlm2zE5nmDNMYrZ4r4G
LOG="/tmp/scraper_full.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') === KOMPLETTER SCRAPE GESTARTET ===" >> "$LOG"

# Alle PLZ aus plz_config.json + scraper default
ALL_PLZ=$(python3 -c "
import json
from scraper import PLZ_ORT_MAP
for plz in sorted(PLZ_ORT_MAP.keys()):
    print(plz)
")

TOTAL=$(echo "$ALL_PLZ" | wc -l | tr -d ' ')
COUNT=0

for PLZ in $ALL_PLZ; do
    COUNT=$((COUNT + 1))
    ORT=$(python3 -c "from scraper import PLZ_ORT_MAP; print(PLZ_ORT_MAP.get('$PLZ','?'))")
    echo "$(date '+%Y-%m-%d %H:%M:%S') === [$COUNT/$TOTAL] PLZ $PLZ ($ORT) ===" >> "$LOG"
    python3 -u scraper.py --plz "$PLZ" --stadt "$ORT" >> "$LOG" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') === FERTIG PLZ $PLZ ===" >> "$LOG"
done

echo "$(date '+%Y-%m-%d %H:%M:%S') === KOMPLETTER SCRAPE ABGESCHLOSSEN ===" >> "$LOG"
