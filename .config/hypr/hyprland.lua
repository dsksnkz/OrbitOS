--                       __  __
--     ____ ___  ____ _/ /_/ /____
--   / __ `__ \/ __ `/ __/ __/ _ \
--  / / / / / / /_/ / /_/ /_/  __/
-- /_/ /_/ /_/\__,_/\__/\__/\___/


local var_mainMod = "SUPER"
local var_terminal = "kitty"
local var_fileManager = "nautilus"
local var_menu = "rofi -show drun"
local var_browser = "flatpak run app.zen_browser.zen"


-- ###############

-- ## MONITORS ###

-- ###############

-- See https://wiki.hypr.land/Configuring/Monitors/
hl.monitor({
    output = "eDP-1",
    disabled = true,
})

hl.monitor({
    output = "HDMI-A-1",
    mode = "1920x1080@200",
    position = "0x0",
    scale = 1,
})

-- ##################

-- ## MY PROGRAMS ###

-- ##################

-- See https://wiki.hypr.land/Configuring/Keywords/

-- Set programs that you use

-- ################

-- ## AUTOSTART ###

-- ################

-- Autostart necessary processes (like notifications daemons, status bars, etc.)

-- Or execute your favorite apps at launch like this:

-- exec-once = $terminal

-- exec-once = nm-applet &
hl.window_rule({
    match = {
        class = "clipse",
    },
    float = true,
})
hl.window_rule({
    match = {
        class = "clipse",
    },
    size = "622 652",
})
hl.bind("SUPER + V", hl.dsp.exec_cmd("kitty --class clipse -e 'clipse'"))

hl.on("hyprland.start", function()
    hl.exec_cmd("~/.local/bin/orbitos-boot")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("quickshell --daemonize")
    hl.exec_cmd("~/.local/bin/orbitos-settings --apply")
    hl.exec_cmd("swayosd-server")
    hl.exec_cmd("clipse -listen")
    hl.exec_cmd("systemd-run --user --unit=orbitos-hypridle --collect hypridle")
    hl.exec_cmd("hyprpm reload")
end)

-- Example: bind = SUPER, V, exec, alacritty --class clipse -e 'clipse'

-- ############################

-- ## ENVIRONMENT VARIABLES ###

-- ############################

-- See https://wiki.hypr.land/Configuring/Environment-variables/
hl.env("XCURSOR_SIZE", "15")
hl.env("HYPRCURSOR_SIZE", "15")

-- ##################

-- ## PERMISSIONS ###

-- ##################

-- See https://wiki.hypr.land/Configuring/Permissions/

-- Please note permission changes here require a Hyprland restart and are not applied on-the-fly

-- for security reasons

-- ecosystem {

-- enforce_permissions = 1

-- }

-- permission = /usr/(bin|local/bin)/grim, screencopy, allow

-- permission = /usr/(lib|libexec|lib64)/xdg-desktop-portal-hyprland, screencopy, allow
hl.permission("/usr/(bin|local/bin)/hyprpm", "plugin", "allow")
hl.permission("/usr/(bin|local/bin)/hyprpm", "plugin", "allow")

-- ####################

-- ## LOOK AND FEEL ###

-- ####################

-- Refer to https://wiki.hypr.land/Configuring/Variables/

-- https://wiki.hypr.land/Configuring/Variables/#general
hl.config({
    general = {
        gaps_in = 3,
        gaps_out = 6,
        border_size = 1,
    },
})

-- https://wiki.hypr.land/Configuring/Variables/#variable-types for info about colors
hl.config({
    general = {
        col = {
            active_border = {
                colors = { "rgb(FFFFFF)", "rgb(666666)", "rgb(FFFFFF)" },
                angle = 45,
            },
            inactive_border = "rgb(242424)",
        },
    },
})

-- Set to true enable resizing windows by clicking and dragging on borders and gaps
hl.config({
    general = {
        resize_on_border = false,
    },
})

-- Please see https://wiki.hypr.land/Configuring/Tearing/ before you turn this on
hl.config({
    general = {
        allow_tearing = false,
        layout = "dwindle",
    },
})

-- Keep fullscreen frames composited on the hybrid NVIDIA display path.
-- Direct scanout can produce flashing corruption on this monitor/GPU combination.
hl.config({
    render = {
        direct_scanout = false,
    },
})

-- https://wiki.hypr.land/Configuring/Variables/#decoration
hl.config({
    decoration = {
        rounding = 3,
        rounding_power = 2,
    },
})

