#!/usr/bin/env bash
# Download IPEDS Completions files (1980, 1984-2024) listed in scripts/ipeds_files.txt into ipeds/ (~200 MB, not tracked).
set -euo pipefail
mkdir -p ipeds
while read -r f; do
  [ -s "ipeds/$f.zip" ] || curl -sfL "https://nces.ed.gov/ipeds/datacenter/data/$f.zip" -o "ipeds/$f.zip"
done < "$(dirname "$0")/ipeds_files.txt"
