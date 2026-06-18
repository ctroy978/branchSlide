#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    cat <<'EOF'
Usage: scripts/open_projector_browser.sh PROJECTOR_URL

Open the projector page in a browser that allows teacher-triggered audio
without requiring a click on the presenter screen.

Example:
  scripts/open_projector_browser.sh http://192.168.1.50:8001/ABCD

On the TV computer, use this script (or the same Chromium flag) instead of
opening the URL in a normal browser tab.
EOF
    exit 1
fi

url="$1"

for bin in chromium google-chrome-stable google-chrome chromium-browser; do
    if command -v "$bin" >/dev/null 2>&1; then
        exec "$bin" \
            --autoplay-policy=no-user-gesture-required \
            --new-window \
            "$url"
    fi
done

echo "No Chromium-based browser found." >&2
echo "Install chromium, or launch your browser with:" >&2
echo "  --autoplay-policy=no-user-gesture-required" >&2
exit 1