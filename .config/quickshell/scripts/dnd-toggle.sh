#!/usr/bin/env bash
set -euo pipefail

state="$(swaync-client --skip-wait -d)"
if [[ "${state}" == "true" ]]; then
    notify-send "OrbitOS" "Do Not Disturb enabled"
else
    notify-send "OrbitOS" "Do Not Disturb disabled"
fi
