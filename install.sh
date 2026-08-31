#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/orbitos/backups"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

if [[ -t 1 ]]; then
    BOLD=$'\e[1m'; DIM=$'\e[2m'; WHITE=$'\e[97m'; RESET=$'\e[0m'
else
    BOLD=""; DIM=""; WHITE=""; RESET=""
fi

cleanup() {
    if [[ -t 1 ]]; then
        printf '\e[?25h'
    fi
}
trap cleanup EXIT INT TERM

say() { printf '%s\n' "$*"; }

ask() {
    local prompt="$1" default="${2:-yes}" answer
    if [[ "$default" == "yes" ]]; then
        read -r -p "$prompt [Y/n] " answer || return 1
        [[ -z "$answer" || "$answer" =~ ^[Yy]$ ]]
    else
        read -r -p "$prompt [y/N] " answer || return 1
        [[ "$answer" =~ ^[Yy]$ ]]
    fi
}

animate_title() {
    local text="ORBITOS" shown="" i
    printf '\n  '
    for ((i = 0; i < ${#text}; i++)); do
        shown+="${text:i:1}"
        printf '\r  %s%s%s%s' "$BOLD" "$WHITE" "$shown" "$RESET"
        [[ -t 1 ]] && sleep 0.045
    done
    printf '\n  %sDotfiles installer%s\n\n' "$DIM" "$RESET"
}

spin() {
    local label="$1" frame=0 log pid status
    local frames=('◐' '◓' '◑' '◒')
    shift
    log="$(mktemp)"
    "$@" >"$log" 2>&1 &
    pid=$!
    [[ -t 1 ]] && printf '\e[?25l'
    while kill -0 "$pid" 2>/dev/null; do
        printf '\r  %s %s' "${frames[frame]}" "$label"
        frame=$(((frame + 1) % ${#frames[@]}))
        sleep 0.08
    done
    if wait "$pid"; then
        printf '\r  ✓ %s\n' "$label"
        rm -f -- "$log"
    else
        status=$?
        printf '\r  ✗ %s\n' "$label"
        sed 's/^/    /' "$log" >&2
        rm -f -- "$log"
        return "$status"
    fi
}

MANAGED_PATHS=(
    ".config/btop"
    ".config/cava"
    ".config/fastfetch"
    ".config/gtk-3.0"
    ".config/gtk-4.0"
    ".config/hypr"
    ".config/kdeglobals"
    ".config/kitty"
    ".config/qt6ct"
    ".config/quickshell"
    ".config/rofi"
    ".config/swaync"
    ".config/wlogout"
    ".local/bin/orbitos-tools"
    ".local/bin/orbitos-apps"
    ".local/bin/orbitos-launcher"
    ".local/bin/orbitos-game"
    ".local/bin/orbitos-settings"
    ".local/lib/orbitos"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitApps.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.Launcher.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.GameAccelerator.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.Settings.desktop"
)

backup_existing() {
    local relative found=false
    mkdir -p -- "$BACKUP_DIR"
    for relative in "${MANAGED_PATHS[@]}"; do
        if [[ -e "$HOME/$relative" || -L "$HOME/$relative" ]]; then
            (cd -- "$HOME" && cp -a --parents -- "$relative" "$BACKUP_DIR")
            found=true
        fi
    done
    [[ "$found" == true ]] || rmdir -- "$BACKUP_DIR"
}

copy_tree() {
    mkdir -p -- "$2"
    cp -a -- "$1/." "$2/"
}

install_dotfiles() {
    local relative source destination entry name
    for relative in "${MANAGED_PATHS[@]}"; do
        source="$REPO_DIR/$relative"
        destination="$HOME/$relative"
        [[ -e "$source" || -L "$source" ]] || continue

        if [[ "$relative" == ".config/hypr" ]]; then
            mkdir -p -- "$destination"
            shopt -s dotglob nullglob
            for entry in "$source"/*; do
                name="${entry##*/}"
                if [[ "$INSTALL_MONITORS" == false && ("$name" == "monitors.conf" || "$name" == "monitors.lua") ]]; then
                    continue
                fi
                cp -a -- "$entry" "$destination/"
            done
            shopt -u dotglob nullglob
        elif [[ -d "$source" ]]; then
            copy_tree "$source" "$destination"
        else
            mkdir -p -- "$(dirname -- "$destination")"
            cp -a -- "$source" "$destination"
        fi
    done
}

rewrite_home_paths() {
    local file escaped_home="${HOME//&/\\&}"
    local files=(
        "$HOME/.config/fastfetch/config.jsonc"
        "$HOME/.config/hypr/hyprlock.conf"
        "$HOME/.config/hypr/hyprpaper.conf"
        "$HOME/.config/qt6ct/qt6ct.conf"
        "$HOME/.local/share/applications/io.github.dsksnkz.OrbitOS.desktop"
        "$HOME/.local/share/applications/io.github.dsksnkz.OrbitApps.desktop"
        "$HOME/.local/share/applications/io.github.dsksnkz.OrbitOS.Launcher.desktop"
        "$HOME/.local/share/applications/io.github.dsksnkz.OrbitOS.GameAccelerator.desktop"
        "$HOME/.local/share/applications/io.github.dsksnkz.OrbitOS.Settings.desktop"
    )
    for file in "${files[@]}"; do
        [[ -f "$file" ]] && sed -i "s|/home/matte|$escaped_home|g" "$file"
    done
}

animate_title

if [[ ! -d "$REPO_DIR/.config/hypr" ]]; then
    say "  Error: run this script from the OrbitOS repository."
    exit 1
fi

if [[ -r /etc/os-release ]] && ! grep -q '^ID=arch$' /etc/os-release; then
    say "  ${DIM}Warning: OrbitOS is designed for Arch Linux.${RESET}"
fi

if ask "  Back up existing managed dotfiles?" yes; then
    CREATE_BACKUP=true
else
    CREATE_BACKUP=false
    if ! ask "  Continue without a backup?" no; then
        say "\n  Installation cancelled."
        exit 0
    fi
fi

if ask "  Apply the included HDMI/eDP monitor layout?" no; then
    INSTALL_MONITORS=true
else
    INSTALL_MONITORS=false
fi

say
if [[ "$CREATE_BACKUP" == true ]]; then
    spin "Backing up existing dotfiles" backup_existing
    if [[ -d "$BACKUP_DIR" ]]; then
        say "    ${DIM}$BACKUP_DIR${RESET}"
    else
        say "    ${DIM}No existing managed dotfiles were found.${RESET}"
    fi
fi

spin "Installing OrbitOS dotfiles" install_dotfiles
spin "Adapting paths for $USER" rewrite_home_paths

if command -v hyprctl >/dev/null 2>&1 && [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    hyprctl reload >/dev/null 2>&1 || true
fi

say
say "  ${BOLD}OrbitOS installed.${RESET}"
say "  Log out and back in to start every desktop component."
say
