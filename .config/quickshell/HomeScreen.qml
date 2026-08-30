import QtQuick
import Quickshell

PopupWindow {
    id: root

    property var anchorWindow
    property bool opened: false
    property real reveal: 0
    property var pendingCommand: []
    signal closeRequested()
    signal controlRequested()

    function launch(command): void {
        pendingCommand = command
        closeRequested()
        launchDelay.restart()
    }

    anchor.window: root.anchorWindow
    anchor.rect.x: -6
    anchor.rect.y: -6
    implicitWidth: root.anchorWindow ? root.anchorWindow.screen.width : 1200
    implicitHeight: root.anchorWindow ? root.anchorWindow.screen.height : 800
    visible: opened
    color: "transparent"

    onOpenedChanged: {
        if (opened) {
            reveal = 0
            revealAnimation.restart()
        }
    }

    Timer {
        id: launchDelay
        interval: 100
        onTriggered: Quickshell.execDetached(root.pendingCommand)
    }

    SystemClock {
        id: clock
        precision: SystemClock.Seconds
    }

    NumberAnimation {
        id: revealAnimation
        target: root
        property: "reveal"
        from: 0
        to: 1
        duration: 420
        easing.type: Easing.OutCubic
    }

    Rectangle {
        anchors.fill: parent
        radius: 3
        color: "#030303"
        border.width: 1
        border.color: "#343434"
        opacity: root.reveal

        MouseArea {
            anchors.fill: parent
            onClicked: root.closeRequested()
        }

        Item {
            id: orbit
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: -72
            width: 480
            height: 480
            opacity: 0.75

            Repeater {
                model: [310, 390, 470]
                Rectangle {
                    required property int modelData
                    anchors.centerIn: parent
                    width: modelData
                    height: modelData
                    radius: width / 2
                    color: "transparent"
                    border.width: 1
                    border.color: modelData === 390 ? "#252525" : "#151515"
                }
            }

            Item {
                anchors.fill: parent
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 45
                    width: 7
                    height: 7
                    radius: 4
                    color: "#f5f5f5"
                }
                RotationAnimator on rotation {
                    from: 0
                    to: 360
                    duration: 32000
                    loops: Animation.Infinite
                    running: root.opened
                }
            }

            Item {
                anchors.centerIn: parent
                width: 390
                height: 390
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    width: 5
                    height: 5
                    radius: 3
                    color: "#777777"
                }
                RotationAnimator on rotation {
                    from: 360
                    to: 0
                    duration: 48000
                    loops: Animation.Infinite
                    running: root.opened
                }
            }
        }

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: -85
            spacing: 8

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatDateTime(clock.date, "HH:mm")
                color: "#f5f5f5"
                font.family: "Inter"
                font.pixelSize: 88
                font.weight: Font.Light
                font.letterSpacing: -3
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatDateTime(clock.date, "dddd, d MMMM")
                color: "#b8b8b8"
                font.family: "Inter"
                font.pixelSize: 17
                font.weight: Font.Medium
            }
            Item { width: 1; height: 26 }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Welcome home."
                color: "#f5f5f5"
                font.family: "Inter"
                font.pixelSize: 23
                font.weight: Font.DemiBold
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Everything is where you left it."
                color: "#737373"
                font.family: "Inter"
                font.pixelSize: 12
            }
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 54
            spacing: 8

            Repeater {
                model: [
                    { icon: "󰀻", label: "Applications", command: ["rofi", "-show", "drun"] },
                    { icon: "󰉋", label: "Files", command: ["nautilus"] },
                    { icon: "󰆍", label: "Terminal", command: ["kitty"] },
                    { icon: "󰒓", label: "Control", command: [] },
                    { icon: "󰌾", label: "Lock", command: ["hyprlock"] }
                ]

                Rectangle {
                    required property var modelData
                    width: 112
                    height: 58
                    radius: 3
                    color: homeMouse.containsMouse ? "#f5f5f5" : "#0d0d0d"
                    border.width: 1
                    border.color: homeMouse.containsMouse ? "#f5f5f5" : "#343434"
                    scale: homeMouse.pressed ? 0.97 : 1

                    Column {
                        anchors.centerIn: parent
                        spacing: 3
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: modelData.icon
                            color: homeMouse.containsMouse ? "#050505" : "#f5f5f5"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 17
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: modelData.label
                            color: homeMouse.containsMouse ? "#050505" : "#a8a8a8"
                            font.family: "Inter"
                            font.pixelSize: 10
                            font.weight: Font.DemiBold
                        }
                    }
                    MouseArea {
                        id: homeMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (modelData.label === "Control") {
                                root.closeRequested()
                                root.controlRequested()
                            } else {
                                root.launch(modelData.command)
                            }
                        }
                    }
                    Behavior on color { ColorAnimation { duration: 160 } }
                    Behavior on border.color { ColorAnimation { duration: 160 } }
                    Behavior on scale { NumberAnimation { duration: 90 } }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 20
            text: "ORBITOS  ·  UX FIRST"
            color: "#4f4f4f"
            font.family: "JetBrainsMono Nerd Font"
            font.pixelSize: 9
            font.letterSpacing: 2
        }

        BarButton {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: 16
            label: "󰅖"
            compact: true
            onClicked: root.closeRequested()
        }
    }
}
