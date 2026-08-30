#!/usr/bin/env bash
set -euo pipefail

if pgrep -x hypridle >/dev/null; then
    systemctl --user stop orbitos-hypridle.service 2>/dev/null || pkill -x hypridle
    notify-send "OrbitOS" "Caffeine enabled — automatic locking is paused"
else
    systemd-run --user --unit=orbitos-hypridle --collect hypridle >/dev/null
    notify-send "OrbitOS" "Caffeine disabled — automatic locking is active"
fi
