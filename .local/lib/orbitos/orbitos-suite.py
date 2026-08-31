#!/usr/bin/env python3
"""Native OrbitOS control suite for Arch Linux and Hyprland."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402


PAGE = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in {"launcher", "game", "settings"} else "launcher"
APP_IDS = {
    "launcher": "io.github.dsksnkz.OrbitOS.Launcher",
    "game": "io.github.dsksnkz.OrbitOS.GameAccelerator",
    "settings": "io.github.dsksnkz.OrbitOS.Settings",
}
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "orbitos"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "orbitos"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
BOOST_FILE = STATE_DIR / "game-boost.json"
QS_SCRIPTS = Path.home() / ".config/quickshell/scripts"

DEFAULTS: dict[str, object] = {
    "animations": True,
    "blur": True,
    "rounding": 3,
    "gaps_in": 4,
    "gaps_out": 6,
    "animation_speed": 100,
    "direct_scanout": True,
}


def run(args: list[str], timeout: float = 5, capture: bool = True) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            args,
            check=False,
            text=True,
            capture_output=capture,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def output(args: list[str], fallback: str = "") -> str:
    result = run(args)
    return result.stdout.strip() if result and result.stdout else fallback


def detached(args: list[str]) -> None:
    try:
        subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def load_json(path: Path, fallback: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else fallback.copy()
    except (OSError, ValueError):
        return fallback.copy()


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def hypr_keyword(name: str, value: object) -> None:
    run(["hyprctl", "keyword", name, str(value)], timeout=3)


def apply_saved_settings() -> int:
    settings = {**DEFAULTS, **load_json(SETTINGS_FILE, DEFAULTS)}
    hypr_keyword("animations:enabled", "true" if settings["animations"] else "false")
    hypr_keyword("decoration:blur:enabled", "true" if settings["blur"] else "false")
    hypr_keyword("decoration:rounding", int(settings["rounding"]))
    hypr_keyword("general:gaps_in", int(settings["gaps_in"]))
    hypr_keyword("general:gaps_out", int(settings["gaps_out"]))
    hypr_keyword("render:direct_scanout", "true" if settings["direct_scanout"] else "false")
    speed_script = QS_SCRIPTS / "animation-speed.py"
    if speed_script.exists():
        run([str(speed_script), "set", str(int(settings["animation_speed"]))], timeout=8)
    return 0


def dnd_enabled() -> bool:
    return output(["swaync-client", "--skip-wait", "-D"], "false").lower() == "true"


def set_dnd(enabled: bool) -> None:
    if dnd_enabled() != enabled:
        run(["swaync-client", "--skip-wait", "-d"])


def caffeine_enabled() -> bool:
    return run(["pgrep", "-x", "hypridle"]) is None or not bool(output(["pgrep", "-x", "hypridle"]))


def set_caffeine(enabled: bool) -> None:
    if caffeine_enabled() == enabled:
        return
    script = QS_SCRIPTS / "caffeine.sh"
    if script.exists():
        run([str(script)], timeout=8)


def set_power_profile(profile: str) -> None:
    if shutil.which("powerprofilesctl"):
        run(["powerprofilesctl", "set", profile], timeout=12)


def async_call(work: Callable[[], object], done: Callable[[object], None] | None = None) -> None:
    def worker() -> None:
        try:
            result: object = work()
        except Exception as error:  # defensive boundary for external system tools
            result = error
        if done:
            GLib.idle_add(done, result)

    threading.Thread(target=worker, daemon=True).start()


class OrbitGauge(Gtk.DrawingArea):
    def __init__(self) -> None:
        super().__init__()
        self.value = 0.0
        self.phase = 0.0
        self.set_size_request(214, 214)
        self.set_draw_func(self._draw)
        self.add_tick_callback(self._tick)

    def set_value(self, value: float) -> None:
        self.value = max(0.0, min(100.0, value))
        self.queue_draw()

    def _tick(self, _widget, frame_clock) -> bool:
        self.phase = frame_clock.get_frame_time() / 1_000_000 * (0.25 + self.value / 130)
        self.queue_draw()
        return True

    def _draw(self, _area, context, width: int, height: int) -> None:
        cx, cy = width / 2, height / 2
        radius = min(width, height) * 0.36
        context.set_line_width(1)
        for offset, alpha in ((0, 0.32), (18, 0.18), (-18, 0.15)):
            context.set_source_rgba(0.85, 0.85, 0.85, alpha)
            context.arc(cx, cy, radius + offset, 0, math.tau)
            context.stroke()
        for index in range(3):
            angle = self.phase * (1 if index != 1 else -0.7) + index * math.tau / 3
            orbit = radius + (index - 1) * 18
            x, y = cx + math.cos(angle) * orbit, cy + math.sin(angle) * orbit
            context.set_source_rgba(0.96, 0.96, 0.96, 0.95 - index * 0.18)
            context.arc(x, y, 4 - index * 0.7, 0, math.tau)
            context.fill()
        context.set_source_rgb(0.96, 0.96, 0.96)
        context.select_font_face("monospace", 0, 1)
        context.set_font_size(29)
        text = f"{round(self.value)}%"
        extents = context.text_extents(text)
        context.move_to(cx - extents.width / 2, cy + 4)
        context.show_text(text)
        context.set_source_rgb(0.48, 0.48, 0.48)
        context.set_font_size(10)
        label = "FAN / THERMAL"
        extents = context.text_extents(label)
        context.move_to(cx - extents.width / 2, cy + 26)
        context.show_text(label)


class MetricCard(Gtk.Box):
    def __init__(self, title: str, icon: str) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add_css_class("metric-card")
        self.set_hexpand(True)
        top = Gtk.Box(spacing=8)
        symbol = Gtk.Label(label=icon)
        symbol.add_css_class("metric-icon")
        title_label = Gtk.Label(label=title.upper(), xalign=0)
        title_label.add_css_class("eyebrow")
        top.append(symbol)
        top.append(title_label)
        self.value_label = Gtk.Label(label="—", xalign=0)
        self.value_label.add_css_class("metric-value")
        self.detail_label = Gtk.Label(label="Collecting telemetry", xalign=0)
        self.detail_label.add_css_class("dim-label")
        self.detail_label.set_ellipsize(3)
        self.progress = Gtk.ProgressBar()
        self.append(top)
        self.append(self.value_label)
        self.append(self.detail_label)
        self.append(self.progress)

    def update(self, value: str, detail: str, fraction: float) -> None:
        self.value_label.set_text(value)
        self.detail_label.set_text(detail)
        self.progress.set_fraction(max(0.0, min(1.0, fraction)))


class Telemetry:
    def __init__(self) -> None:
        self.previous_cpu = self._cpu_ticks()

    @staticmethod
    def _cpu_ticks() -> tuple[int, int]:
        try:
            fields = [int(value) for value in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
            return sum(fields), fields[3] + (fields[4] if len(fields) > 4 else 0)
        except (OSError, ValueError, IndexError):
            return 1, 1

    def cpu_percent(self) -> int:
        now_total, now_idle = self._cpu_ticks()
        old_total, old_idle = self.previous_cpu
        self.previous_cpu = now_total, now_idle
        delta = max(1, now_total - old_total)
        return round((delta - (now_idle - old_idle)) * 100 / delta)

    @staticmethod
    def memory() -> tuple[int, float, float, float]:
        values: dict[str, int] = {}
        try:
            for line in Path("/proc/meminfo").read_text().splitlines():
                key, raw = line.split(":", 1)
                values[key] = int(raw.strip().split()[0])
        except (OSError, ValueError):
            return 0, 0, 0, 0
        total = values.get("MemTotal", 1) / 1_048_576
        available = values.get("MemAvailable", 0) / 1_048_576
        cached = (values.get("Cached", 0) + values.get("SReclaimable", 0)) / 1_048_576
        used = max(0.0, total - available)
        return round(used * 100 / total), used, total, cached

    @staticmethod
    def temperatures() -> tuple[int, int]:
        values: list[float] = []
        fans: list[int] = []
        for path in Path("/sys/class/hwmon").glob("hwmon*/temp*_input"):
            try:
                value = float(path.read_text().strip()) / 1000
                if 5 <= value <= 120:
                    values.append(value)
            except (OSError, ValueError):
                pass
        for path in Path("/sys/class/hwmon").glob("hwmon*/fan*_input"):
            try:
                value = int(path.read_text().strip())
                if value > 0:
                    fans.append(value)
            except (OSError, ValueError):
                pass
        return round(max(values)) if values else 0, max(fans) if fans else 0

    @staticmethod
    def gpu() -> dict[str, object]:
        query = "name,utilization.gpu,memory.used,memory.total,temperature.gpu,fan.speed,power.draw"
        raw = output(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"], "")
        if not raw:
            return {"name": "GPU unavailable", "load": 0, "used": 0, "total": 0, "temp": 0, "fan": 0, "power": 0}
        fields = [item.strip() for item in raw.splitlines()[0].split(",")]

        def number(index: int) -> float:
            try:
                return float(fields[index]) if fields[index] not in {"[N/A]", "N/A"} else 0
            except (IndexError, ValueError):
                return 0

        return {
            "name": fields[0] if fields else "NVIDIA GPU",
            "load": round(number(1)),
            "used": number(2) / 1024,
            "total": number(3) / 1024,
            "temp": round(number(4)),
            "fan": round(number(5)),
            "power": number(6),
        }

    def snapshot(self) -> dict[str, object]:
        cpu = self.cpu_percent()
        memory, used, total, cached = self.memory()
        system_temp, fan_rpm = self.temperatures()
        gpu = self.gpu()
        temperature = max(system_temp, int(gpu["temp"]))
        if int(gpu["fan"]):
            fan = int(gpu["fan"])
        elif fan_rpm:
            fan = min(100, round(fan_rpm / 50))
        else:
            fan = min(100, max(12, temperature))
        readiness = max(0, min(100, 100 - max(0, temperature - 60) * 2 - max(0, cpu - 85)))
        return {
            "cpu": cpu,
            "memory": memory,
            "used": used,
            "total": total,
            "cached": cached,
            "system_temp": system_temp,
            "fan": fan,
            "fan_rpm": fan_rpm,
            "gpu": gpu,
            "readiness": readiness,
        }


class OrbitWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, page: str) -> None:
        super().__init__(application=application, title="OrbitOS")
        self.page = page
        self.settings = {**DEFAULTS, **load_json(SETTINGS_FILE, DEFAULTS)}
        self.telemetry = Telemetry()
        self.telemetry_busy = False
        self.speed_timeout = 0
        self.set_default_size(1080, 760)
        self.set_size_request(760, 560)

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main)

        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="OrbitOS", subtitle="UX first, then UI"))
        home = Gtk.Button.new_from_icon_name("go-home-symbolic")
        home.set_tooltip_text("Open the OrbitOS home screen")
        home.connect("clicked", lambda *_: self.quick_call("toggleHome"))
        header.pack_start(home)
        controls = Gtk.Button.new_from_icon_name("view-grid-symbolic")
        controls.set_tooltip_text("Open desktop controls")
        controls.connect("clicked", lambda *_: self.quick_call("toggleControl"))
        header.pack_end(controls)
        main.append(header)

        body = Gtk.Box()
        body.set_vexpand(True)
        main.append(body)
        sidebar = self.build_sidebar()
        body.append(sidebar)
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        body.append(separator)
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT, transition_duration=240)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.add_named(self.build_launcher(), "launcher")
        self.stack.add_named(self.build_game(), "game")
        self.stack.add_named(self.build_settings(), "settings")
        body.append(self.stack)
        self.show_page(page)

    def toast(self, message: str) -> None:
        self.toast_overlay.add_toast(Adw.Toast(title=message, timeout=3))

    def quick_call(self, method: str) -> None:
        detached(["quickshell", "ipc", "call", "orbitos", method])

    def build_sidebar(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("sidebar")
        brand = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        brand.set_margin_bottom(18)
        title = Gtk.Label(label="ORBITOS", xalign=0)
        title.add_css_class("brand")
        subtitle = Gtk.Label(label="CONTROL SURFACE", xalign=0)
        subtitle.add_css_class("eyebrow")
        brand.append(title)
        brand.append(subtitle)
        box.append(brand)
        self.nav_buttons: dict[str, Gtk.Button] = {}
        for name, label, icon in (
            ("launcher", "Orbit Launcher", "view-app-grid-symbolic"),
            ("game", "Game Accelerator", "applications-games-symbolic"),
            ("settings", "Settings", "preferences-system-symbolic"),
        ):
            button = Gtk.Button()
            button.set_child(self.button_content(icon, label))
            button.add_css_class("nav-button")
            button.connect("clicked", lambda _button, target=name: self.show_page(target))
            box.append(button)
            self.nav_buttons[name] = button
        spacer = Gtk.Box(vexpand=True)
        box.append(spacer)
        version = Gtk.Label(label="ORBITOS  /  ECOSYSTEM", xalign=0)
        version.add_css_class("eyebrow")
        box.append(version)
        return box

    @staticmethod
    def button_content(icon: str, label: str) -> Gtk.Widget:
        row = Gtk.Box(spacing=10)
        image = Gtk.Image.new_from_icon_name(icon)
        image.set_pixel_size(18)
        text = Gtk.Label(label=label, xalign=0)
        row.append(image)
        row.append(text)
        return row

    def show_page(self, page: str) -> None:
        self.page = page
        self.stack.set_visible_child_name(page)
        for name, button in self.nav_buttons.items():
            if name == page:
                button.add_css_class("active")
            else:
                button.remove_css_class("active")
        if page == "game":
            self.refresh_telemetry()

    def page_shell(self, eyebrow: str, title: str, description: str) -> tuple[Gtk.ScrolledWindow, Gtk.Box]:
        scroll = Gtk.ScrolledWindow()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        content.add_css_class("page")
        over = Gtk.Label(label=eyebrow, xalign=0)
        over.add_css_class("eyebrow")
        heading = Gtk.Label(label=title, xalign=0)
        heading.add_css_class("page-title")
        heading.set_wrap(True)
        sub = Gtk.Label(label=description, xalign=0)
        sub.add_css_class("page-description")
        sub.set_wrap(True)
        content.append(over)
        content.append(heading)
        content.append(sub)
        scroll.set_child(content)
        return scroll, content

    def build_launcher(self) -> Gtk.Widget:
        scroll, content = self.page_shell(
            "ORBIT LAUNCHER", "Your OrbitOS, in one place.",
            "Launch system surfaces and native OrbitOS apps without hunting through menus.",
        )
        grid = Gtk.FlowBox()
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.set_max_children_per_line(3)
        grid.set_min_children_per_line(2)
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)
        actions = (
            ("Game Accelerator", "Live telemetry and reversible game boost", "applications-games-symbolic", lambda: self.show_page("game")),
            ("Settings", "Shape motion, layout and desktop behavior", "preferences-system-symbolic", lambda: self.show_page("settings")),
            ("Orbit Apps", "View and uninstall installed applications", "system-software-install-symbolic", lambda: detached(["orbitos-apps"])),
            ("Home", "Return to your full-screen home surface", "go-home-symbolic", lambda: self.quick_call("toggleHome")),
            ("Control Center", "Connectivity, sound, power and utilities", "view-grid-symbolic", lambda: self.quick_call("toggleControl")),
            ("Time Hub", "Calendar, alarms, timers and focus", "org.gnome.Settings-time-symbolic", lambda: self.quick_call("toggleTime")),
            ("System Monitor", "CPU, GPU, memory and process detail", "utilities-system-monitor-symbolic", lambda: detached(["missioncenter"])),
            ("Power", "Lock, log out, suspend or shut down", "system-shutdown-symbolic", lambda: detached(["wlogout"])),
            ("App Search", "Search every installed application", "system-search-symbolic", lambda: detached(["rofi", "-show", "drun"])),
        )
        for title, detail, icon, callback in actions:
            button = Gtk.Button()
            button.add_css_class("launch-card")
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            image = Gtk.Image.new_from_icon_name(icon)
            image.set_pixel_size(28)
            image.set_halign(Gtk.Align.START)
            name = Gtk.Label(label=title, xalign=0)
            name.add_css_class("card-title")
            desc = Gtk.Label(label=detail, xalign=0)
            desc.add_css_class("dim-label")
            desc.set_wrap(True)
            desc.set_max_width_chars(28)
            card.append(image)
            card.append(name)
            card.append(desc)
            button.set_child(card)
            button.connect("clicked", lambda _button, action=callback: action())
            grid.insert(button, -1)
        content.append(grid)
        hint = Adw.Banner(title="Tip: Super+Esc opens Home, and Super+I opens Settings.")
        hint.set_revealed(True)
        content.append(hint)
        return scroll

    def build_game(self) -> Gtk.Widget:
        scroll, content = self.page_shell(
            "GAME ACCELERATOR", "Performance, without the mystery.",
            "See what your hardware is doing, engage a reversible boost, and reclaim cache only when you choose.",
        )
        hero = Gtk.Box(spacing=22)
        hero.add_css_class("hero-card")
        self.fan_gauge = OrbitGauge()
        hero.append(self.fan_gauge)
        summary = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        summary.set_hexpand(True)
        self.readiness_label = Gtk.Label(label="Measuring system readiness…", xalign=0)
        self.readiness_label.add_css_class("section-title")
        self.readiness_detail = Gtk.Label(label="Thermals, load and memory pressure", xalign=0)
        self.readiness_detail.add_css_class("dim-label")
        self.readiness_detail.set_wrap(True)
        self.boost_button = Gtk.Button(label="Engage Boost")
        self.boost_button.add_css_class("suggested-action")
        self.boost_button.add_css_class("pill")
        self.boost_button.set_halign(Gtk.Align.START)
        self.boost_button.connect("clicked", self.toggle_boost)
        self.boost_status = Gtk.Label(label="Boost is idle", xalign=0)
        self.boost_status.add_css_class("eyebrow")
        summary.append(self.readiness_label)
        summary.append(self.readiness_detail)
        summary.append(self.boost_button)
        summary.append(self.boost_status)
        hero.append(summary)
        content.append(hero)

        metrics = Gtk.Box(spacing=12, homogeneous=True)
        self.cpu_card = MetricCard("CPU", "")
        self.gpu_card = MetricCard("GPU", "󰢮")
        self.ram_card = MetricCard("Memory", "")
        self.temp_card = MetricCard("Thermal", "󰔏")
        for card in (self.cpu_card, self.gpu_card, self.ram_card, self.temp_card):
            metrics.append(card)
        content.append(metrics)

        actions = Adw.PreferencesGroup(title="Session actions", description="Every performance change is visible and reversible.")
        steam = Adw.ActionRow(title="Open Steam Library", subtitle="Launch a game after engaging Boost")
        steam.add_prefix(Gtk.Image.new_from_icon_name("applications-games-symbolic"))
        steam.set_activatable(True)
        steam.connect("activated", lambda *_: detached(["steam", "steam://open/games"] if shutil.which("steam") else ["rofi", "-show", "drun"]))
        actions.add(steam)
        monitor = Adw.ActionRow(title="Detailed system monitor", subtitle="Inspect processes, disks and network activity")
        monitor.add_prefix(Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic"))
        monitor.set_activatable(True)
        monitor.connect("activated", lambda *_: detached(["missioncenter"]))
        actions.add(monitor)
        reclaim = Adw.ActionRow(title="Reclaim filesystem cache", subtitle="Optional · temporary · requires administrator approval")
        reclaim.add_prefix(Gtk.Image.new_from_icon_name("edit-clear-all-symbolic"))
        reclaim.set_activatable(True)
        reclaim.connect("activated", self.confirm_reclaim)
        actions.add(reclaim)
        self.cache_row = Adw.ActionRow(title="Reclaimable cache", subtitle="Calculating…")
        self.cache_row.add_prefix(Gtk.Image.new_from_icon_name("drive-harddisk-symbolic"))
        actions.add(self.cache_row)
        content.append(actions)

        explanation = Adw.Banner(title="Linux uses spare RAM as a fast cache. Reclaiming it can free the number shown, but may briefly make loading slower.")
        explanation.set_revealed(True)
        content.append(explanation)
        self.update_boost_ui()
        GLib.timeout_add(1500, self.telemetry_timer)
        return scroll

    def telemetry_timer(self) -> bool:
        if self.page == "game":
            self.refresh_telemetry()
        return GLib.SOURCE_CONTINUE

    def refresh_telemetry(self) -> None:
        if self.telemetry_busy:
            return
        self.telemetry_busy = True
        async_call(self.telemetry.snapshot, self.apply_telemetry)

    def apply_telemetry(self, snapshot: object) -> bool:
        self.telemetry_busy = False
        if isinstance(snapshot, Exception) or not isinstance(snapshot, dict):
            self.readiness_label.set_text("Telemetry temporarily unavailable")
            return GLib.SOURCE_REMOVE
        gpu = snapshot["gpu"]
        self.cpu_card.update(f"{snapshot['cpu']}%", "Whole-system utilization", snapshot["cpu"] / 100)
        self.gpu_card.update(f"{gpu['load']}%", f"{gpu['name']} · {gpu['power']:.0f} W", gpu["load"] / 100)
        self.ram_card.update(f"{snapshot['memory']}%", f"{snapshot['used']:.1f} / {snapshot['total']:.1f} GiB", snapshot["memory"] / 100)
        thermal = max(snapshot["system_temp"], gpu["temp"])
        self.temp_card.update(f"{thermal}°C" if thermal else "—", f"GPU {gpu['temp']}° · CPU/system {snapshot['system_temp']}°", thermal / 100 if thermal else 0)
        self.fan_gauge.set_value(snapshot["fan"])
        readiness = snapshot["readiness"]
        state = "Ready to play" if readiness >= 80 else "System under load" if readiness >= 55 else "Cool down recommended"
        self.readiness_label.set_text(f"{state}  ·  {readiness}/100")
        fan_detail = f"Fan {snapshot['fan_rpm']} RPM" if snapshot["fan_rpm"] else (f"GPU fan {gpu['fan']}%" if gpu["fan"] else "Automatic fan control")
        self.readiness_detail.set_text(f"{fan_detail} · GameMode {'available' if shutil.which('gamemoderun') else 'not installed'}")
        self.cache_row.set_subtitle(f"Approximately {snapshot['cached']:.1f} GiB is currently used for fast file access")
        return GLib.SOURCE_REMOVE

    def boost_active(self) -> bool:
        return bool(load_json(BOOST_FILE, {}).get("active", False))

    def update_boost_ui(self) -> None:
        active = self.boost_active()
        self.boost_button.set_label("Restore Normal Mode" if active else "Engage Boost")
        if active:
            self.boost_button.remove_css_class("suggested-action")
            self.boost_status.set_text("PERFORMANCE · DND · CAFFEINE ACTIVE")
        else:
            self.boost_button.add_css_class("suggested-action")
            self.boost_status.set_text("Boost is idle")

    def toggle_boost(self, _button) -> None:
        self.boost_button.set_sensitive(False)
        work = self.restore_boost if self.boost_active() else self.engage_boost
        async_call(work, self.boost_finished)

    def engage_boost(self) -> str:
        previous = {
            "active": True,
            "power_profile": output(["powerprofilesctl", "get"], "balanced"),
            "dnd": dnd_enabled(),
            "caffeine": caffeine_enabled(),
            "started": int(time.time()),
        }
        save_json(BOOST_FILE, previous)
        set_power_profile("performance")
        set_dnd(True)
        set_caffeine(True)
        run(["systemctl", "--user", "start", "gamemoded.service"], timeout=8)
        return "Boost engaged — previous desktop state was saved"

    def restore_boost(self) -> str:
        previous = load_json(BOOST_FILE, {})
        set_power_profile(str(previous.get("power_profile", "balanced")))
        set_dnd(bool(previous.get("dnd", False)))
        set_caffeine(bool(previous.get("caffeine", False)))
        save_json(BOOST_FILE, {"active": False})
        return "Normal desktop state restored"

    def boost_finished(self, result: object) -> bool:
        self.boost_button.set_sensitive(True)
        self.update_boost_ui()
        self.toast(str(result))
        return GLib.SOURCE_REMOVE

    def confirm_reclaim(self, *_args) -> None:
        dialog = Adw.AlertDialog(
            heading="Reclaim filesystem cache?",
            body="OrbitOS will sync pending writes, then ask for administrator approval before releasing Linux file caches. This is temporary and normally unnecessary.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("reclaim", "Reclaim Cache")
        dialog.set_response_appearance("reclaim", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self.reclaim_response)
        dialog.present(self)

    def reclaim_response(self, _dialog, response: str) -> None:
        if response != "reclaim":
            return
        if not shutil.which("pkexec"):
            self.toast("polkit is required for cache reclaim")
            return
        self.toast("Waiting for administrator approval…")

        def reclaim() -> str:
            result = run(["pkexec", "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], timeout=90)
            return "Filesystem cache reclaimed" if result and result.returncode == 0 else "Cache reclaim cancelled or unavailable"

        async_call(reclaim, lambda message: (self.toast(str(message)), self.refresh_telemetry(), GLib.SOURCE_REMOVE)[-1])

    def build_settings(self) -> Gtk.Widget:
        scroll, content = self.page_shell(
            "SETTINGS", "Make OrbitOS feel like yours.",
            "Useful controls are grouped by intent, with immediate feedback and persistent desktop behavior.",
        )
        experience = Adw.PreferencesGroup(title="Experience", description="Motion and visual rhythm")
        self.animations_row = Adw.SwitchRow(title="Animations", subtitle="Smooth workspace, window and layer transitions")
        self.animations_row.set_active(bool(self.settings["animations"]))
        self.animations_row.connect("notify::active", lambda row, _param: self.setting_bool("animations", row.get_active(), "animations:enabled"))
        experience.add(self.animations_row)
        self.blur_row = Adw.SwitchRow(title="Background blur", subtitle="Separate floating surfaces from the desktop")
        self.blur_row.set_active(bool(self.settings["blur"]))
        self.blur_row.connect("notify::active", lambda row, _param: self.setting_bool("blur", row.get_active(), "decoration:blur:enabled"))
        experience.add(self.blur_row)
        speed = Adw.ActionRow(title="Animation speed", subtitle="Calm 50%  ·  balanced 100%  ·  swift 180%")
        self.speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 50, 180, 5)
        self.speed_scale.set_value(float(self.settings["animation_speed"]))
        self.speed_scale.set_size_request(260, -1)
        self.speed_scale.set_valign(Gtk.Align.CENTER)
        self.speed_scale.set_draw_value(True)
        self.speed_scale.connect("value-changed", self.speed_changed)
        speed.add_suffix(self.speed_scale)
        experience.add(speed)
        content.append(experience)

        layout = Adw.PreferencesGroup(title="Desktop geometry", description="Small corners and deliberate spacing are the OrbitOS default")
        for key, title, low, high in (
            ("rounding", "Corner radius", 0, 16),
            ("gaps_in", "Inner gaps", 0, 20),
            ("gaps_out", "Outer gaps", 0, 24),
        ):
            row = Adw.ActionRow(title=title)
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, low, high, 1)
            scale.set_value(float(self.settings[key]))
            scale.set_size_request(230, -1)
            scale.set_draw_value(True)
            scale.connect("value-changed", lambda widget, setting=key: self.geometry_changed(setting, round(widget.get_value())))
            row.add_suffix(scale)
            layout.add(row)
        content.append(layout)

        desktop = Adw.PreferencesGroup(title="Desktop surfaces", description="Fast routes to the parts of OrbitOS you use most")
        for title, subtitle, icon, callback in (
            ("Home screen", "Open the full-screen place you return to", "go-home-symbolic", lambda: self.quick_call("toggleHome")),
            ("Top bar", "Show or hide the orbital rail", "view-more-horizontal-symbolic", lambda: detached([str(QS_SCRIPTS / "bar-toggle.sh")])),
            ("Control Center", "Connectivity, sound, power and quick tools", "view-grid-symbolic", lambda: self.quick_call("toggleControl")),
            ("Notifications", "Open notification history and quiet controls", "preferences-system-notifications-symbolic", lambda: detached(["swaync-client", "--toggle-panel"])),
        ):
            row = Adw.ActionRow(title=title, subtitle=subtitle)
            row.add_prefix(Gtk.Image.new_from_icon_name(icon))
            row.set_activatable(True)
            row.connect("activated", lambda _row, action=callback: action())
            desktop.add(row)
        content.append(desktop)

        performance = Adw.PreferencesGroup(title="Power and performance", description="Choose a system policy, or let Game Accelerator coordinate a session")
        profile = Adw.ActionRow(title="Power profile", subtitle="Changes the system power policy")
        profiles = ["power-saver", "balanced", "performance"]
        dropdown = Gtk.DropDown.new_from_strings(profiles)
        current = output(["powerprofilesctl", "get"], "balanced")
        dropdown.set_selected(profiles.index(current) if current in profiles else 1)
        dropdown.connect("notify::selected", lambda widget, _param: self.profile_changed(profiles[widget.get_selected()]))
        profile.add_suffix(dropdown)
        performance.add(profile)
        direct = Adw.SwitchRow(title="Direct scanout", subtitle="Reduce compositor overhead for suitable fullscreen games")
        direct.set_active(bool(self.settings["direct_scanout"]))
        direct.connect("notify::active", lambda row, _param: self.setting_bool("direct_scanout", row.get_active(), "render:direct_scanout"))
        performance.add(direct)
        game = Adw.ActionRow(title="Game Accelerator", subtitle="Telemetry, Boost sessions and memory tools")
        game.add_prefix(Gtk.Image.new_from_icon_name("applications-games-symbolic"))
        game.set_activatable(True)
        game.connect("activated", lambda *_: self.show_page("game"))
        performance.add(game)
        content.append(performance)

        system = Adw.PreferencesGroup(title="System tools")
        for title, subtitle, icon, command in (
            ("Installed apps", "Review and uninstall software", "system-software-install-symbolic", ["orbitos-apps"]),
            ("Audio", "Output, input and application volume", "audio-volume-high-symbolic", ["pavucontrol"]),
            ("Network", "Saved Wi-Fi and wired connections", "network-wireless-symbolic", ["nm-connection-editor"]),
            ("System monitor", "Processes and hardware resources", "utilities-system-monitor-symbolic", ["missioncenter"]),
            ("Power menu", "Lock, suspend, log out or shut down", "system-shutdown-symbolic", ["wlogout"]),
        ):
            row = Adw.ActionRow(title=title, subtitle=subtitle)
            row.add_prefix(Gtk.Image.new_from_icon_name(icon))
            row.set_activatable(True)
            row.connect("activated", lambda _row, args=command: detached(args))
            system.add(row)
        content.append(system)

        about = Adw.PreferencesGroup(title="About")
        identity = Adw.ActionRow(title="OrbitOS", subtitle="A UX-first desktop ecosystem for Arch Linux and Hyprland")
        identity.add_prefix(Gtk.Image.new_from_icon_name("starred-symbolic"))
        about.add(identity)
        content.append(about)
        return scroll

    def persist_settings(self) -> None:
        save_json(SETTINGS_FILE, self.settings)

    def setting_bool(self, key: str, value: bool, keyword: str) -> None:
        self.settings[key] = value
        self.persist_settings()
        hypr_keyword(keyword, "true" if value else "false")
        self.toast(f"{key.replace('_', ' ').title()} {'enabled' if value else 'disabled'}")

    def geometry_changed(self, key: str, value: int) -> None:
        self.settings[key] = value
        self.persist_settings()
        keyword = {"rounding": "decoration:rounding", "gaps_in": "general:gaps_in", "gaps_out": "general:gaps_out"}[key]
        hypr_keyword(keyword, value)

    def speed_changed(self, scale: Gtk.Scale) -> None:
        self.settings["animation_speed"] = round(scale.get_value())
        self.persist_settings()
        if self.speed_timeout:
            GLib.source_remove(self.speed_timeout)
        self.speed_timeout = GLib.timeout_add(180, self.apply_speed)

    def apply_speed(self) -> bool:
        self.speed_timeout = 0
        script = QS_SCRIPTS / "animation-speed.py"
        if script.exists():
            detached([str(script), "set", str(self.settings["animation_speed"])])
        return GLib.SOURCE_REMOVE

    def profile_changed(self, profile: str) -> None:
        async_call(lambda: (set_power_profile(profile), f"Power profile set to {profile}")[1], lambda message: (self.toast(str(message)), GLib.SOURCE_REMOVE)[1])


class OrbitApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_IDS[PAGE], flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self) -> None:
        window = self.props.active_window or OrbitWindow(self, PAGE)
        window.present()


def install_css() -> None:
    css = b"""
    window { background: #050505; color: #f4f4f4; }
    headerbar { background: #070707; border-bottom: 1px solid #292929; min-height: 46px; }
    button { border-radius: 4px; }
    .sidebar { min-width: 218px; padding: 22px 14px 16px 14px; background: #080808; }
    .brand { font-family: "JetBrainsMono Nerd Font"; font-size: 19px; font-weight: 800; letter-spacing: 2px; }
    .eyebrow { color: #858585; font-family: "JetBrainsMono Nerd Font"; font-size: 9px; font-weight: 700; letter-spacing: 1.4px; }
    .nav-button { min-height: 42px; padding: 0 12px; background: transparent; border: 1px solid transparent; color: #a8a8a8; }
    .nav-button:hover { background: #111111; border-color: #292929; color: #f4f4f4; }
    .nav-button.active { background: #f4f4f4; color: #050505; }
    .page { padding: 32px 36px 44px 36px; }
    .page-title { font-size: 30px; font-weight: 700; letter-spacing: -0.7px; }
    .page-description { color: #949494; font-size: 13px; margin-bottom: 8px; }
    .launch-card { min-width: 220px; min-height: 126px; padding: 18px; background: #0b0b0b; border: 1px solid #292929; }
    .launch-card:hover { background: #f4f4f4; color: #050505; border-color: #f4f4f4; }
    .card-title { font-size: 15px; font-weight: 700; }
    .hero-card { padding: 18px 24px; background: #080808; border: 1px solid #343434; border-radius: 4px; }
    .section-title { font-size: 22px; font-weight: 700; }
    .metric-card { padding: 15px; background: #0a0a0a; border: 1px solid #292929; border-radius: 4px; }
    .metric-icon { font-family: "JetBrainsMono Nerd Font"; font-size: 16px; }
    .metric-value { font-family: "JetBrainsMono Nerd Font"; font-size: 23px; font-weight: 800; }
    .dim-label { color: #858585; font-size: 11px; }
    progressbar trough { min-height: 3px; background: #202020; border-radius: 2px; }
    progressbar progress { min-height: 3px; background: #f4f4f4; border-radius: 2px; }
    preferencesgroup { margin-top: 4px; }
    .boxed-list, preferencesgroup > box > box { border-radius: 4px; }
    switch:checked { background: #f4f4f4; color: #050505; }
    scale highlight { background: #f4f4f4; }
    .pill { padding-left: 20px; padding-right: 20px; }
    banner { border-radius: 4px; }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def main() -> int:
    if "--apply" in sys.argv:
        return apply_saved_settings()
    Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    app = OrbitApplication()
    app.connect("startup", lambda _app: install_css())
    return app.run([sys.argv[0]])


if __name__ == "__main__":
    raise SystemExit(main())
