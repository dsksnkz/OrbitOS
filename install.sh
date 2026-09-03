#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/orbitos/backups"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
ASSUME_YES=false
DRY_RUN=false
INSTALL_PACKAGES=true

PACMAN_PACKAGES=(
    hyprland hyprpaper hypridle hyprlock xdg-desktop-portal-hyprland
    quickshell kitty rofi swaync swayosd brightnessctl playerctl grim slurp
    wl-clipboard btop cava fastfetch nautilus pavucontrol networkmanager
    network-manager-applet bluez bluez-utils blueman power-profiles-daemon
    mission-center python-gobject gtk4 libadwaita polkit-gnome qt6ct
    ttf-jetbrains-mono-nerd noto-fonts ddcutil gamemode gamescope hyprpicker
    pipewire pipewire-pulse wireplumber libnotify flatpak lm_sensors pciutils
    desktop-file-utils xdg-utils
)
AUR_PACKAGES=(wlogout clipse tide-island)

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
    if [[ "$ASSUME_YES" == true ]]; then
        return 0
    fi
    if [[ "$default" == "yes" ]]; then
        read -r -p "$prompt [Y/n] " answer || return 1
        [[ -z "$answer" || "$answer" =~ ^[Yy]$ ]]
    else
        read -r -p "$prompt [y/N] " answer || return 1
        [[ "$answer" =~ ^[Yy]$ ]]
    fi
}

usage() {
    cat <<'EOF'
Usage: ./install.sh [options]

  -y, --yes          Accept recommended prompts (monitor layout stays opt-in)
      --no-packages  Install dotfiles only
      --dry-run      Show package and file actions without changing the system
  -h, --help         Show this help
EOF
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

run_step() {
    local label="$1"
    shift
    if [[ "$DRY_RUN" == true ]]; then
        printf '  · %s: ' "$label"
        printf '%q ' "$@"
        printf '\n'
        return 0
    fi
    spin "$label" "$@"
}

missing_repo_packages() {
    local package
    for package in "${PACMAN_PACKAGES[@]}"; do
        pacman -Q "$package" >/dev/null 2>&1 || printf '%s\n' "$package"
    done
}

install_repo_packages() {
    local -a missing=()
    mapfile -t missing < <(missing_repo_packages)
    ((${#missing[@]} == 0)) && return 0
    sudo pacman -S --needed --noconfirm "${missing[@]}"
}

aur_helper() {
    command -v paru 2>/dev/null || command -v yay 2>/dev/null || true
}

install_aur_packages() {
    local helper package
    local -a missing=()
    helper="$(aur_helper)"
    [[ -n "$helper" ]] || return 2
    for package in "${AUR_PACKAGES[@]}"; do
        pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
    done
    ((${#missing[@]} == 0)) && return 0
    "$helper" -S --needed --noconfirm "${missing[@]}"
}

enable_services() {
    local service
    for service in NetworkManager.service bluetooth.service; do
        systemctl list-unit-files "$service" >/dev/null 2>&1 || continue
        sudo systemctl enable --now "$service"
    done
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
    ".local/bin/orbitos-boot"
    ".local/bin/orbitos-launcher"
    ".local/bin/orbitos-game"
    ".local/bin/orbitos-settings"
    ".local/lib/orbitos"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitApps.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.Launcher.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.GameAccelerator.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.Settings.desktop"
    ".local/share/applications/io.github.dsksnkz.OrbitOS.Boot.desktop"
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
        "$HOME/.local/share/applications/io.github.dsksnkz.OrbitOS.Boot.desktop"
    )
    for file in "${files[@]}"; do
        [[ -f "$file" ]] && sed -i "s|/home/matte|$escaped_home|g" "$file"
    done
}

finish_install() {
    chmod +x "$HOME/.local/bin"/orbitos-* 2>/dev/null || true
    chmod +x "$HOME/.config/quickshell/scripts"/*.sh "$HOME/.config/quickshell/scripts"/*.py 2>/dev/null || true
    mkdir -p "$HOME/.local/state/orbitos" "$HOME/.config/orbitos"
    command -v update-desktop-database >/dev/null 2>&1 && \
        update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
}

while (($#)); do
    case "$1" in
        -y|--yes) ASSUME_YES=true ;;
        --no-packages) INSTALL_PACKAGES=false ;;
        --dry-run) DRY_RUN=true ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

animate_title

if [[ ! -d "$REPO_DIR/.config/hypr" ]]; then
    say "  Error: run this script from the OrbitOS repository."
    exit 1
fi

if [[ -r /etc/os-release ]] && ! grep -q '^ID=arch$' /etc/os-release; then
    say "  ${DIM}Warning: OrbitOS is designed for Arch Linux.${RESET}"
fi

if [[ "$INSTALL_PACKAGES" == true ]] && ask "  Install the software used by OrbitOS?" yes; then
    if [[ "$DRY_RUN" == false ]]; then
        say "  Administrator access is needed to install system packages."
        sudo -v
    fi
    run_step "Installing Arch packages" install_repo_packages
    if ! run_step "Installing AUR integrations" install_aur_packages; then
        say "    ${DIM}wlogout, clipse, and the overview need yay or paru; continuing without them.${RESET}"
    fi
    run_step "Enabling networking and Bluetooth" enable_services
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

if [[ "$ASSUME_YES" == false ]] && ask "  Apply the included HDMI/eDP monitor layout?" no; then
    INSTALL_MONITORS=true
else
    INSTALL_MONITORS=false
fi

say
if [[ "$CREATE_BACKUP" == true ]]; then
    run_step "Backing up existing dotfiles" backup_existing
    if [[ "$DRY_RUN" == true ]]; then
        say "    ${DIM}Existing managed files would be copied to $BACKUP_DIR.${RESET}"
    elif [[ -d "$BACKUP_DIR" ]]; then
        say "    ${DIM}$BACKUP_DIR${RESET}"
    else
        say "    ${DIM}No existing managed dotfiles were found.${RESET}"
    fi
fi

run_step "Installing OrbitOS dotfiles" install_dotfiles
run_step "Adapting paths for $USER" rewrite_home_paths
run_step "Finishing desktop integration" finish_install

if [[ "$DRY_RUN" == false ]] && command -v hyprctl >/dev/null 2>&1 && [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    hyprctl reload >/dev/null 2>&1 || true
fi

say
if [[ "$DRY_RUN" == true ]]; then
    say "  ${BOLD}Dry run complete. No changes were made.${RESET}"
else
    say "  ${BOLD}OrbitOS installed.${RESET}"
    if [[ "$INSTALL_MONITORS" == false ]]; then
        say "  Your existing monitor layout was preserved."
    fi
    say "  Log out and back in to start every desktop component."
fi
say
