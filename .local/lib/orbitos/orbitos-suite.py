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
    "border_size": 1,
    "shadow": True,
    "motion_blur": True,
    "inactive_opacity": 94,
    "pointer_sensitivity": 0,
    "accel_profile": "flat",
    "natural_scroll": False,
    "left_handed": False,
    "scroll_factor": 100,
    "tap_to_click": True,
    "disable_while_typing": True,
    "clickfinger": False,
    "repeat_rate": 25,
    "repeat_delay": 600,
    "numlock": False,
    "vrr": False,
    "cursor_size": 15,
    "workspace_wraparound": True,
    "focus_follows_mouse": 1,
    "resize_on_border": False,
    "allow_tearing": False,
    "layout": "dwindle",
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


def lua_literal(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def hypr_eval(code: str) -> bool:
    result = run(["hyprctl", "eval", code], timeout=5)
    return bool(result and result.returncode == 0 and not result.stdout.lower().startswith("error"))


def hypr_keyword(name: str, value: object) -> bool:
    """Apply a config value through Hyprland's non-legacy Lua parser."""
    nested = lua_literal(value)
    for key in reversed(name.split(":")):
        nested = "{ " + key.replace("-", "_") + " = " + nested + " }"
    return hypr_eval(f"hl.config({nested})")


def hypr_option(name: str, fallback: object) -> object:
    try:
        data = json.loads(output(["hyprctl", "getoption", name, "-j"], "{}"))
    except ValueError:
        return fallback
    for key in ("bool", "int", "float", "str"):
        if key in data:
            return data[key]
    if "css" in data:
        try:
            return int(str(data["css"]).split()[0])
        except (ValueError, IndexError):
            pass
    return fallback


def live_settings() -> dict[str, object]:
    animation_state = STATE_DIR / "animation-speed"
    try:
        speed = int(animation_state.read_text().strip())
    except (OSError, ValueError):
        speed = 100
    return {
        "animations": bool(hypr_option("animations:enabled", True)),
        "blur": bool(hypr_option("decoration:blur:enabled", True)),
        "rounding": int(hypr_option("decoration:rounding", 3)),
        "gaps_in": int(hypr_option("general:gaps_in", 3)),
        "gaps_out": int(hypr_option("general:gaps_out", 6)),
        "animation_speed": speed,
        "direct_scanout": bool(hypr_option("render:direct_scanout", 1)),
        "border_size": int(hypr_option("general:border_size", 1)),
        "shadow": bool(hypr_option("decoration:shadow:enabled", True)),
        "motion_blur": bool(hypr_option("decoration:motion_blur:enabled", True)),
        "inactive_opacity": round(float(hypr_option("decoration:inactive_opacity", 0.94)) * 100),
        "pointer_sensitivity": round(float(hypr_option("input:sensitivity", 0.0)) * 10),
        "accel_profile": str(hypr_option("input:accel_profile", "flat")),
        "natural_scroll": bool(hypr_option("input:touchpad:natural_scroll", False)),
        "left_handed": bool(hypr_option("input:left_handed", False)),
        "scroll_factor": round(float(hypr_option("input:scroll_factor", 1.0)) * 100),
        "tap_to_click": bool(hypr_option("input:touchpad:tap-to-click", True)),
        "disable_while_typing": bool(hypr_option("input:touchpad:disable_while_typing", True)),
        "clickfinger": bool(hypr_option("input:touchpad:clickfinger_behavior", False)),
        "repeat_rate": int(hypr_option("input:repeat_rate", 25)),
        "repeat_delay": int(hypr_option("input:repeat_delay", 600)),
        "numlock": bool(hypr_option("input:numlock_by_default", False)),
        "vrr": bool(hypr_option("misc:vrr", 0)),
        "cursor_size": int(os.environ.get("HYPRCURSOR_SIZE", "15")),
        "workspace_wraparound": bool(hypr_option("animations:workspace_wraparound", True)),
        "focus_follows_mouse": int(hypr_option("input:follow_mouse", 1)),
        "resize_on_border": bool(hypr_option("general:resize_on_border", False)),
        "allow_tearing": bool(hypr_option("general:allow_tearing", False)),
        "layout": str(hypr_option("general:layout", "dwindle")),
    }


def apply_saved_settings() -> int:
    settings = load_json(SETTINGS_FILE, {})
    mappings = {
        "animations": ("animations:enabled", bool),
        "blur": ("decoration:blur:enabled", bool),
        "rounding": ("decoration:rounding", int),
        "gaps_in": ("general:gaps_in", int),
        "gaps_out": ("general:gaps_out", int),
        "direct_scanout": ("render:direct_scanout", bool),
        "border_size": ("general:border_size", int),
        "shadow": ("decoration:shadow:enabled", bool),
        "motion_blur": ("decoration:motion_blur:enabled", bool),
        "inactive_opacity": ("decoration:inactive_opacity", lambda value: int(value) / 100),
        "pointer_sensitivity": ("input:sensitivity", lambda value: int(value) / 10),
        "accel_profile": ("input:accel_profile", str),
        "natural_scroll": ("input:touchpad:natural_scroll", bool),
        "left_handed": ("input:left_handed", bool),
        "scroll_factor": ("input:scroll_factor", lambda value: int(value) / 100),
        "tap_to_click": ("input:touchpad:tap-to-click", bool),
        "disable_while_typing": ("input:touchpad:disable_while_typing", bool),
        "clickfinger": ("input:touchpad:clickfinger_behavior", bool),
        "repeat_rate": ("input:repeat_rate", int),
        "repeat_delay": ("input:repeat_delay", int),
        "numlock": ("input:numlock_by_default", bool),
        "vrr": ("misc:vrr", lambda value: 1 if value else 0),
        "kb_layout": ("input:kb_layout", str),
        "workspace_wraparound": ("animations:workspace_wraparound", bool),
        "focus_follows_mouse": ("input:follow_mouse", int),
        "resize_on_border": ("general:resize_on_border", bool),
        "allow_tearing": ("general:allow_tearing", bool),
        "layout": ("general:layout", str),
    }
    for key, (option, convert) in mappings.items():
        if key in settings:
            hypr_keyword(option, convert(settings[key]))
    speed_script = QS_SCRIPTS / "animation-speed.py"
    if speed_script.exists() and "animation_speed" in settings:
        run([str(speed_script), "set", str(int(settings["animation_speed"]))], timeout=8)
    monitor = settings.get("monitor")
    if isinstance(monitor, dict):
        connected = {item.get("name") for item in monitor_snapshot()}
        if monitor.get("output") in connected:
            apply_monitor(monitor)
    if "cursor_size" in settings:
        run(["hyprctl", "setcursor", os.environ.get("XCURSOR_THEME") or "breeze_cursors", str(int(settings["cursor_size"]))])
    return 0


def monitor_snapshot() -> list[dict]:
    try:
        value = json.loads(output(["hyprctl", "monitors", "-j"], "[]"))
        return value if isinstance(value, list) else []
    except ValueError:
        return []


def apply_monitor(config: dict) -> bool:
    required = {"output", "mode", "position", "scale", "transform"}
    if not required <= config.keys():
        return False
    command = (
        "hl.monitor({ output = " + lua_literal(config["output"])
        + ", mode = " + lua_literal(config["mode"])
        + ", position = " + lua_literal(config["position"])
        + ", scale = " + lua_literal(float(config["scale"]))
        + ", transform = " + lua_literal(int(config["transform"])) + " })"
    )
    return hypr_eval(command)


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
        self.settings = {**DEFAULTS, **live_settings(), **load_json(SETTINGS_FILE, {})}
        self.telemetry = Telemetry()
        self.telemetry_busy = False
        self.speed_timeout = 0
        self.setting_timeouts: dict[str, int] = {}
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
            "Display, input, sound, power and desktop behavior—live, persistent, and grouped by intent.",
        )

        diagnostics = output(["hyprctl", "configerrors"], "").strip()
        status = Adw.Banner(title="Hyprland configuration is healthy" if not diagnostics else "Hyprland reported configuration errors")
        status.set_revealed(True)
        content.append(status)

        experience = Adw.PreferencesGroup(title="Experience", description="Motion and visual rhythm")
        self.animations_row = Adw.SwitchRow(title="Animations", subtitle="Smooth workspace, window and layer transitions")
        self.animations_row.set_active(bool(self.settings["animations"]))
        self.animations_row.connect("notify::active", lambda row, _param: self.setting_bool("animations", row.get_active(), "animations:enabled"))
        experience.add(self.animations_row)
        self.blur_row = Adw.SwitchRow(title="Background blur", subtitle="Separate floating surfaces from the desktop")
        self.blur_row.set_active(bool(self.settings["blur"]))
        self.blur_row.connect("notify::active", lambda row, _param: self.setting_bool("blur", row.get_active(), "decoration:blur:enabled"))
        experience.add(self.blur_row)
        shadow = Adw.SwitchRow(title="Window shadows", subtitle="Give floating surfaces a subtle depth cue")
        shadow.set_active(bool(self.settings["shadow"]))
        shadow.connect("notify::active", lambda row, _param: self.setting_bool("shadow", row.get_active(), "decoration:shadow:enabled"))
        experience.add(shadow)
        motion_blur = Adw.SwitchRow(title="Motion blur", subtitle="OrbitOS compositor motion effect")
        motion_blur.set_active(bool(self.settings["motion_blur"]))
        motion_blur.connect("notify::active", lambda row, _param: self.setting_bool("motion_blur", row.get_active(), "decoration:motion_blur:enabled"))
        experience.add(motion_blur)
        speed = Adw.ActionRow(title="Animation speed", subtitle="Calm 50%  ·  balanced 100%  ·  swift 180%")
        self.speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 50, 180, 5)
        self.speed_scale.set_value(float(self.settings["animation_speed"]))
        self.speed_scale.set_size_request(260, -1)
        self.speed_scale.set_valign(Gtk.Align.CENTER)
        self.speed_scale.set_draw_value(True)
        self.speed_scale.connect("value-changed", self.speed_changed)
        speed.add_suffix(self.speed_scale)
        experience.add(speed)
        opacity = self.scale_row("Inactive-window opacity", "Keep focus clear without hiding context", 70, 100, 1, self.settings["inactive_opacity"])
        opacity[1].connect("value-changed", lambda scale: self.delayed_setting("inactive_opacity", round(scale.get_value()), "decoration:inactive_opacity", lambda value: value / 100))
        experience.add(opacity[0])
        content.append(experience)

        layout = Adw.PreferencesGroup(title="Desktop geometry", description="Small corners and deliberate spacing are the OrbitOS default")
        for key, title, subtitle, low, high, option in (
            ("rounding", "Corner radius", "Applies to tiled and floating windows", 0, 16, "decoration:rounding"),
            ("gaps_in", "Inner gaps", "Space between neighboring windows", 0, 20, "general:gaps_in"),
            ("gaps_out", "Outer gaps", "Space between windows and screen edges", 0, 24, "general:gaps_out"),
            ("border_size", "Border width", "Focused-window edge width", 0, 5, "general:border_size"),
        ):
            row, scale = self.scale_row(title, subtitle, low, high, 1, self.settings[key])
            scale.connect("value-changed", lambda widget, setting=key, target=option: self.delayed_setting(setting, round(widget.get_value()), target))
            layout.add(row)
        content.append(layout)

        windows = Adw.PreferencesGroup(title="Windows and workspaces", description="Focus, tiling and edge behavior")
        layout_row = Adw.ActionRow(title="Tiling layout", subtitle="Dwindle is compact; master keeps one primary window")
        layout_values = ["dwindle", "master"]
        tiling_dropdown = Gtk.DropDown.new_from_strings(["Dwindle", "Master"])
        tiling_dropdown.set_selected(layout_values.index(self.settings["layout"]) if self.settings["layout"] in layout_values else 0)
        tiling_dropdown.connect("notify::selected", lambda widget, _param: self.setting_value("layout", layout_values[widget.get_selected()], "general:layout"))
        layout_row.add_suffix(tiling_dropdown)
        windows.add(layout_row)
        focus_row = Adw.ActionRow(title="Focus follows pointer", subtitle="Choose how pointer movement changes keyboard focus")
        focus_values = [0, 1, 2, 3]
        focus_dropdown = Gtk.DropDown.new_from_strings(["Click to focus", "Follow pointer", "Loose follow", "Always follow"])
        focus_value = int(self.settings["focus_follows_mouse"])
        focus_dropdown.set_selected(focus_values.index(focus_value) if focus_value in focus_values else 1)
        focus_dropdown.connect("notify::selected", lambda widget, _param: self.setting_value("focus_follows_mouse", focus_values[widget.get_selected()], "input:follow_mouse"))
        focus_row.add_suffix(focus_dropdown)
        windows.add(focus_row)
        for key, title, subtitle, option in (
            ("workspace_wraparound", "Workspace wraparound", "Continue from the last workspace back to the first", "animations:workspace_wraparound"),
            ("resize_on_border", "Resize from window borders", "Drag a border or gap to resize tiled windows", "general:resize_on_border"),
            ("allow_tearing", "Allow tearing", "Lowest latency for explicitly configured games", "general:allow_tearing"),
        ):
            row = Adw.SwitchRow(title=title, subtitle=subtitle)
            row.set_active(bool(self.settings[key]))
            row.connect("notify::active", lambda widget, _param, setting=key, target=option: self.setting_bool(setting, widget.get_active(), target))
            windows.add(row)
        content.append(windows)

        displays = Adw.PreferencesGroup(title="Displays", description="Safe monitor changes automatically roll back after 12 seconds")
        self.monitors = monitor_snapshot()
        self.monitor = next((item for item in self.monitors if item.get("focused")), self.monitors[0] if self.monitors else None)
        if self.monitor:
            display_name = self.monitor.get("description") or self.monitor.get("name", "Display")
            display_info = Adw.ActionRow(
                title=display_name,
                subtitle=f"{self.monitor['width']}×{self.monitor['height']} · {self.monitor['refreshRate']:.0f} Hz · {self.monitor['name']}",
            )
            display_info.add_prefix(Gtk.Image.new_from_icon_name("video-display-symbolic"))
            displays.add(display_info)
            mode_row = Adw.ActionRow(title="Resolution and refresh rate", subtitle="Choose one of the monitor's advertised modes")
            self.monitor_modes = list(dict.fromkeys(self.monitor.get("availableModes", [])))
            self.mode_dropdown = Gtk.DropDown.new_from_strings(self.monitor_modes or ["preferred"])
            current_prefix = f"{self.monitor['width']}x{self.monitor['height']}@{self.monitor['refreshRate']:.2f}"
            current_index = next((i for i, mode in enumerate(self.monitor_modes) if mode.lower().replace("hz", "").startswith(current_prefix.lower())), 0)
            self.mode_dropdown.set_selected(current_index)
            mode_row.add_suffix(self.mode_dropdown)
            displays.add(mode_row)
            scale_row = Adw.ActionRow(title="Display scale", subtitle="Larger values make interface elements bigger")
            self.monitor_scales = ["1.00", "1.25", "1.50", "1.75", "2.00"]
            self.monitor_scale_dropdown = Gtk.DropDown.new_from_strings(self.monitor_scales)
            self.monitor_scale_dropdown.set_selected(min(range(len(self.monitor_scales)), key=lambda i: abs(float(self.monitor_scales[i]) - float(self.monitor.get("scale", 1)))))
            scale_row.add_suffix(self.monitor_scale_dropdown)
            displays.add(scale_row)
            orientation_row = Adw.ActionRow(title="Orientation", subtitle="Rotate the desktop output")
            self.monitor_transforms = [0, 1, 2, 3]
            self.orientation_dropdown = Gtk.DropDown.new_from_strings(["Landscape", "Portrait right", "Landscape flipped", "Portrait left"])
            transform = int(self.monitor.get("transform", 0))
            self.orientation_dropdown.set_selected(self.monitor_transforms.index(transform) if transform in self.monitor_transforms else 0)
            orientation_row.add_suffix(self.orientation_dropdown)
            displays.add(orientation_row)
            apply_display = Adw.ActionRow(title="Apply display configuration", subtitle="Preview the selected mode, scale and orientation")
            apply_button = Gtk.Button(label="Apply")
            apply_button.add_css_class("suggested-action")
            apply_button.set_valign(Gtk.Align.CENTER)
            apply_button.connect("clicked", self.preview_monitor)
            apply_display.add_suffix(apply_button)
            displays.add(apply_display)
        vrr = Adw.SwitchRow(title="Variable refresh rate", subtitle="Allow VRR on compatible displays and games")
        vrr.set_active(bool(self.settings["vrr"]))
        vrr.connect("notify::active", lambda row, _param: self.setting_value("vrr", row.get_active(), "misc:vrr", lambda value: 1 if value else 0))
        displays.add(vrr)
        if shutil.which("brightnessctl"):
            brightness = self.current_brightness()
            bright_row, bright_scale = self.scale_row("Brightness", "Hardware backlight level", 5, 100, 1, brightness)
            bright_scale.connect("value-changed", lambda scale: self.set_brightness(round(scale.get_value())))
            displays.add(bright_row)
        content.append(displays)

        pointer = Adw.PreferencesGroup(title="Mouse and pointer", description="Controls apply to Hyprland input devices immediately")
        try:
            devices = json.loads(output(["hyprctl", "devices", "-j"], "{}"))
        except ValueError:
            devices = {}
        pointer_names = [item.get("name", "Pointer") for item in devices.get("mice", [])]
        connected_pointer = Adw.ActionRow(
            title=f"Connected pointers · {len(pointer_names)}",
            subtitle=" · ".join(pointer_names[:3]) + (" · …" if len(pointer_names) > 3 else ""),
        )
        connected_pointer.add_prefix(Gtk.Image.new_from_icon_name("input-mouse-symbolic"))
        pointer.add(connected_pointer)
        sensitivity = self.scale_row("Pointer sensitivity", "Negative is slower; positive is faster", -10, 10, 1, self.settings["pointer_sensitivity"])
        sensitivity[1].connect("value-changed", lambda scale: self.delayed_setting("pointer_sensitivity", round(scale.get_value()), "input:sensitivity", lambda value: value / 10))
        pointer.add(sensitivity[0])
        acceleration = Adw.ActionRow(title="Acceleration profile", subtitle="Flat is consistent; adaptive responds to movement speed")
        accel_values = ["flat", "adaptive"]
        accel_dropdown = Gtk.DropDown.new_from_strings(["Flat", "Adaptive"])
        accel_dropdown.set_selected(accel_values.index(self.settings["accel_profile"]) if self.settings["accel_profile"] in accel_values else 0)
        accel_dropdown.connect("notify::selected", lambda widget, _param: self.setting_value("accel_profile", accel_values[widget.get_selected()], "input:accel_profile"))
        acceleration.add_suffix(accel_dropdown)
        pointer.add(acceleration)
        scroll_speed = self.scale_row("Scroll speed", "Multiplier for wheel and touchpad scrolling", 25, 200, 5, self.settings["scroll_factor"])
        scroll_speed[1].connect("value-changed", lambda scale: self.delayed_setting("scroll_factor", round(scale.get_value()), "input:scroll_factor", lambda value: value / 100))
        pointer.add(scroll_speed[0])
        for key, title, subtitle, option in (
            ("natural_scroll", "Natural scrolling", "Content follows your fingers", "input:touchpad:natural_scroll"),
            ("left_handed", "Left-handed buttons", "Swap primary and secondary pointer buttons", "input:left_handed"),
        ):
            row = Adw.SwitchRow(title=title, subtitle=subtitle)
            row.set_active(bool(self.settings[key]))
            row.connect("notify::active", lambda widget, _param, setting=key, target=option: self.setting_bool(setting, widget.get_active(), target))
            pointer.add(row)
        content.append(pointer)

        touchpad = Adw.PreferencesGroup(title="Touchpad")
        for key, title, subtitle, option in (
            ("tap_to_click", "Tap to click", "A light tap performs a primary click", "input:touchpad:tap-to-click"),
            ("disable_while_typing", "Disable while typing", "Prevent accidental pointer movement", "input:touchpad:disable_while_typing"),
            ("clickfinger", "Clickfinger buttons", "Choose buttons from finger count", "input:touchpad:clickfinger_behavior"),
        ):
            row = Adw.SwitchRow(title=title, subtitle=subtitle)
            row.set_active(bool(self.settings[key]))
            row.connect("notify::active", lambda widget, _param, setting=key, target=option: self.setting_bool(setting, widget.get_active(), target))
            touchpad.add(row)
        content.append(touchpad)

        keyboard = Adw.PreferencesGroup(title="Keyboard", description="Layout and repeat behavior")
        keyboard_names = [item.get("name", "Keyboard") for item in devices.get("keyboards", []) if not item.get("name", "").startswith("video-bus")]
        connected_keyboard = Adw.ActionRow(
            title=f"Connected keyboards · {len(keyboard_names)}",
            subtitle=" · ".join(keyboard_names[:3]) + (" · …" if len(keyboard_names) > 3 else ""),
        )
        connected_keyboard.add_prefix(Gtk.Image.new_from_icon_name("input-keyboard-symbolic"))
        keyboard.add(connected_keyboard)
        layout_row = Adw.ActionRow(title="Keyboard layout", subtitle="Applied to every Hyprland keyboard")
        layouts = ["us", "gb", "de", "fr", "es"]
        layout_names = ["English (US)", "English (UK)", "German", "French", "Spanish"]
        layout_dropdown = Gtk.DropDown.new_from_strings(layout_names)
        current_layout = str(hypr_option("input:kb_layout", "us"))
        layout_dropdown.set_selected(layouts.index(current_layout) if current_layout in layouts else 0)
        layout_dropdown.connect("notify::selected", lambda widget, _param: self.setting_value("kb_layout", layouts[widget.get_selected()], "input:kb_layout"))
        layout_row.add_suffix(layout_dropdown)
        keyboard.add(layout_row)
        repeat_rate = self.scale_row("Repeat rate", "Characters repeated per second", 10, 60, 1, self.settings["repeat_rate"])
        repeat_rate[1].connect("value-changed", lambda scale: self.delayed_setting("repeat_rate", round(scale.get_value()), "input:repeat_rate"))
        keyboard.add(repeat_rate[0])
        repeat_delay = self.scale_row("Repeat delay", "Milliseconds before a held key repeats", 200, 1000, 50, self.settings["repeat_delay"])
        repeat_delay[1].connect("value-changed", lambda scale: self.delayed_setting("repeat_delay", round(scale.get_value()), "input:repeat_delay"))
        keyboard.add(repeat_delay[0])
        numlock = Adw.SwitchRow(title="Num Lock on startup", subtitle="Enable the numeric keypad after login")
        numlock.set_active(bool(self.settings["numlock"]))
        numlock.connect("notify::active", lambda row, _param: self.setting_bool("numlock", row.get_active(), "input:numlock_by_default"))
        keyboard.add(numlock)
        content.append(keyboard)

        sound = Adw.PreferencesGroup(title="Sound", description="PipeWire output and microphone controls")
        sink_volume, sink_muted = self.wp_volume("@DEFAULT_AUDIO_SINK@")
        output_row, output_scale = self.scale_row("Output volume", "Speakers and headphones", 0, 125, 1, sink_volume)
        output_scale.connect("value-changed", lambda scale: self.set_wp_volume("@DEFAULT_AUDIO_SINK@", round(scale.get_value())))
        sound.add(output_row)
        output_mute = Adw.SwitchRow(title="Mute output", subtitle="Silence all playback")
        output_mute.set_active(sink_muted)
        output_mute.connect("notify::active", lambda row, _param: run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if row.get_active() else "0"]))
        sound.add(output_mute)
        mic_volume, mic_muted = self.wp_volume("@DEFAULT_AUDIO_SOURCE@")
        mic_row, mic_scale = self.scale_row("Microphone level", "Default recording input", 0, 125, 1, mic_volume)
        mic_scale.connect("value-changed", lambda scale: self.set_wp_volume("@DEFAULT_AUDIO_SOURCE@", round(scale.get_value())))
        sound.add(mic_row)
        mic_mute = Adw.SwitchRow(title="Mute microphone", subtitle="Prevent applications from recording audio")
        mic_mute.set_active(mic_muted)
        mic_mute.connect("notify::active", lambda row, _param: run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "1" if row.get_active() else "0"]))
        sound.add(mic_mute)
        mixer = self.command_row("Advanced audio mixer", "Per-device and per-application routing", "audio-volume-high-symbolic", ["pavucontrol"])
        sound.add(mixer)
        content.append(sound)

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

        connectivity = Adw.PreferencesGroup(title="Connectivity")
        wifi_active = output(["nmcli", "-t", "-f", "WIFI", "general"], "disabled") == "enabled"
        wifi = Adw.SwitchRow(title="Wi-Fi", subtitle="Enable or disable the wireless radio")
        wifi.set_active(wifi_active)
        wifi.connect("notify::active", lambda row, _param: run(["nmcli", "radio", "wifi", "on" if row.get_active() else "off"]))
        connectivity.add(wifi)
        bluetooth_active = "Powered: yes" in output(["bluetoothctl", "show"], "")
        bluetooth = Adw.SwitchRow(title="Bluetooth", subtitle="Enable or disable the Bluetooth radio")
        bluetooth.set_active(bluetooth_active)
        bluetooth.connect("notify::active", lambda row, _param: run(["bluetoothctl", "power", "on" if row.get_active() else "off"]))
        connectivity.add(bluetooth)
        connectivity.add(self.command_row("Network connections", "Wi-Fi, Ethernet, DNS and saved profiles", "network-wired-symbolic", ["nm-connection-editor"]))
        content.append(connectivity)

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
        caffeine = Adw.SwitchRow(title="Caffeine", subtitle="Pause automatic locking and idle actions")
        caffeine.set_active(caffeine_enabled())
        caffeine.connect("notify::active", lambda row, _param: async_call(lambda: set_caffeine(row.get_active())))
        performance.add(caffeine)
        game = Adw.ActionRow(title="Game Accelerator", subtitle="Telemetry, Boost sessions and memory tools")
        game.add_prefix(Gtk.Image.new_from_icon_name("applications-games-symbolic"))
        game.set_activatable(True)
        game.connect("activated", lambda *_: self.show_page("game"))
        performance.add(game)
        content.append(performance)

        focus = Adw.PreferencesGroup(title="Focus and accessibility")
        dnd = Adw.SwitchRow(title="Do Not Disturb", subtitle="Silence notification popups while preserving history")
        dnd.set_active(dnd_enabled())
        dnd.connect("notify::active", lambda row, _param: async_call(lambda: set_dnd(row.get_active())))
        focus.add(dnd)
        cursor = self.scale_row("Cursor size", "Hyprland and XWayland pointer size", 12, 48, 1, self.settings["cursor_size"])
        cursor[1].connect("value-changed", lambda scale: self.cursor_size_changed(round(scale.get_value())))
        focus.add(cursor[0])
        focus.add(self.command_row("Lock screen", "Secure the session immediately", "system-lock-screen-symbolic", ["hyprlock"]))
        content.append(focus)

        system = Adw.PreferencesGroup(title="System and maintenance")
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
        reload_row = Adw.ActionRow(title="Reload OrbitOS", subtitle="Reload Hyprland configuration and restart the top bar")
        reload_row.add_prefix(Gtk.Image.new_from_icon_name("view-refresh-symbolic"))
        reload_row.set_activatable(True)
        reload_row.connect("activated", lambda *_: self.reload_orbitos())
        system.add(reload_row)
        logs = self.command_row("System logs", "Open recent user-session errors", "text-x-generic-symbolic", ["kitty", "--title", "OrbitOS Logs", "-e", "journalctl", "--user", "-f"])
        system.add(logs)
        reset_row = Adw.ActionRow(title="Reset OrbitOS settings", subtitle="Return app-managed values to the dotfile defaults")
        reset_row.add_prefix(Gtk.Image.new_from_icon_name("edit-undo-symbolic"))
        reset_row.set_activatable(True)
        reset_row.add_css_class("property")
        reset_row.connect("activated", self.confirm_reset_settings)
        system.add(reset_row)
        content.append(system)

        about = Adw.PreferencesGroup(title="About")
        identity = Adw.ActionRow(title="OrbitOS", subtitle="A UX-first desktop ecosystem for Arch Linux and Hyprland")
        identity.add_prefix(Gtk.Image.new_from_icon_name("starred-symbolic"))
        about.add(identity)
        content.append(about)
        return scroll

    @staticmethod
    def scale_row(title: str, subtitle: str, low: float, high: float, step: float, value: object) -> tuple[Adw.ActionRow, Gtk.Scale]:
        row = Adw.ActionRow(title=title, subtitle=subtitle)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, low, high, step)
        scale.set_value(float(value))
        scale.set_size_request(260, -1)
        scale.set_valign(Gtk.Align.CENTER)
        scale.set_draw_value(True)
        scale.set_digits(0 if step >= 1 else 1)
        row.add_suffix(scale)
        return row, scale

    @staticmethod
    def command_row(title: str, subtitle: str, icon: str, command: list[str]) -> Adw.ActionRow:
        row = Adw.ActionRow(title=title, subtitle=subtitle)
        row.add_prefix(Gtk.Image.new_from_icon_name(icon))
        row.set_activatable(True)
        row.connect("activated", lambda _row: detached(command))
        return row

    def setting_value(self, key: str, value: object, option: str, convert: Callable[[object], object] | None = None) -> None:
        self.settings[key] = value
        self.persist_settings()
        applied = convert(value) if convert else value
        if not hypr_keyword(option, applied):
            self.toast(f"Could not apply {key.replace('_', ' ')}")

    def delayed_setting(self, key: str, value: object, option: str, convert: Callable[[object], object] | None = None) -> None:
        self.settings[key] = value
        self.persist_settings()
        if source := self.setting_timeouts.pop(key, 0):
            GLib.source_remove(source)

        def apply_value() -> bool:
            self.setting_timeouts.pop(key, None)
            applied = convert(value) if convert else value
            if not hypr_keyword(option, applied):
                self.toast(f"Could not apply {key.replace('_', ' ')}")
            return GLib.SOURCE_REMOVE

        self.setting_timeouts[key] = GLib.timeout_add(140, apply_value)

    @staticmethod
    def current_brightness() -> int:
        raw = output(["brightnessctl", "-m"], "")
        try:
            return int(raw.split(",")[3].rstrip("%"))
        except (ValueError, IndexError):
            return 100

    def set_brightness(self, value: int) -> None:
        key = "brightness"
        if source := self.setting_timeouts.pop(key, 0):
            GLib.source_remove(source)
        self.setting_timeouts[key] = GLib.timeout_add(
            120,
            lambda: (self.setting_timeouts.pop(key, None), run(["brightnessctl", "set", f"{value}%"]), GLib.SOURCE_REMOVE)[-1],
        )

    @staticmethod
    def wp_volume(target: str) -> tuple[int, bool]:
        raw = output(["wpctl", "get-volume", target], "Volume: 0")
        try:
            value = round(float(raw.split()[1]) * 100)
        except (ValueError, IndexError):
            value = 0
        return value, "MUTED" in raw

    def set_wp_volume(self, target: str, value: int) -> None:
        key = f"volume-{target}"
        if source := self.setting_timeouts.pop(key, 0):
            GLib.source_remove(source)
        self.setting_timeouts[key] = GLib.timeout_add(
            100,
            lambda: (self.setting_timeouts.pop(key, None), run(["wpctl", "set-volume", "-l", "1.25", target, f"{value / 100:.2f}"]), GLib.SOURCE_REMOVE)[-1],
        )

    def cursor_size_changed(self, value: int) -> None:
        self.settings["cursor_size"] = value
        self.persist_settings()
        key = "cursor_size"
        if source := self.setting_timeouts.pop(key, 0):
            GLib.source_remove(source)

        def apply_cursor() -> bool:
            self.setting_timeouts.pop(key, None)
            theme = os.environ.get("XCURSOR_THEME") or "breeze_cursors"
            run(["hyprctl", "setcursor", theme, str(value)])
            return GLib.SOURCE_REMOVE

        self.setting_timeouts[key] = GLib.timeout_add(150, apply_cursor)

    def preview_monitor(self, _button) -> None:
        if not self.monitor:
            self.toast("No active display found")
            return
        previous = {
            "output": self.monitor["name"],
            "mode": f"{self.monitor['width']}x{self.monitor['height']}@{self.monitor['refreshRate']:.2f}",
            "position": f"{self.monitor['x']}x{self.monitor['y']}",
            "scale": float(self.monitor.get("scale", 1)),
            "transform": int(self.monitor.get("transform", 0)),
        }
        mode = self.monitor_modes[self.mode_dropdown.get_selected()].replace("Hz", "") if self.monitor_modes else "preferred"
        proposed = {
            "output": self.monitor["name"],
            "mode": mode,
            "position": previous["position"],
            "scale": float(self.monitor_scales[self.monitor_scale_dropdown.get_selected()]),
            "transform": self.monitor_transforms[self.orientation_dropdown.get_selected()],
        }
        if not apply_monitor(proposed):
            self.toast("The display configuration was rejected")
            return
        self.monitor_previous = previous
        self.monitor_proposed = proposed
        self.monitor_timeout = GLib.timeout_add_seconds(12, self.rollback_monitor)
        dialog = Adw.AlertDialog(
            heading="Keep this display configuration?",
            body="OrbitOS will automatically restore the previous display after 12 seconds if you cannot confirm.",
        )
        dialog.add_response("revert", "Revert")
        dialog.add_response("keep", "Keep")
        dialog.set_response_appearance("keep", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("keep")
        dialog.set_close_response("revert")
        dialog.connect("response", self.monitor_response)
        self.monitor_dialog = dialog
        dialog.present(self)

    def rollback_monitor(self) -> bool:
        if getattr(self, "monitor_previous", None):
            apply_monitor(self.monitor_previous)
            self.monitor_previous = None
            self.toast("Previous display configuration restored")
        self.monitor_timeout = 0
        dialog = getattr(self, "monitor_dialog", None)
        if dialog:
            self.monitor_dialog = None
            dialog.force_close()
        return GLib.SOURCE_REMOVE

    def monitor_response(self, _dialog, response: str) -> None:
        if timeout := getattr(self, "monitor_timeout", 0):
            GLib.source_remove(timeout)
            self.monitor_timeout = 0
        self.monitor_dialog = None
        if response == "keep":
            self.settings["monitor"] = self.monitor_proposed
            self.persist_settings()
            self.monitor_previous = None
            self.toast("Display configuration saved")
        else:
            self.rollback_monitor()

    def reload_orbitos(self) -> None:
        result = run(["hyprctl", "reload", "config-only"], timeout=10)
        run(["quickshell", "kill"], timeout=5)
        detached(["quickshell", "--daemonize"])
        if result and result.returncode == 0:
            self.toast("OrbitOS reloaded")
        else:
            self.toast("Hyprland reload reported an error")

    def confirm_reset_settings(self, *_args) -> None:
        dialog = Adw.AlertDialog(
            heading="Reset OrbitOS settings?",
            body="App-managed overrides will be removed and the dotfile configuration will be reloaded. Your files and application data are not affected.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("reset", "Reset")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self.reset_settings_response)
        dialog.present(self)

    def reset_settings_response(self, _dialog, response: str) -> None:
        if response != "reset":
            return
        try:
            SETTINGS_FILE.unlink(missing_ok=True)
        except OSError:
            self.toast("Could not remove the settings override")
            return
        run(["hyprctl", "reload", "config-only"], timeout=10)
        speed_script = QS_SCRIPTS / "animation-speed.py"
        if speed_script.exists():
            run([str(speed_script), "set", "100"], timeout=8)
        self.toast("Settings reset; reopen Settings to refresh every control")

    def persist_settings(self) -> None:
        save_json(SETTINGS_FILE, self.settings)

    def setting_bool(self, key: str, value: bool, keyword: str) -> None:
        self.settings[key] = value
        self.persist_settings()
        if hypr_keyword(keyword, value):
            self.toast(f"{key.replace('_', ' ').title()} {'enabled' if value else 'disabled'}")
        else:
            self.toast(f"Could not apply {key.replace('_', ' ')}")

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
