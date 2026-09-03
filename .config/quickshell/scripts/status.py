#!/usr/bin/env python3
"""Stream lightweight desktop status as one JSON object every five seconds."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path


def read_cpu() -> tuple[int, int]:
    fields = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0].split()[1:]
    values = [int(value) for value in fields]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return sum(values), idle


def memory_percent() -> int:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        key, value = line.split(":", 1)
        values[key] = int(value.strip().split()[0])
    total = values.get("MemTotal", 1)
    available = values.get("MemAvailable", 0)
    return round((total - available) * 100 / total)


def temperature() -> int | None:
    readings: list[float] = []
    for path in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            value = float(path.read_text(encoding="utf-8").strip())
            if value > 1000:
                value /= 1000
            if 5 <= value <= 120:
                readings.append(value)
        except (OSError, ValueError):
            pass
    return round(max(readings)) if readings else None


def brightness_percent() -> int | None:
    controller = Path(__file__).with_name("brightness.py")
    try:
        result = subprocess.run(
            [str(controller), "get"],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

    roots = sorted(Path("/sys/class/backlight").glob("*"))
    if not roots:
        return None
    try:
        current = int((roots[0] / "brightness").read_text(encoding="utf-8"))
        maximum = int((roots[0] / "max_brightness").read_text(encoding="utf-8"))
        return round(current * 100 / maximum)
    except (OSError, ValueError, ZeroDivisionError):
        return None


def command(args: list[str], fallback: str = "") -> str:
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return fallback


def snapshot(cpu_percent: int) -> dict[str, object]:
    wifi_enabled = command(["nmcli", "-t", "-f", "WIFI", "general"], "disabled") == "enabled"
    active_wifi = command(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"])
    ssid = next(
        (line.split(":", 1)[1] for line in active_wifi.splitlines() if line.startswith("yes:")),
        "Disconnected",
    )
    bluetooth = "Powered: yes" in command(["bluetoothctl", "show"])
    dnd = command(["swaync-client", "--skip-wait", "-D"], "false").lower() == "true"
    notifications = command(["swaync-client", "--skip-wait", "-c"], "0")
    profile = command(["powerprofilesctl", "get"], "balanced")
    return {
        "cpu": cpu_percent,
        "memory": memory_percent(),
        "temperature": temperature(),
        "brightness": brightness_percent(),
        "wifi": wifi_enabled,
        "ssid": ssid,
        "bluetooth": bluetooth,
        "dnd": dnd,
        "notifications": int(notifications) if notifications.isdigit() else 0,
        "powerProfile": profile,
        "caffeine": not bool(command(["pgrep", "-x", "hypridle"])),
    }


def main() -> None:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    previous_total, previous_idle = read_cpu()
    while True:
        time.sleep(0.4)
        total, idle = read_cpu()
        delta_total = max(1, total - previous_total)
        cpu_percent = round((delta_total - (idle - previous_idle)) * 100 / delta_total)
        previous_total, previous_idle = total, idle
        try:
            print(json.dumps(snapshot(cpu_percent), separators=(",", ":")), flush=True)
        except BrokenPipeError:
            return
        time.sleep(4.6)


if __name__ == "__main__":
    main()
