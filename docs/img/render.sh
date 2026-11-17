#!/usr/bin/env bash
# Render every *.mmd in this folder to .svg (the .mmd is the source of truth).
set -euo pipefail
cd "$(dirname "$0")"
export PUPPETEER_SKIP_DOWNLOAD=1
for f in *.mmd; do
  npx -y @mermaid-js/mermaid-cli@11 -i "$f" -o "${f%.mmd}.svg" -p pconf.json -c mmdconf.json -b transparent
done
