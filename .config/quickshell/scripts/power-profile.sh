#!/usr/bin/env bash
set -euo pipefail

current="$(powerprofilesctl get)"
case "${current}" in
    power-saver) next="balanced" ;;
    balanced) next="performance" ;;
    *) next="power-saver" ;;
esac
powerprofilesctl set "${next}"
notify-send "OrbitOS" "Power profile: ${next}"
