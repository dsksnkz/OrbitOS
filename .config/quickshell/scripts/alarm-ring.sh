#!/usr/bin/env bash
set -euo pipefail

label="${1:-Alarm}"
sound="/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"

notify-send -u critical -a "Magnetism Alarm" "Alarm" "$label"

if command -v canberra-gtk-play >/dev/null 2>&1; then
    canberra-gtk-play --id=alarm-clock-elapsed --description="Alarm" >/dev/null 2>&1 || true
elif command -v pw-play >/dev/null 2>&1 && [[ -f "$sound" ]]; then
    pw-play "$sound" >/dev/null 2>&1 || true
fi
