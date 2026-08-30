//@ pragma ShellId orbitos-shell
//@ pragma DropExpensiveFonts

import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Services.Mpris
import Quickshell.Services.Pipewire
import Quickshell.Services.SystemTray
import Quickshell.Services.UPower
import Quickshell.Widgets

ShellRoot {
    id: shell
    property bool controlOpen: false
    property bool timeOpen: false
    property bool homeOpen: false

    Variants {
        id: bars
        model: Quickshell.screens

        PanelWindow {
            id: bar
            required property var modelData

            property var player: Mpris.players.values.length > 0 ? Mpris.players.values[0] : null
            property var audioSink: Pipewire.defaultAudioSink
            property int cpuUsage: 0
            property int memoryUsage: 0
            property int temperature: 0
            property int brightness: 0
            property bool wifiEnabled: false
            property string ssid: "Loading…"
            property bool bluetoothEnabled: false
            property bool dndEnabled: false
            property int notificationCount: 0
            property string powerProfile: "balanced"
            property bool caffeineEnabled: false
            property int animationSpeed: 100

            function toggleControl(): void {
                shell.controlOpen = !shell.controlOpen
                if (shell.controlOpen) {
                    shell.timeOpen = false
                    shell.homeOpen = false
                }
            }

            screen: modelData
            color: "transparent"
            implicitHeight: 40
            exclusiveZone: 46

            anchors {
                top: true
                left: true
                right: true
            }
            margins {
                top: 6
                left: 6
                right: 6
            }

            PwObjectTracker {
                objects: [bar.audioSink]
            }

            SystemClock {
                id: clock
                precision: SystemClock.Seconds
            }

            Process {
                id: statusProcess
                command: [Quickshell.shellPath("scripts/status.py")]
                running: true
                stdout: SplitParser {
                    onRead: data => {
                        try {
                            const status = JSON.parse(data)
                            bar.cpuUsage = status.cpu ?? 0
                            bar.memoryUsage = status.memory ?? 0
                            bar.temperature = status.temperature ?? 0
                            bar.brightness = status.brightness ?? 0
                            bar.wifiEnabled = status.wifi ?? false
                            bar.ssid = status.ssid ?? "Disconnected"
                            bar.bluetoothEnabled = status.bluetooth ?? false
                            bar.dndEnabled = status.dnd ?? false
                            bar.notificationCount = status.notifications ?? 0
                            bar.powerProfile = status.powerProfile ?? "balanced"
                            bar.caffeineEnabled = status.caffeine ?? false
                        } catch (error) {
                            console.warn("OrbitOS status parse failed:", error)
                        }
                    }
                }
            }

            Rectangle {
                anchors.fill: parent
                radius: 3
                color: "#050505"
                border.width: 1
                border.color: "#f5f5f5"

                Row {
                    id: leftSide
                    anchors.left: parent.left
                    anchors.leftMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 5

                    BarButton {
                        label: "󰣇"
                        compact: true
                        hint: "Home"
                        active: shell.homeOpen
                        onClicked: button => {
                            shell.homeOpen = !shell.homeOpen
                            if (shell.homeOpen) {
                                shell.timeOpen = false
                                shell.controlOpen = false
                            }
                        }
                    }

                    Row {
                        spacing: 3
                        Repeater {
                            model: 10
                            Rectangle {
                                required property int index
                                readonly property int workspaceId: index + 1
                                readonly property bool selected: Hyprland.focusedWorkspace
                                    && Hyprland.focusedWorkspace.id === workspaceId

                                width: selected ? 31 : 24
                                height: 28
                                radius: 3
                                color: selected ? "#f5f5f5" : (workspaceMouse.containsMouse ? "#242424" : "transparent")
                                border.width: selected ? 0 : 1
                                border.color: workspaceMouse.containsMouse ? "#f5f5f5" : "#2d2d2d"

                                Text {
                                    anchors.centerIn: parent
                                    text: parent.workspaceId
                                    color: parent.selected ? "#050505" : "#b8b8b8"
                                    font.family: "JetBrainsMono Nerd Font"
                                    font.pixelSize: 11
                                    font.weight: parent.selected ? Font.Bold : Font.Medium
                                }
                                MouseArea {
                                    id: workspaceMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: Hyprland.dispatch("hl.dsp.focus({workspace = " + parent.workspaceId + "})")
                                }
                                Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutBack } }
                                Behavior on color { ColorAnimation { duration: 160; easing.type: Easing.OutCubic } }
                            }
                        }
                    }

                    Rectangle {
                        visible: bar.width > 1500
                        width: 1
                        height: 18
                        color: "#3b3b3b"
                    }

                    Text {
                        visible: bar.width > 1500
                        width: 230
                        text: Hyprland.activeToplevel ? Hyprland.activeToplevel.title : "Desktop"
                        color: "#b8b8b8"
                        elide: Text.ElideRight
                        font.family: "Inter"
                        font.pixelSize: 11
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Rectangle {
                    id: centerClock
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    width: clockMouse.containsMouse ? 174 : 164
                    height: 28
                    radius: 3
                    color: clockMouse.containsMouse ? "#202020" : "#0d0d0d"
                    border.width: 1
                    border.color: clockMouse.containsMouse ? "#f5f5f5" : "#343434"

                    Row {
                        anchors.centerIn: parent
                        spacing: 8
                        Item {
                            width: 14
                            height: 14
                            anchors.verticalCenter: parent.verticalCenter
                            Rectangle {
                                anchors.centerIn: parent
                                width: 12
                                height: 12
                                radius: 6
                                color: "transparent"
                                border.width: 1
                                border.color: "#555555"
                            }
                            Item {
                                anchors.fill: parent
                                Rectangle {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    anchors.top: parent.top
                                    width: 3
                                    height: 3
                                    radius: 2
                                    color: "#f5f5f5"
                                }
                                RotationAnimator on rotation {
                                    from: 0
                                    to: 360
                                    duration: 18000
                                    loops: Animation.Infinite
                                    running: true
                                }
                            }
                        }
                        Text {
                            text: Qt.formatDateTime(clock.date, "HH:mm")
                            color: "#f5f5f5"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 13
                            font.weight: Font.Bold
                        }
                        Text {
                            text: Qt.formatDateTime(clock.date, "ddd dd")
                            color: "#888888"
                            font.family: "Inter"
                            font.pixelSize: 10
                        }
                    }
                    MouseArea {
                        id: clockMouse
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: event => {
                            if (event.button === Qt.MiddleButton) {
                                shell.timeOpen = false
                                Quickshell.execDetached(["sh", "-lc", "~/.config/quickshell/scripts/timer.sh"])
                            } else if (event.button === Qt.RightButton) {
                                shell.timeOpen = false
                                Quickshell.execDetached([Quickshell.shellPath("scripts/alarm.py"), "add"])
                            } else {
                                shell.timeOpen = !shell.timeOpen
                                if (shell.timeOpen) {
                                    shell.controlOpen = false
                                    shell.homeOpen = false
                                }
                            }
                        }
                    }
                    Behavior on color { ColorAnimation { duration: 160 } }
                    Behavior on border.color { ColorAnimation { duration: 160 } }
                    Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutBack } }
                }

                Row {
                    id: rightSide
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    BarButton {
                        visible: bar.player !== null && bar.width > 1500
                        label: bar.player
                            ? ((bar.player.isPlaying ? "󰏤 " : "󰐊 ")
                                + (bar.player.trackTitle || bar.player.identity || "Media"))
                            : ""
                        width: Math.min(210, implicitWidth)
                        onClicked: button => {
                            if (!bar.player) return
                            if (button === Qt.RightButton && bar.player.canGoNext) bar.player.next()
                            else if (button === Qt.MiddleButton && bar.player.canGoPrevious) bar.player.previous()
                            else if (bar.player.canTogglePlaying) bar.player.togglePlaying()
                        }
                        onWheel: delta => {
                            if (!bar.player) return
                            if (delta > 0 && bar.player.canGoPrevious) bar.player.previous()
                            else if (delta < 0 && bar.player.canGoNext) bar.player.next()
                        }
                    }

                    BarButton {
                        visible: bar.width > 1350
                        label: " " + bar.cpuUsage + "%   " + bar.memoryUsage + "%"
                        onClicked: Quickshell.execDetached(["missioncenter"])
                    }

                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 4
                        Repeater {
                            model: SystemTray.items
                            Item {
                                required property var modelData
                                width: 25
                                height: 28
                                IconImage {
                                    anchors.centerIn: parent
                                    width: 17
                                    height: 17
                                    source: modelData.icon
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: event => {
                                        if (event.button === Qt.RightButton && modelData.hasMenu)
                                            modelData.display(bar, 0, bar.height)
                                        else if (event.button === Qt.MiddleButton)
                                            modelData.secondaryActivate()
                                        else
                                            modelData.activate()
                                    }
                                    onWheel: event => modelData.scroll(event.angleDelta.y, false)
                                }
                            }
                        }
                    }

                    BarButton {
                        label: bar.wifiEnabled ? "󰖩" : "󰖪"
                        active: bar.wifiEnabled && bar.ssid !== "Disconnected"
                        compact: true
                        onClicked: button => {
                            if (button === Qt.RightButton)
                                Quickshell.execDetached(["nm-connection-editor"])
                            else
                                Quickshell.execDetached(["sh", "-lc", "~/.config/quickshell/scripts/wifi-toggle.sh"])
                        }
                    }

                    BarButton {
                        label: bar.bluetoothEnabled ? "󰂯" : "󰂲"
                        active: bar.bluetoothEnabled
                        compact: true
                        onClicked: Quickshell.execDetached(["sh", "-lc", "~/.config/quickshell/scripts/bluetooth-toggle.sh"])
                    }

                    BarButton {
                        label: bar.audioSink && bar.audioSink.audio
                            ? ((bar.audioSink.audio.muted ? "󰝟 " : "󰕾 ")
                                + Math.round(bar.audioSink.audio.volume * 100) + "%")
                            : "󰖁"
                        onClicked: button => {
                            if (button === Qt.RightButton)
                                Quickshell.execDetached(["pavucontrol"])
                            else
                                Quickshell.execDetached(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
                        }
                        onWheel: delta => Quickshell.execDetached([
                            "wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@", delta > 0 ? "3%+" : "3%-"
                        ])
                    }

                    BarButton {
                        visible: bar.brightness > 0
                        label: "󰃠 " + bar.brightness + "%"
                        onClicked: Quickshell.execDetached(["sh", "-lc", "brightnessctl set 50%"])
                        onWheel: delta => Quickshell.execDetached([
                            "brightnessctl", "-e4", "-n2", "set", delta > 0 ? "3%+" : "3%-"
                        ])
                    }

                    BarButton {
                        label: (UPower.onBattery ? "󰁹 " : "󰂄 ")
                            + Math.round(UPower.displayDevice.percentage * 100) + "%"
                        onClicked: Quickshell.execDetached(["sh", "-lc", "~/.config/quickshell/scripts/power-profile.sh"])
                    }

                    BarButton {
                        label: bar.notificationCount > 0 ? "󰂚 " + bar.notificationCount : "󰂚"
                        active: bar.dndEnabled
                        onClicked: button => {
                            if (button === Qt.RightButton)
                                Quickshell.execDetached(["sh", "-lc", "~/.config/quickshell/scripts/dnd-toggle.sh"])
                            else
                                Quickshell.execDetached(["swaync-client", "--toggle-panel"])
                        }
                    }

                    BarButton {
                        label: "󰒓"
                        compact: true
                        active: shell.controlOpen
                        onClicked: {
                            shell.controlOpen = !shell.controlOpen
                            if (shell.controlOpen) {
                                shell.timeOpen = false
                                shell.homeOpen = false
                            }
                        }
                    }
                }
            }

            PopupWindow {
                id: controlPopup
                anchor.window: bar
                anchor.rect.x: bar.width - width
                anchor.rect.y: bar.height + 6
                implicitWidth: 382
                implicitHeight: 578
                visible: shell.controlOpen
                color: "transparent"

                Rectangle {
                    id: dashboard
                    anchors.fill: parent
                    radius: 3
                    color: "#050505"
                    border.width: 1
                    border.color: "#f5f5f5"
                    opacity: shell.controlOpen ? 1 : 0
                    transform: Translate { y: shell.controlOpen ? 0 : -12 }

                    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

                    Column {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10

                        Row {
                            width: parent.width
                            height: 42
                            Text {
                                width: parent.width - closeControl.width
                                text: "ORBITOS  /  CONTROL"
                                color: "#f5f5f5"
                                font.family: "JetBrainsMono Nerd Font"
                                font.pixelSize: 14
                                font.weight: Font.Bold
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            BarButton {
                                id: closeControl
                                label: "󰅖"
                                compact: true
                                onClicked: shell.controlOpen = false
                            }
                        }

                        Row {
                            spacing: 7
                            Repeater {
                                model: [
                                    { label: "CPU", value: bar.cpuUsage + "%" },
                                    { label: "MEMORY", value: bar.memoryUsage + "%" },
                                    { label: "THERMAL", value: bar.temperature > 0 ? bar.temperature + "°" : "—" }
                                ]
                                Rectangle {
                                    required property var modelData
                                    width: 113
                                    height: 58
                                    radius: 3
                                    color: "#101010"
                                    border.width: 1
                                    border.color: "#303030"
                                    Column {
                                        anchors.centerIn: parent
                                        spacing: 2
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: modelData.value
                                            color: "#f5f5f5"
                                            font.family: "JetBrainsMono Nerd Font"
                                            font.pixelSize: 15
                                            font.weight: Font.Bold
                                        }
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: modelData.label
                                            color: "#777777"
                                            font.family: "Inter"
                                            font.pixelSize: 9
                                            font.weight: Font.DemiBold
                                        }
                                    }
                                }
                            }
                        }

                        Grid {
                            columns: 2
                            rowSpacing: 7
                            columnSpacing: 7

                            UtilityTile {
                                icon: wifiEnabled ? "󰖩" : "󰖪"
                                title: "Wi-Fi"
                                subtitle: ssid
                                toggled: wifiEnabled
                                command: "~/.config/quickshell/scripts/wifi-toggle.sh"
                            }
                            UtilityTile {
                                icon: bluetoothEnabled ? "󰂯" : "󰂲"
                                title: "Bluetooth"
                                subtitle: bluetoothEnabled ? "Radio enabled" : "Radio disabled"
                                toggled: bluetoothEnabled
                                command: "~/.config/quickshell/scripts/bluetooth-toggle.sh"
                            }
                            UtilityTile {
                                icon: dndEnabled ? "󰂛" : "󰂚"
                                title: "Do Not Disturb"
                                subtitle: dndEnabled ? "Notifications silenced" : "Notifications enabled"
                                toggled: dndEnabled
                                command: "~/.config/quickshell/scripts/dnd-toggle.sh"
                            }
                            UtilityTile {
                                icon: caffeineEnabled ? "󰅶" : "󰾪"
                                title: "Caffeine"
                                subtitle: caffeineEnabled ? "Auto-lock paused" : "Auto-lock active"
                                toggled: caffeineEnabled
                                command: "~/.config/quickshell/scripts/caffeine.sh"
                            }
                            UtilityTile {
                                icon: powerProfile === "performance" ? "󰓅" : (powerProfile === "power-saver" ? "󰌪" : "󰾅")
                                title: "Power Profile"
                                subtitle: powerProfile
                                toggled: powerProfile === "performance"
                                command: "~/.config/quickshell/scripts/power-profile.sh"
                            }
                            UtilityTile {
                                icon: "󰋊"
                                title: "System Monitor"
                                subtitle: "CPU, GPU, disks, network"
                                command: "missioncenter"
                                onActivated: shell.controlOpen = false
                            }
                            UtilityTile {
                                icon: "󰕾"
                                title: "Audio"
                                subtitle: audioSink && audioSink.audio
                                    ? Math.round(audioSink.audio.volume * 100) + "% output"
                                    : "Open mixer"
                                command: "pavucontrol"
                                onActivated: shell.controlOpen = false
                            }
                            UtilityTile {
                                icon: "󰆍"
                                title: "OrbitOS Tools"
                                subtitle: "15 desktop utilities"
                                command: "~/.config/quickshell/scripts/utility-menu.sh"
                                onActivated: shell.controlOpen = false
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: "#303030"
                        }

                        Row {
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: 7
                            BarButton {
                                label: "󰹑 Capture"
                                onClicked: Quickshell.execDetached(["sh", "-lc", "~/.config/quickshell/scripts/capture.sh"])
                            }
                            BarButton {
                                label: "󰅍 Clipboard"
                                onClicked: Quickshell.execDetached(["kitty", "--class", "clipse", "-e", "clipse"])
                            }
                            BarButton {
                                label: "󰌾 Lock"
                                onClicked: Quickshell.execDetached(["hyprlock"])
                            }
                            BarButton {
                                label: "󰐥 Power"
                                onClicked: {
                                    shell.controlOpen = false
                                    Quickshell.execDetached(["wlogout"])
                                }
                            }
                        }

                        Column {
                            width: parent.width
                            spacing: 6

                            Row {
                                width: parent.width
                                Text {
                                    width: parent.width - speedValue.width
                                    text: "ANIMATION SPEED"
                                    color: "#9a9a9a"
                                    font.family: "JetBrainsMono Nerd Font"
                                    font.pixelSize: 9
                                    font.weight: Font.DemiBold
                                }
                                Text {
                                    id: speedValue
                                    text: bar.animationSpeed + "%"
                                    color: "#f5f5f5"
                                    font.family: "JetBrainsMono Nerd Font"
                                    font.pixelSize: 10
                                    font.weight: Font.Bold
                                }
                            }

                            Rectangle {
                                id: speedTrack
                                width: parent.width
                                height: 24
                                radius: 3
                                color: "#101010"
                                border.width: 1
                                border.color: speedMouse.containsMouse ? "#777777" : "#303030"

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 4
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: Math.max(8, (parent.width - 8) * (bar.animationSpeed - 50) / 130)
                                    height: 4
                                    radius: 2
                                    color: "#f5f5f5"
                                    Behavior on width { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
                                }
                                Rectangle {
                                    x: 4 + (parent.width - 16) * (bar.animationSpeed - 50) / 130
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 8
                                    height: 14
                                    radius: 2
                                    color: "#f5f5f5"
                                    Behavior on x { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
                                }
                                MouseArea {
                                    id: speedMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    function updateSpeed(mouseX): void {
                                        bar.animationSpeed = Math.round(50 + Math.max(0, Math.min(1, mouseX / width)) * 130)
                                        speedApply.restart()
                                    }
                                    onPressed: event => updateSpeed(event.x)
                                    onPositionChanged: event => { if (pressed) updateSpeed(event.x) }
                                    onWheel: event => {
                                        bar.animationSpeed = Math.max(50, Math.min(180,
                                            bar.animationSpeed + (event.angleDelta.y > 0 ? 5 : -5)))
                                        speedApply.restart()
                                    }
                                }
                            }

                            Row {
                                width: parent.width
                                Text { width: parent.width / 2; text: "CALM"; color: "#555555"; font.family: "Inter"; font.pixelSize: 8 }
                                Text { width: parent.width / 2; text: "SWIFT"; color: "#555555"; font.family: "Inter"; font.pixelSize: 8; horizontalAlignment: Text.AlignRight }
                            }
                        }
                    }
                }

                Timer {
                    id: speedApply
                    interval: 140
                    onTriggered: Quickshell.execDetached([
                        Quickshell.shellPath("scripts/animation-speed.py"), "set", bar.animationSpeed.toString()
                    ])
                }

                Process {
                    command: [Quickshell.shellPath("scripts/animation-speed.py"), "apply"]
                    running: true
                    stdout: SplitParser { onRead: data => bar.animationSpeed = parseInt(data.trim()) || 100 }
                }
            }

            HomeScreen {
                anchorWindow: bar
                opened: shell.homeOpen
                onCloseRequested: shell.homeOpen = false
                onControlRequested: {
                    shell.homeOpen = false
                    shell.controlOpen = true
                }
            }

            TimeHub {
                anchorWindow: bar
                opened: shell.timeOpen
                onCloseRequested: shell.timeOpen = false
            }
        }
    }

    IpcHandler {
        target: "orbitos"

        function toggleControl(): void {
            shell.controlOpen = !shell.controlOpen
            if (shell.controlOpen) {
                shell.timeOpen = false
                shell.homeOpen = false
            }
        }

        function controlVisible(): bool {
            return shell.controlOpen
        }

        function toggleTime(): void {
            shell.timeOpen = !shell.timeOpen
            if (shell.timeOpen) {
                shell.controlOpen = false
                shell.homeOpen = false
            }
        }

        function timeVisible(): bool {
            return shell.timeOpen
        }

        function openTools(): void {
            Quickshell.execDetached(["sh", "-lc", "~/.config/quickshell/scripts/utility-menu.sh"])
        }

        function toggleHome(): void {
            shell.homeOpen = !shell.homeOpen
            if (shell.homeOpen) {
                shell.controlOpen = false
                shell.timeOpen = false
            }
        }
    }
}
