#!/usr/bin/env bash
# Download the GSS public-use files (1972-2025) listed in scripts/puf_urls.txt into puf/ (~460 MB, not tracked by git).
set -euo pipefail
mkdir -p puf
while read -r p; do
  f="puf/$(basename "$p")"
  [ -s "$f" ] || curl -sfL "https://ncses.nsf.gov$p" -o "$f"
done < "$(dirname "$0")/puf_urls.txt"
