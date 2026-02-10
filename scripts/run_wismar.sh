#!/bin/bash
cd "$(dirname "$0")"
LOG="/tmp/scraper_wismar.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') === WISMAR SCRAPE START ===" > "$LOG"

for PLZ in 23952 23966 23968 23970; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') === PLZ $PLZ (Wismar) ===" >> "$LOG"
    python3 -u scraper.py --plz "$PLZ" --stadt "Wismar" >> "$LOG" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') === FERTIG PLZ $PLZ ===" >> "$LOG"
done

echo "$(date '+%Y-%m-%d %H:%M:%S') === WISMAR KOMPLETT ===" >> "$LOG"