-- Change transparency of focused and unfocused windows
hl.config({
    decoration = {
        active_opacity = 1.0,
        inactive_opacity = 0.94,
        shadow = {
            enabled = true,
            range = 12,
            render_power = 3,
            color = {
                colors = { "rgba(000000dd)", "rgba(66666644)" },
                angle = 45,
            },
        },
        glow = {
            enabled = true,
            range = 6,
            render_power = 3,
            color = {
                colors = { "rgba(ffffff33)", "rgba(77777711)" },
                angle = 45,
            },
        },
        motion_blur = {
            enabled = true,
            samples = 7,
        },
    },
})

-- https://wiki.hypr.land/Configuring/Variables/#blur
hl.config({
    decoration = {
        blur = {
            enabled = true,
            size = 5,
            passes = 2,
            vibrancy = 0.0,
            special = true,
            popups = true,
        },
    },
})

-- https://wiki.hypr.land/Configuring/Variables/#animations
hl.config({
    animations = {
        enabled = true,
        workspace_wraparound = true,
    },
})

-- Keep rapid Super + wheel workspace navigation responsive.
hl.config({
    binds = {
        scroll_event_delay = 60,
    },
})

-- Animation curves
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.curve("md3_standard", { type = "bezier", points = { { 0.2, 0 }, { 0, 1 } } })
hl.curve("md3_decel", { type = "bezier", points = { { 0.05, 0.7 }, { 0.1, 1 } } })
hl.curve("md3_accel", { type = "bezier", points = { { 0.3, 0 }, { 0.8, 0.15 } } })
hl.curve("overshot", { type = "bezier", points = { { 0.05, 0.9 }, { 0.1, 1.1 } } })
hl.curve("crazyshot", { type = "bezier", points = { { 0.1, 1.5 }, { 0.76, 0.92 } } })
hl.curve("hyprnostretch", { type = "bezier", points = { { 0.05, 0.9 }, { 0.1, 1.0 } } })
hl.curve("menu_decel", { type = "bezier", points = { { 0.1, 1 }, { 0, 1 } } })
hl.curve("menu_accel", { type = "bezier", points = { { 0.38, 0.04 }, { 1, 0.07 } } })
hl.curve("easeInOutCirc", { type = "bezier", points = { { 0.85, 0 }, { 0.15, 1 } } })
hl.curve("easeOutCirc", { type = "bezier", points = { { 0, 0.55 }, { 0.45, 1 } } })
hl.curve("easeOutExpo", { type = "bezier", points = { { 0.16, 1 }, { 0.3, 1 } } })
hl.curve("softAcDecel", { type = "bezier", points = { { 0.26, 0.26 }, { 0.15, 1 } } })
hl.curve("md2", { type = "bezier", points = { { 0.4, 0 }, { 0.2, 1 } } })
hl.curve("orbit_spring", { type = "spring", mass = 1, stiffness = 170, dampening = 21 })

-- Animation configs
hl.animation({
    leaf = "windows",
    enabled = true,
    speed = 4.2,
    bezier = "overshot",
    style = "popin 72%",
})
hl.animation({
    leaf = "windowsIn",
    enabled = true,
    speed = 4.5,
    bezier = "overshot",
    style = "popin 68%",
})
hl.animation({
    leaf = "windowsOut",
    enabled = true,
    speed = 3.2,
    bezier = "md3_accel",
    style = "popin 80%",
})
hl.animation({
    leaf = "windowsMove",
    enabled = true,
    speed = 4.0,
    spring = "orbit_spring",
})
hl.animation({
    leaf = "border",
    enabled = true,
    speed = 5.5,
    bezier = "md3_standard",
})
hl.animation({
    leaf = "fade",
    enabled = true,
    speed = 3.2,
    bezier = "md3_standard",
})

hl.animation({ leaf = "fadeIn", enabled = true, speed = 4.0, bezier = "md3_decel" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 3.0, bezier = "md3_accel" })
hl.animation({ leaf = "fadeSwitch", enabled = true, speed = 2.2, bezier = "md3_standard" })
hl.animation({ leaf = "fadeShadow", enabled = true, speed = 4.0, bezier = "softAcDecel" })
hl.animation({ leaf = "fadeGlow", enabled = true, speed = 4.0, bezier = "softAcDecel" })
hl.animation({ leaf = "fadeDim", enabled = true, speed = 3.0, bezier = "md3_standard" })

