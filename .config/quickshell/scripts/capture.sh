#!/usr/bin/env bash
set -euo pipefail

target_dir="${HOME}/Pictures/Screenshots"
target="${target_dir}/OrbitOS-$(date +%Y-%m-%d-%H%M%S).png"
mkdir -p "${target_dir}"
geometry="$(slurp)" || exit 0
grim -g "${geometry}" "${target}"
wl-copy < "${target}"
notify-send -i "${target}" "Screenshot captured" "Saved to ${target} and copied to clipboard"
