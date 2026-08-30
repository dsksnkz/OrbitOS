import QtQuick
import Quickshell
import Quickshell.Io

PopupWindow {
    id: root

    property var anchorWindow
    property bool opened: false
    property int monthOffset: 0
    property string nextAlarm: "No alarms scheduled"
    property real reveal: 0
    signal closeRequested()

    function shownMonth(): var {
        const now = clock.date
        return new Date(now.getFullYear(), now.getMonth() + monthOffset, 1)
    }

    function cellDate(index): var {
        const month = shownMonth()
        const mondayOffset = (month.getDay() + 6) % 7
        return new Date(month.getFullYear(), month.getMonth(), index - mondayOffset + 1)
    }

    function sameDay(a, b): bool {
        return a.getFullYear() === b.getFullYear()
            && a.getMonth() === b.getMonth()
            && a.getDate() === b.getDate()
    }

    function runAction(command): void {
        Quickshell.execDetached(command)
    }

    onOpenedChanged: {
        if (opened) {
            reveal = 0
            monthOffset = 0
            alarmStatus.running = true
            revealAnimation.restart()
        }
    }

    anchor.window: root.anchorWindow
    anchor.rect.x: root.anchorWindow ? (root.anchorWindow.width - width) / 2 : 0
    anchor.rect.y: root.anchorWindow ? root.anchorWindow.height + 6 : 46
    implicitWidth: 430
    implicitHeight: 558
    visible: opened
    color: "transparent"

    SystemClock {
        id: clock
        precision: SystemClock.Seconds
    }

    Process {
        id: alarmStatus
        command: [Quickshell.shellPath("scripts/alarm.py"), "next"]
        stdout: SplitParser {
            onRead: data => root.nextAlarm = data.trim() || "No alarms scheduled"
        }
    }

    Timer {
        interval: 15000
        running: root.opened
        repeat: true
        onTriggered: alarmStatus.running = true
    }

    NumberAnimation {
        id: revealAnimation
        target: root
        property: "reveal"
        from: 0
        to: 1
        duration: 260
        easing.type: Easing.OutBack
    }

    Rectangle {
        id: card
        anchors.fill: parent
        radius: 3
        color: "#050505"
        border.width: 1
        border.color: "#f5f5f5"
        opacity: root.reveal
        scale: 0.96 + root.reveal * 0.04
        transform: Translate { y: (1 - root.reveal) * -14 }

        SequentialAnimation on border.color {
            running: root.opened
            loops: Animation.Infinite
            ColorAnimation { to: "#555555"; duration: 2400; easing.type: Easing.InOutSine }
            ColorAnimation { to: "#f5f5f5"; duration: 2400; easing.type: Easing.InOutSine }
        }

        Column {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 10

            Row {
                width: parent.width
                height: 34
                Text {
                    width: parent.width - closeButton.width
                    anchors.verticalCenter: parent.verticalCenter
                    text: "MAGNETISM  /  TIME"
                    color: "#f5f5f5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 13
                    font.weight: Font.Bold
                }
                BarButton {
                    id: closeButton
                    label: "󰅖"
                    compact: true
                    onClicked: root.closeRequested()
                }
            }

            Item {
                width: parent.width
                height: 100

                Item {
                    id: orbit
                    width: 82
                    height: 82
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter

                    Rectangle {
                        anchors.fill: parent
                        radius: 41
                        color: "#090909"
                        border.width: 1
                        border.color: "#383838"
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: 60
                        height: 60
                        radius: 30
                        color: "transparent"
                        border.width: 1
                        border.color: "#202020"
                    }
                    Item {
                        anchors.fill: parent
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 2
                            width: 7
                            height: 7
                            radius: 4
                            color: "#f5f5f5"
                        }
                        RotationAnimator on rotation {
                            from: 0
                            to: 360
                            duration: 14000
                            loops: Animation.Infinite
                            running: root.opened
                        }
                    }
                    Text {
                        anchors.centerIn: parent
                        text: Qt.formatDateTime(clock.date, "ss")
                        color: "#777777"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 11
                    }
                }

                Column {
                    anchors.left: orbit.right
                    anchors.leftMargin: 18
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    Text {
                        text: Qt.formatDateTime(clock.date, "HH:mm")
                        color: "#f5f5f5"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 34
                        font.weight: Font.Bold
                    }
                    Text {
                        text: Qt.formatDateTime(clock.date, "dddd, d MMMM yyyy")
                        color: "#8a8a8a"
                        font.family: "Inter"
                        font.pixelSize: 11
                    }
                    Text {
                        width: parent.width
                        text: "󰀠  " + root.nextAlarm
                        color: "#c9c9c9"
                        elide: Text.ElideRight
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 10
                    }
                }
            }

            Rectangle { width: parent.width; height: 1; color: "#303030" }

            Row {
                width: parent.width
                height: 32
                BarButton {
                    label: "󰅁"
                    compact: true
                    onClicked: root.monthOffset--
                }
                Text {
                    width: parent.width - 64
                    anchors.verticalCenter: parent.verticalCenter
                    horizontalAlignment: Text.AlignHCenter
                    text: Qt.formatDateTime(root.shownMonth(), "MMMM yyyy").toUpperCase()
                    color: "#f5f5f5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
                BarButton {
                    label: "󰅂"
                    compact: true
                    onClicked: root.monthOffset++
                }
            }

            Grid {
                width: parent.width
                columns: 7
                columnSpacing: 3
                rowSpacing: 3

                Repeater {
                    model: ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
                    Text {
                        required property string modelData
                        width: 54
                        height: 18
                        text: modelData
                        color: "#666666"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 9
                        font.weight: Font.Bold
                    }
                }

                Repeater {
                    model: 42
                    Rectangle {
                        required property int index
                        readonly property var dateValue: root.cellDate(index)
                        readonly property bool inMonth: dateValue.getMonth() === root.shownMonth().getMonth()
                        readonly property bool today: root.sameDay(dateValue, clock.date)

                        width: 54
                        height: 30
                        radius: 3
                        color: today ? "#f5f5f5" : (dayMouse.containsMouse ? "#1f1f1f" : "transparent")
                        border.width: today ? 0 : 1
                        border.color: inMonth ? "#222222" : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: parent.dateValue.getDate()
                            color: parent.today ? "#050505" : (parent.inMonth ? "#d0d0d0" : "#454545")
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 10
                            font.weight: parent.today ? Font.Bold : Font.Medium
                        }
                        MouseArea {
                            id: dayMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                        }
                        Behavior on color { ColorAnimation { duration: 120 } }
                    }
                }
            }

            Rectangle { width: parent.width; height: 1; color: "#303030" }

            Grid {
                anchors.horizontalCenter: parent.horizontalCenter
                columns: 3
                columnSpacing: 7
                rowSpacing: 7

                BarButton { width: 124; label: "󰃰 Alarm"; onClicked: root.runAction([Quickshell.shellPath("scripts/alarm.py"), "add"]) }
                BarButton { width: 124; label: "󰔛 Timer"; onClicked: root.runAction(["sh", "-lc", "~/.config/quickshell/scripts/timer.sh"]) }
                BarButton { width: 124; label: "󰀠 Alarms"; onClicked: root.runAction([Quickshell.shellPath("scripts/alarm.py"), "manage"]) }
                BarButton { width: 124; label: "󰅍 Copy time"; onClicked: root.runAction([Quickshell.shellPath("scripts/alarm.py"), "copy-time"]) }
                BarButton { width: 124; label: "󰅍 Copy date"; onClicked: root.runAction([Quickshell.shellPath("scripts/alarm.py"), "copy-date"]) }
                BarButton { width: 124; label: "󰂛 Focus"; onClicked: root.runAction(["sh", "-lc", "~/.config/quickshell/scripts/dnd-toggle.sh"]) }
            }
        }
    }
}