-- animation = layers, 1, 2, md3_decel, slide
hl.animation({
    leaf = "layersIn",
    enabled = true,
    speed = 4.0,
    bezier = "overshot",
    style = "slide top",
})
hl.animation({
    leaf = "layersOut",
    enabled = true,
    speed = 3.0,
    bezier = "md3_accel",
    style = "slide top",
})
hl.animation({
    leaf = "fadeLayersIn",
    enabled = true,
    speed = 3.5,
    bezier = "menu_decel",
})
hl.animation({
    leaf = "fadeLayersOut",
    enabled = true,
    speed = 3.0,
    bezier = "menu_accel",
})
hl.animation({
    leaf = "workspaces",
    enabled = true,
    speed = 5.5,
    bezier = "md3_decel",
    style = "slidefade 18%",
})

-- animation = workspaces, 1, 2.5, softAcDecel, slide

-- animation = workspaces, 1, 7, menu_decel, slidefade 15%

-- animation = specialWorkspace, 1, 3, md3_decel, slidefadevert 15%
hl.animation({
    leaf = "specialWorkspace",
    enabled = true,
    speed = 5.0,
    bezier = "overshot",
    style = "slidefadevert 22%",
})

-- Explicitly animate every supported Hyprland 0.56 leaf instead of relying on inheritance.
hl.animation({ leaf = "fadeLayers", enabled = true, speed = 3.3, bezier = "md3_standard" })
hl.animation({ leaf = "fadePopups", enabled = true, speed = 3.0, bezier = "md3_standard" })
hl.animation({ leaf = "fadePopupsIn", enabled = true, speed = 3.5, bezier = "overshot" })
hl.animation({ leaf = "fadePopupsOut", enabled = true, speed = 2.6, bezier = "md3_accel" })
hl.animation({ leaf = "fadeDpms", enabled = true, speed = 7.0, bezier = "linear" })
hl.animation({ leaf = "borderangle", enabled = true, speed = 12.0, bezier = "linear", style = "once" })
hl.animation({ leaf = "shadowangle", enabled = true, speed = 14.0, bezier = "linear", style = "once" })
hl.animation({ leaf = "glowangle", enabled = true, speed = 14.0, bezier = "linear", style = "once" })
hl.animation({ leaf = "workspacesIn", enabled = true, speed = 5.5, bezier = "md3_decel", style = "slidefade 18%" })
hl.animation({ leaf = "workspacesOut", enabled = true, speed = 4.5, bezier = "md3_decel", style = "slidefade 18%" })
hl.animation({ leaf = "specialWorkspaceIn", enabled = true, speed = 5.0, bezier = "overshot", style = "slidefadevert 22%" })
hl.animation({ leaf = "specialWorkspaceOut", enabled = true, speed = 4.0, bezier = "md3_accel", style = "slidefadevert 22%" })
hl.animation({ leaf = "zoomFactor", enabled = true, speed = 4.0, spring = "orbit_spring" })
hl.animation({ leaf = "monitorAdded", enabled = true, speed = 8.0, spring = "orbit_spring" })

hl.config({
    input = {
        accel_profile = "flat",
        sensitivity = 0.0,
    }
})

-- Ref https://wiki.hypr.land/Configuring/Workspace-Rules/

-- "Smart gaps" / "No gaps when only"

-- uncomment all if you wish to use that.

-- workspace = w[tv1], gapsout:0, gapsin:0

-- workspace = f[1], gapsout:0, gapsin:0

-- windowrule = bordersize 0, floating:0, onworkspace:w[tv1]

-- windowrule = rounding 0, floating:0, onworkspace:w[tv1]

-- windowrule = bordersize 0, floating:0, onworkspace:f[1]

-- windowrule = rounding 0, floating:0, onworkspace:f[1]

-- See https://wiki.hypr.land/Configuring/Dwindle-Layout/ for more
hl.config({
    dwindle = {
        preserve_split = true,
    },
})

-- See https://wiki.hypr.land/Configuring/Master-Layout/ for more
hl.config({
    master = {
        new_status = "master",
    },
})

-- https://wiki.hypr.land/Configuring/Variables/#misc
hl.config({
    misc = {
        force_default_wallpaper = -1,
        disable_hyprland_logo = false,
    },
})

-- workspaces
hl.workspace_rule({
    workspace = 1,
    persistent = true,
})
hl.workspace_rule({
    workspace = 2,
    persistent = true,
})
hl.workspace_rule({
    workspace = 3,
    persistent = true,
})
hl.workspace_rule({
    workspace = 4,
    persistent = true,
})
hl.workspace_rule({
    workspace = 5,
    persistent = true,
})
hl.workspace_rule({
    workspace = 6,
    persistent = true,
})

-- ############

-- ## INPUT ###

-- ############

