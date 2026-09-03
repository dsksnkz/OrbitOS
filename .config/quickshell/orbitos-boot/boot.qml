//@ pragma ShellId orbitos-boot
//@ pragma DropExpensiveFonts

import QtQuick
import Quickshell

ShellRoot {
    id: shell

    // A single clock drives every effect, keeping the handoff exactly seven seconds.
    property real elapsed: 0
    property bool finishing: elapsed >= 6500

    function clamp(value, minimum, maximum): real {
        return Math.max(minimum, Math.min(maximum, value))
    }

    function span(start, end): real {
        return clamp((elapsed - start) / (end - start), 0, 1)
    }

    function smooth(start, end): real {
        const value = span(start, end)
        return value * value * (3 - 2 * value)
    }

    function exit(): void {
        handoff.stop()
        Qt.quit()
    }

    NumberAnimation on elapsed {
        id: timeline
        from: 0
        to: 7000
        duration: 7000
        easing.type: Easing.Linear
        running: true
    }

    Timer {
        id: handoff
        interval: 7000
        running: true
        onTriggered: shell.exit()
    }

    Variants {
        model: Quickshell.screens

        PanelWindow {
            id: window
            required property var modelData

            screen: modelData
            color: "#000000"
            exclusiveZone: -1
            aboveWindows: true
            focusable: false

            anchors {
                top: true
                right: true
                bottom: true
                left: true
            }

            Rectangle {
                anchors.fill: parent
                color: "#000000"

                // Subtle perspective grid: the machine's visual field comes online first.
                Item {
                    id: grid
                    anchors.fill: parent
                    opacity: shell.span(80, 900) * (1 - shell.span(6100, 6850)) * 0.34

                    Repeater {
                        model: 29
                        Rectangle {
                            required property int index
                            x: parent.width / 2 + (index - 14) * parent.width / 28
                                * (0.58 + 0.42 * shell.span(0, 900))
                            y: parent.height * 0.12
                            width: 1
                            height: parent.height * 0.76
                            color: index % 7 === 0 ? "#5c6570" : "#24282d"
                            opacity: 0.25 + 0.55 * Math.abs(Math.sin(shell.elapsed / 390 + index))
                            transform: Rotation {
                                origin.x: 0
                                origin.y: height
                                angle: (index - 14) * 0.34
                            }
                        }
                    }

                    Repeater {
                        model: 18
                        Rectangle {
                            required property int index
                            x: parent.width * 0.12
                            y: parent.height / 2 + (index - 9) * (15 + index * 2.5)
                            width: parent.width * 0.76
                            height: 1
                            color: index % 5 === 0 ? "#515862" : "#202328"
                            opacity: 0.18 + 0.5 * Math.abs(Math.sin(shell.elapsed / 460 + index * 0.7))
                        }
                    }
                }

                // Fast boot streaks cross the screen at different phases.
                Repeater {
                    model: 22
                    Rectangle {
                        required property int index
                        readonly property real seed: Math.abs(Math.sin((index + 2) * 91.73))
                        readonly property real local: (shell.elapsed / (900 + seed * 900) + seed) % 1
                        x: index % 2 === 0 ? local * window.width : window.width * (1 - local)
                        y: window.height * (0.08 + seed * 0.84)
                        width: 34 + seed * 160
                        height: index % 5 === 0 ? 2 : 1
                        radius: 1
                        color: index % 6 === 0 ? "#ffffff" : "#8b96a3"
                        opacity: shell.span(120, 600) * (1 - shell.span(2350, 3000))
                            * (0.12 + seed * 0.48)
                        scale: 0.5 + shell.span(100, 2100)
                    }
                }

                Item {
                    id: core
                    anchors.centerIn: parent
                    width: Math.min(window.width, window.height) * 0.58
                    height: width
                    scale: 0.62 + shell.smooth(300, 2300) * 0.38
                    opacity: (shell.span(180, 700) - shell.span(6250, 6950))

                    // A restrained bloom made from nested translucent discs.
                    Repeater {
                        model: 9
                        Rectangle {
                            required property int index
                            anchors.centerIn: parent
                            width: 26 + index * 34 + shell.smooth(400, 2100) * index * 6
                            height: width
                            radius: width / 2
                            color: "transparent"
                            border.width: index < 3 ? 2 : 1
                            border.color: index % 3 === 0 ? "#dde7f2" : "#65717e"
                            opacity: (0.78 - index * 0.065)
                                * (0.42 + 0.58 * Math.abs(Math.sin(shell.elapsed / (240 + index * 67) + index)))
                            scale: 0.88 + Math.sin(shell.elapsed / (310 + index * 31)) * 0.025
                        }
                    }

                    // Counter-rotating broken rings imply a system assembling itself.
                    Repeater {
                        model: 4
                        Item {
                            required property int index
                            anchors.centerIn: parent
                            width: 178 + index * 76
                            height: width
                            rotation: (index % 2 === 0 ? 1 : -1)
                                * shell.elapsed * (0.025 + index * 0.009)

                            Repeater {
                                model: 16
                                Rectangle {
                                    required property int index
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    y: 0
                                    width: index % 4 === 0 ? 17 : 7
                                    height: 2
                                    radius: 1
                                    color: index % 5 === 0 ? "#ffffff" : "#7f8a96"
                                    opacity: index % 3 === 0 ? 0.95 : 0.38
                                    transform: Rotation {
                                        origin.x: width / 2
                                        origin.y: parent.parent.height / 2
                                        angle: index * 22.5
                                    }
                                }
                            }
                        }
                    }

                    // Radial data particles accelerate into the central reactor.
                    Repeater {
                        model: 56
                        Item {
                            required property int index
                            readonly property real angle: index * 137.508
                            readonly property real seed: Math.abs(Math.sin(index * 17.17 + 2))
                            readonly property real radiusNow: (1 - shell.smooth(520 + seed * 600, 2500))
                                * (core.width * (0.43 + seed * 0.42)) + 34
                            anchors.centerIn: parent
                            width: 3
                            height: radiusNow * 2
                            rotation: angle + shell.elapsed * (index % 2 ? 0.018 : -0.013)

                            Rectangle {
                                anchors.horizontalCenter: parent.horizontalCenter
                                y: 0
                                width: index % 9 === 0 ? 5 : 2
                                height: width
                                radius: width / 2
                                color: index % 11 === 0 ? "#ffffff" : "#8995a2"
                                opacity: 0.28 + parent.seed * 0.72
                            }
                        }
                    }

                    Rectangle {
                        anchors.centerIn: parent
                        width: 20 + shell.smooth(900, 2800) * 58
                        height: width
                        radius: width / 2
                        color: "#f7fbff"
                        opacity: 0.55 + 0.42 * Math.abs(Math.sin(shell.elapsed / 105))
                        scale: shell.elapsed > 5700 ? 1 + shell.smooth(5700, 6450) * 9 : 1
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: 4
                        height: 4
                        radius: 2
                        color: "#ffffff"
                        scale: 1 + shell.smooth(800, 2500) * 5
                    }
                }

                // Four acquisition brackets lock onto the core.
                Item {
                    anchors.centerIn: parent
                    width: Math.min(window.width, window.height) * 0.39
                    height: width
                    opacity: shell.span(900, 1450) * (1 - shell.span(5300, 6050))
                    scale: 1.38 - shell.smooth(700, 1800) * 0.38

                    Repeater {
                        model: 4
                        Item {
                            required property int index
                            anchors.centerIn: parent
                            width: parent.width
                            height: parent.height
                            rotation: index * 90
                            Rectangle {
                                x: 0
                                y: 0
                                width: 54
                                height: 2
                                color: "#aeb8c3"
                            }
                            Rectangle {
                                x: 0
                                y: 0
                                width: 2
                                height: 54
                                color: "#aeb8c3"
                            }
                        }
                    }
                }

                // White ignition flash transitions from machinery to identity.
                Rectangle {
                    anchors.fill: parent
                    color: "#f6f9fc"
                    opacity: shell.elapsed < 2920 ? shell.span(2750, 2920)
                        : (1 - shell.span(2920, 3300))
                }

                Column {
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 2
                    spacing: 8
                    opacity: shell.span(3100, 3550) * (1 - shell.span(6200, 6860))
                    scale: 0.91 + shell.smooth(3050, 3900) * 0.09

                    Row {
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: 20

                        Item {
                            width: 62
                            height: 62
                            anchors.verticalCenter: parent.verticalCenter
                            Rectangle {
                                anchors.centerIn: parent
                                width: 58
                                height: 58
                                radius: 29
                                color: "transparent"
                                border.width: 2
                                border.color: "#f4f7fa"
                            }
                            Rectangle {
                                anchors.centerIn: parent
                                width: 26
                                height: 26
                                radius: 13
                                color: "#f4f7fa"
                            }
                            Rectangle {
                                anchors.horizontalCenter: parent.horizontalCenter
                                y: -2
                                width: 5
                                height: 12
                                radius: 3
                                color: "#050607"
                                transform: Rotation {
                                    origin.x: 2.5
                                    origin.y: 33
                                    angle: shell.elapsed * 0.055
                                }
                            }
                        }

                        Text {
                            text: "ORBITOS"
                            color: "#f7f9fb"
                            font.family: "Inter"
                            font.pixelSize: Math.min(72, window.width * 0.054)
                            font.weight: Font.DemiBold
                            font.letterSpacing: 12
                            renderType: Text.NativeRendering
                        }
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: shell.elapsed < 4400 ? "INITIALIZING ORBITAL ENVIRONMENT"
                            : shell.elapsed < 5350 ? "DISPLAY  •  AUDIO  •  NETWORK  •  MOTION"
                            : "SYSTEM READY"
                        color: shell.elapsed >= 5350 ? "#ffffff" : "#7f8993"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 11
                        font.weight: Font.Medium
                        font.letterSpacing: 3
                    }

                    Item { width: 1; height: 18 }

                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: Math.min(480, window.width * 0.43)
                        height: 2
                        color: "#20252a"

                        Rectangle {
                            width: parent.width * shell.smooth(3300, 5700)
                            height: parent.height
                            color: "#f5f7fa"
                        }
                        Rectangle {
                            x: Math.max(0, parent.width * shell.smooth(3300, 5700) - 18)
                            width: 18
                            height: parent.height
                            color: "#ffffff"
                            opacity: 0.95
                        }
                    }
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 54
                    spacing: 18
                    opacity: shell.span(3400, 3900) * (1 - shell.span(5950, 6500))

                    Repeater {
                        model: ["CORE", "GRAPHICS", "LINK", "SHELL"]
                        Column {
                            required property string modelData
                            spacing: 6
                            Rectangle {
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: 82
                                height: 1
                                color: "#31373d"
                                Rectangle {
                                    width: parent.width * shell.smooth(3500, 5000)
                                    height: 1
                                    color: "#bac4ce"
                                }
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData
                                color: "#59616a"
                                font.family: "JetBrainsMono Nerd Font"
                                font.pixelSize: 8
                                font.letterSpacing: 1.5
                            }
                        }
                    }
                }

                Text {
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.rightMargin: 22
                    anchors.bottomMargin: 18
                    text: "CLICK TO SKIP"
                    color: "#40464c"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 8
                    font.letterSpacing: 1
                    opacity: shell.span(1000, 1500) * (1 - shell.span(5600, 6200))
                }

                // Final luminance surge, then fade to black before releasing the desktop.
                Rectangle {
                    anchors.fill: parent
                    color: "#ffffff"
                    opacity: shell.elapsed < 6250 ? 0
                        : shell.elapsed < 6450 ? shell.span(6250, 6450) * 0.92
                        : (1 - shell.span(6450, 6860)) * 0.92
                }
                Rectangle {
                    anchors.fill: parent
                    color: "#000000"
                    opacity: shell.span(6750, 7000)
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (shell.elapsed > 600)
                            shell.exit()
                    }
                }
            }
        }
    }
}
