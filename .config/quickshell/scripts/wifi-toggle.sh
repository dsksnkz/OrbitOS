#!/usr/bin/env bash
set -euo pipefail

if [[ "$(nmcli -t -f WIFI general)" == "enabled" ]]; then
    nmcli radio wifi off
    notify-send "OrbitOS" "Wi-Fi disabled"
else
    nmcli radio wifi on
    notify-send "OrbitOS" "Wi-Fi enabled"
fi