-- https://wiki.hypr.land/Configuring/Variables/#input
hl.config({
    input = {
        kb_layout = "us",
        kb_variant = "",
        kb_model = "",
        kb_options = "",
        kb_rules = "",
        follow_mouse = 1,
        sensitivity = -1,
        touchpad = {
            natural_scroll = false,
        },
    },
})

-- See https://wiki.hypr.land/Configuring/Gestures
hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace",
})

-- Example per-device config

-- See https://wiki.hypr.land/Configuring/Keywords/#per-device-input-configs for more
hl.device({
    name = "epic-mouse-v1",
    sensitivity = -1,
})

-- ##################

-- ## KEYBINDINGS ###

-- ##################

-- See https://wiki.hypr.land/Configuring/Keywords/

-- Example binds, see https://wiki.hypr.land/Configuring/Binds/ for more
hl.bind(var_mainMod .. " + W", hl.dsp.exec_cmd(var_terminal))
hl.bind(var_mainMod .. " + Q", hl.dsp.window.close())
hl.bind(var_mainMod .. " + SHIFT + M", hl.dsp.exit())
hl.bind(var_mainMod .. " + E", hl.dsp.exec_cmd(var_fileManager))
hl.bind(var_mainMod .. " + T", hl.dsp.window.float({ action = "toggle" }))
hl.bind(var_mainMod .. " + Space", hl.dsp.exec_cmd(var_menu))
hl.bind(var_mainMod .. " + P", hl.dsp.window.pseudo())
hl.bind(var_mainMod .. " + B", hl.dsp.exec_cmd("~/.config/quickshell/scripts/bar-toggle.sh"))
hl.bind(var_mainMod .. " + ESCAPE", hl.dsp.exec_cmd("quickshell ipc call orbitos toggleHome"))
hl.bind(var_mainMod .. " + I", hl.dsp.exec_cmd("~/.local/bin/orbitos-settings"))
hl.bind(var_mainMod .. " + O", hl.dsp.exec_cmd("~/.local/bin/orbitos-launcher"))
hl.bind(var_mainMod .. " + G", hl.dsp.exec_cmd("~/.local/bin/orbitos-game"))
hl.bind(var_mainMod .. " + l", hl.dsp.exec_cmd("hyprlock"))
hl.bind(var_mainMod .. " + A", hl.dsp.exec_cmd("zeditor --classic"))
hl.bind(var_mainMod .. " + S", hl.dsp.exec_cmd(var_browser))
hl.bind(var_mainMod .. " + SHIFT + S", hl.dsp.exec_cmd("~/.config/quickshell/scripts/capture.sh"))
hl.bind(var_mainMod .. " + N", hl.dsp.exec_cmd("swaync-client --toggle-panel"))
hl.bind(var_mainMod .. " + SHIFT + B", hl.dsp.exec_cmd("~/.config/quickshell/scripts/bluetooth-toggle.sh"))
hl.bind(var_mainMod .. " + SHIFT + W", hl.dsp.exec_cmd("~/.config/quickshell/scripts/wifi-toggle.sh"))
hl.bind(var_mainMod .. " + SHIFT + P", hl.dsp.exec_cmd("~/.config/quickshell/scripts/power-menu.sh"))
hl.bind(var_mainMod .. " + SHIFT + T", hl.dsp.exec_cmd("~/.config/quickshell/scripts/timer.sh"))
hl.bind(var_mainMod .. " + SHIFT + A", hl.dsp.exec_cmd("quickshell ipc call orbitos toggleTime"))
hl.bind(var_mainMod .. " + SHIFT + X", hl.dsp.exec_cmd("hyprpicker --autocopy --notify --format=hex"))
hl.bind(var_mainMod .. " + SHIFT + U", hl.dsp.exec_cmd("~/.config/quickshell/scripts/utility-menu.sh"))
hl.bind(var_mainMod .. " + SHIFT + D", hl.dsp.exec_cmd("~/.config/quickshell/scripts/dnd-toggle.sh"))
hl.bind(var_mainMod .. " + SHIFT + I", hl.dsp.exec_cmd("~/.config/quickshell/scripts/caffeine.sh"))
hl.bind("CTRL + SHIFT + ESCAPE", hl.dsp.exec_cmd("missioncenter"))


-- Move focus with mainMod + arrow keys
hl.bind(var_mainMod .. " + up", hl.dsp.focus({ direction = "up" }))

