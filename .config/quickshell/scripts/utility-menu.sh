#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
choice="$(printf '%s\n' \
    'Applications' 'Clipboard' 'Screenshot region' 'Color picker' 'Mission Center' \
    'Audio controls' 'Network controls' 'Files' 'Calculator' 'Timer' 'Web search' \
    'Notifications' 'Installed apps' 'Lock screen' 'Power menu' | rofi -dmenu -p 'OrbitOS Tools')"

case "${choice}" in
    Applications) rofi -show drun ;;
    Clipboard) kitty --class clipse -e clipse ;;
    "Screenshot region") "${script_dir}/capture.sh" ;;
    "Color picker") hyprpicker --autocopy --notify --format=hex ;;
    "Mission Center") missioncenter ;;
    "Audio controls") pavucontrol ;;
    "Network controls") nm-connection-editor ;;
    Files) nautilus --new-window ;;
    Calculator) "${script_dir}/calculator.py" ;;
    Timer) "${script_dir}/timer.sh" ;;
    "Web search") "${script_dir}/web-search.sh" ;;
    Notifications) swaync-client --toggle-panel ;;
    "Installed apps") orbitos-apps ;;
    "Lock screen") hyprlock ;;
    "Power menu") "${script_dir}/power-menu.sh" ;;
esac
