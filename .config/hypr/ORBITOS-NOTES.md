# OrbitOS preset

OrbitOS is a monochrome, animation-rich desktop preset. Hardware-specific
monitor rules, keybindings, autostart commands, input behavior, HyprMod
integration, and power settings remain based on the saved live configuration.

Theme rules:

- pure black and neutral grayscale only
- 3 px corners
- 3 px inner and 6 px outer gaps
- spring window movement with motion blur, glow, blur, and shadows
- explicit animation settings for every Hyprland 0.56 animation leaf
- animated lock fields, Kitty cursor trails, and smooth Quickshell interactions

## Command bar and tools

Waybar is intentionally absent in this profile. Quickshell provides the top
command bar and control dashboard from `~/.config/quickshell/shell.qml`.

Additional shortcuts:

- `Super+B`: toggle the Quickshell bar
- `Super+N`: notifications
- `Super+Shift+S`: region capture and clipboard copy
- `Super+Shift+B`: toggle Bluetooth
- `Super+Shift+W`: toggle Wi-Fi
- `Super+Shift+P`: confirmed power menu
- `Super+Shift+T`: timer
- `Super+Shift+A`: animated calendar, clock, and alarms
- `Super+Shift+X`: color picker
- `Super+Shift+U`: OrbitOS Tools hub
- `Super+Shift+D`: Do Not Disturb
- `Super+Shift+I`: caffeine / automatic lock toggle