-- Switch workspaces with mainMod + [0-9]
hl.bind(var_mainMod .. " + 1", hl.dsp.focus({ workspace = 1 }))
hl.bind(var_mainMod .. " + 2", hl.dsp.focus({ workspace = 2 }))
hl.bind(var_mainMod .. " + 3", hl.dsp.focus({ workspace = 3 }))
hl.bind(var_mainMod .. " + 4", hl.dsp.focus({ workspace = 4 }))
hl.bind(var_mainMod .. " + 5", hl.dsp.focus({ workspace = 5 }))
hl.bind(var_mainMod .. " + 6", hl.dsp.focus({ workspace = 6 }))
hl.bind(var_mainMod .. " + 7", hl.dsp.focus({ workspace = 7 }))
hl.bind(var_mainMod .. " + 8", hl.dsp.focus({ workspace = 8 }))
hl.bind(var_mainMod .. " + 9", hl.dsp.focus({ workspace = 9 }))
hl.bind(var_mainMod .. " + 0", hl.dsp.focus({ workspace = 10 }))

-- Move active window to a workspace with mainMod + SHIFT + [0-9]
hl.bind(var_mainMod .. " + SHIFT + 1", hl.dsp.window.move({ workspace = 1 }))
hl.bind(var_mainMod .. " + SHIFT + 2", hl.dsp.window.move({ workspace = 2 }))
hl.bind(var_mainMod .. " + SHIFT + 3", hl.dsp.window.move({ workspace = 3 }))
hl.bind(var_mainMod .. " + SHIFT + 4", hl.dsp.window.move({ workspace = 4 }))
hl.bind(var_mainMod .. " + SHIFT + 5", hl.dsp.window.move({ workspace = 5 }))
hl.bind(var_mainMod .. " + SHIFT + 6", hl.dsp.window.move({ workspace = 6 }))
hl.bind(var_mainMod .. " + SHIFT + 7", hl.dsp.window.move({ workspace = 7 }))
hl.bind(var_mainMod .. " + SHIFT + 8", hl.dsp.window.move({ workspace = 8 }))
hl.bind(var_mainMod .. " + SHIFT + 9", hl.dsp.window.move({ workspace = 9 }))
hl.bind(var_mainMod .. " + SHIFT + 0", hl.dsp.window.move({ workspace = 10 }))
-- Open Mission Center with Ctrl + Shift + ESC
-- Example special workspace (scratchpad)
hl.bind(var_mainMod .. " + C", hl.dsp.workspace.toggle_special("magic"))
hl.bind(var_mainMod .. " + SHIFT + C", hl.dsp.window.move({ workspace = "special:magic" }))

-- Scroll through existing workspaces with mainMod + scroll
hl.bind(var_mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))
hl.bind(var_mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(var_mainMod .. " + SHIFT + mouse_down", hl.dsp.window.move({ workspace = "e+1" }))
hl.bind(var_mainMod .. " + SHIFT + mouse_up", hl.dsp.window.move({ workspace = "e-1" }))

-- Move/resize windows with mainMod + LMB/RMB and dragging
hl.bind(var_mainMod .. " + mouse:272", hl.dsp.window.drag(), {
    mouse = true,
})
hl.bind(var_mainMod .. " + mouse:273", hl.dsp.window.resize(), {
    mouse = true,
})

-- Multimedia keys for volume and the active monitor brightness
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), {
    repeating = true,
    locked = true,
})
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), {
    repeating = true,
    locked = true,
})
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), {
    repeating = true,
    locked = true,
})
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), {
    repeating = true,
    locked = true,
})
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("~/.config/quickshell/scripts/brightness.py change 5"), {
    repeating = true,
    locked = true,
})
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("~/.config/quickshell/scripts/brightness.py change -5"), {
    repeating = true,
    locked = true,
})

-- Requires playerctl
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), {
    locked = true,
})
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), {
    locked = true,
})
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), {
    locked = true,
})
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), {
    locked = true,
})

-- #############################

-- ## WINDOWS AND WORKSPACES ###

-- #############################

-- See https://wiki.hypr.land/Configuring/Window-Rules/ for more

-- See https://wiki.hypr.land/Configuring/Workspace-Rules/ for workspace rules

-- Example windowrule

-- windowrule = float,class:^(kitty)$,title:^(kitty)$
hl.window_rule({
    name = "my-custom-rule",
    match = {
        class = "^(org.gnome.Nautilus)$",
    },
    float = 1,
    rounding = 3,
    no_blur = 1,
})

-- Tide Island workspace overview
hl.bind("SUPER + TAB", hl.dsp.exec_cmd("qs ipc -p /usr/share/tide-island call overview toggle"))


-- HyprMod managed settings
require("hyprland-gui")

-- TODO: the following entries need manual conversion to Lua:
--   bind = $mainMod, left, movefocus, h
--   bind = $mainMod, right, movefocus, k
--   bind = $mainMod, down, movefocus, j
