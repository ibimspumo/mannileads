#!/bin/bash
# Alle 5 restlichen Schwerin-PLZ nacheinander
for PLZ in 19053 19057 19059 19061 19063; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') === STARTE PLZ $PLZ ===" >> /tmp/scraper_all.log
    python3 -u scraper.py --plz $PLZ --stadt Schwerin >> /tmp/scraper_all.log 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') === FERTIG PLZ $PLZ ===" >> /tmp/scraper_all.log
done
echo "$(date '+%Y-%m-%d %H:%M:%S') === ALLE FERTIG ===" >> /tmp/scraper_all.log
