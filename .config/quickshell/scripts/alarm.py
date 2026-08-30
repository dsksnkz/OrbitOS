#!/usr/bin/env python3
"""Small local alarm manager for the OrbitOS time hub."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

STATE_DIR = Path.home() / ".local/state/orbitos"
STATE_FILE = STATE_DIR / "alarms.json"
ALARM_RING = Path(__file__).with_name("alarm-ring.sh")


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, check=False, **kwargs)


def load_alarms() -> list[dict[str, object]]:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    now = int(time.time())
    return [item for item in data if isinstance(item, dict) and int(item.get("timestamp", 0)) > now]


def save_alarms(alarms: list[dict[str, object]]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(alarms, indent=2) + "\n", encoding="utf-8")


def notify(message: str) -> None:
    run(["notify-send", "OrbitOS Alarm", message])


def rofi(prompt: str, choices: str = "") -> str:
    result = run(
        ["rofi", "-dmenu", "-p", prompt],
        input=choices,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def parse_alarm(value: str) -> tuple[datetime, str] | None:
    relative = re.fullmatch(r"\+(\d{1,4})(?:\s+(.+))?", value.strip())
    if relative:
        minutes = int(relative.group(1))
        if not 1 <= minutes <= 10080:
            return None
        return datetime.now() + timedelta(minutes=minutes), relative.group(2) or "Alarm"

    absolute = re.fullmatch(r"(\d{1,2}):(\d{2})(?:\s+(.+))?", value.strip())
    if not absolute:
        return None
    hour, minute = int(absolute.group(1)), int(absolute.group(2))
    if hour > 23 or minute > 59:
        return None
    target = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= datetime.now():
        target += timedelta(days=1)
    return target, absolute.group(3) or "Alarm"


def add_alarm() -> int:
    value = rofi("Alarm: HH:MM label or +minutes", "07:30 Wake up\n+25 Focus break\n")
    if not value:
        return 0
    parsed = parse_alarm(value)
    if parsed is None:
        notify("Use HH:MM label or +minutes label")
        return 1
    target, label = parsed
    alarm_id = f"{int(target.timestamp())}-{int(time.time() * 1000) % 100000}"
    unit = f"orbitos-alarm-{alarm_id}"
    command = [
        "systemd-run",
        "--user",
        f"--unit={unit}",
        f"--on-calendar={target:%Y-%m-%d %H:%M:%S}",
        "--timer-property=AccuracySec=1s",
        "--collect",
        str(ALARM_RING),
        label,
    ]
    result = run(command, capture_output=True)
    if result.returncode != 0:
        notify("Could not schedule alarm")
        return result.returncode
    alarms = load_alarms()
    alarms.append({"id": alarm_id, "timestamp": int(target.timestamp()), "label": label})
    alarms.sort(key=lambda item: int(item["timestamp"]))
    save_alarms(alarms)
    notify(f"{target:%a %H:%M} · {label}")
    return 0


def next_alarm() -> int:
    alarms = load_alarms()
    save_alarms(alarms)
    if not alarms:
        print("No alarms scheduled")
        return 0
    alarm = alarms[0]
    target = datetime.fromtimestamp(int(alarm["timestamp"]))
    print(f"{target:%a %H:%M} · {alarm['label']}")
    return 0


def manage_alarms() -> int:
    alarms = load_alarms()
    save_alarms(alarms)
    if not alarms:
        notify("No alarms scheduled")
        return 0
    lines = []
    for alarm in alarms:
        target = datetime.fromtimestamp(int(alarm["timestamp"]))
        lines.append(f"{target:%a %H:%M}  {alarm['label']}")
    choice = rofi("Cancel alarm", "\n".join(lines) + "\nCancel all alarms\n")
    if not choice:
        return 0
    if choice == "Cancel all alarms":
        selected = alarms
        remaining: list[dict[str, object]] = []
    else:
        try:
            index = lines.index(choice)
        except ValueError:
            return 0
        selected = [alarms[index]]
        remaining = [alarm for offset, alarm in enumerate(alarms) if offset != index]
    for alarm in selected:
        unit = f"orbitos-alarm-{alarm['id']}.timer"
        run(["systemctl", "--user", "stop", unit], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    save_alarms(remaining)
    notify("Alarm cancelled" if len(selected) == 1 else "All alarms cancelled")
    return 0


def copy_value(kind: str) -> int:
    if not shutil.which("wl-copy"):
        notify("wl-copy is not installed")
        return 1
    value = datetime.now().strftime("%H:%M:%S" if kind == "time" else "%A, %d %B %Y")
    result = run(["wl-copy"], input=value)
    if result.returncode == 0:
        notify(f"Copied {kind}: {value}")
    return result.returncode


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "next"
    actions = {
        "add": add_alarm,
        "next": next_alarm,
        "manage": manage_alarms,
        "copy-time": lambda: copy_value("time"),
        "copy-date": lambda: copy_value("date"),
    }
    handler = actions.get(action)
    if handler is None:
        print(f"Unknown action: {action}", file=sys.stderr)
        return 2
    return handler()


if __name__ == "__main__":
    raise SystemExit(main())
