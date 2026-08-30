#!/usr/bin/env python3
"""Persist and apply OrbitOS Hyprland animation speed."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "orbitos" / "animation-speed"

ANIMATIONS = [
    ("windows", 4.2, "overshot", "popin 72%"),
    ("windowsIn", 4.5, "overshot", "popin 68%"),
    ("windowsOut", 3.2, "md3_accel", "popin 80%"),
    ("windowsMove", 4.0, "orbit_spring", ""),
    ("border", 5.5, "md3_standard", ""),
    ("fade", 3.2, "md3_standard", ""),
    ("fadeIn", 4.0, "md3_decel", ""),
    ("fadeOut", 3.0, "md3_accel", ""),
    ("fadeSwitch", 2.2, "md3_standard", ""),
    ("fadeShadow", 4.0, "softAcDecel", ""),
    ("fadeGlow", 4.0, "softAcDecel", ""),
    ("fadeDim", 3.0, "md3_standard", ""),
    ("layersIn", 4.0, "overshot", "slide top"),
    ("layersOut", 3.0, "md3_accel", "slide top"),
    ("fadeLayersIn", 3.5, "menu_decel", ""),
    ("fadeLayersOut", 3.0, "menu_accel", ""),
    ("workspaces", 5.5, "orbit_spring", "slidefade 18%"),
    ("specialWorkspace", 5.0, "overshot", "slidefadevert 22%"),
    ("fadeLayers", 3.3, "md3_standard", ""),
    ("fadePopups", 3.0, "md3_standard", ""),
    ("fadePopupsIn", 3.5, "overshot", ""),
    ("fadePopupsOut", 2.6, "md3_accel", ""),
    ("fadeDpms", 7.0, "linear", ""),
    ("borderangle", 12.0, "linear", "once"),
    ("shadowangle", 14.0, "linear", "once"),
    ("glowangle", 14.0, "linear", "once"),
    ("workspacesIn", 5.5, "orbit_spring", "slidefade 18%"),
    ("workspacesOut", 4.5, "md3_accel", "slidefade 18%"),
    ("specialWorkspaceIn", 5.0, "overshot", "slidefadevert 22%"),
    ("specialWorkspaceOut", 4.0, "md3_accel", "slidefadevert 22%"),
    ("zoomFactor", 4.0, "orbit_spring", ""),
    ("monitorAdded", 8.0, "orbit_spring", ""),
]


def current() -> int:
    try:
        return max(50, min(180, int(STATE.read_text().strip())))
    except (OSError, ValueError):
        return 100


def apply(percent: int) -> None:
    factor = percent / 100
    for leaf, base, curve, style in ANIMATIONS:
        value = f"{leaf},1,{base * factor:.2f},{curve}"
        if style:
            value += f",{style}"
        subprocess.run(["hyprctl", "keyword", "animation", value], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "get"
    percent = current()
    if command == "set":
        if len(sys.argv) != 3:
            return 2
        percent = max(50, min(180, int(float(sys.argv[2]))))
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(f"{percent}\n")
        apply(percent)
    elif command == "apply":
        apply(percent)
    print(percent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
