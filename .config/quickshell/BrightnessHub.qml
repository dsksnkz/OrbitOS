import QtQuick
import Quickshell

PopupWindow {
    id: root

    property var anchorWindow
    property bool opened: false
    property int brightness: 50
    property int level: 50
    property real reveal: 0
    signal closeRequested()
    signal brightnessRequested(int target)

    function apply(target): void {
        level = Math.max(5, Math.min(100, Math.round(target)))
        brightnessRequested(level)
    }

    onBrightnessChanged: {
        if (!levelMouse.pressed)
            level = brightness
    }
    onOpenedChanged: {
        if (opened) {
            level = brightness
            reveal = 0
            revealAnimation.restart()
        }
    }

    anchor.window: root.anchorWindow
    anchor.rect.x: root.anchorWindow ? root.anchorWindow.width - width : 0
    anchor.rect.y: root.anchorWindow ? root.anchorWindow.height + 6 : 46
    implicitWidth: 350
    implicitHeight: 190
    visible: opened
    color: "transparent"

    NumberAnimation {
        id: revealAnimation
        target: root
        property: "reveal"
        from: 0
        to: 1
        duration: 220
        easing.type: Easing.OutBack
    }

    Rectangle {
        anchors.fill: parent
        radius: 3
        color: "#050505"
        border.width: 1
        border.color: "#686868"
        opacity: root.reveal
        scale: 0.97 + root.reveal * 0.03
        transform: Translate { y: (1 - root.reveal) * -10 }

        Column {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 12

            Row {
                width: parent.width
                height: 30
                Text {
                    width: parent.width - closeButton.width
                    anchors.verticalCenter: parent.verticalCenter
                    text: "ORBITOS  /  DISPLAY"
                    color: "#f5f5f5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
                BarButton {
                    id: closeButton
                    label: "󰅖"
                    compact: true
                    onClicked: root.closeRequested()
                }
            }

            Row {
                width: parent.width
                height: 24
                Text {
                    width: parent.width - levelText.width
                    text: "󰃠  MONITOR BRIGHTNESS"
                    color: "#a8a8a8"
                    font.family: "Inter"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }
                Text {
                    id: levelText
                    text: root.level + "%"
                    color: "#f5f5f5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 13
                    font.weight: Font.Bold
                }
            }

            Rectangle {
                id: levelTrack
                width: parent.width
                height: 28
                radius: 3
                color: "#101010"
                border.width: 1
                border.color: levelMouse.containsMouse ? "#777777" : "#303030"

                Rectangle {
                    anchors.left: parent.left
                    anchors.leftMargin: 4
                    anchors.verticalCenter: parent.verticalCenter
                    width: Math.max(8, (parent.width - 8) * root.level / 100)
                    height: 6
                    radius: 3
                    color: "#f5f5f5"
                    Behavior on width { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
                }
                Rectangle {
                    x: 4 + (parent.width - 16) * root.level / 100
                    anchors.verticalCenter: parent.verticalCenter
                    width: 9
                    height: 18
                    radius: 3
                    color: "#f5f5f5"
                    Behavior on x { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
                }
                MouseArea {
                    id: levelMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    function updateLevel(mouseX): void {
                        root.level = Math.max(5, Math.min(100, Math.round(mouseX / width * 100)))
                    }
                    onPressed: event => updateLevel(event.x)
                    onPositionChanged: event => { if (pressed) updateLevel(event.x) }
                    onReleased: root.apply(root.level)
                    onWheel: event => root.apply(root.level + (event.angleDelta.y > 0 ? 5 : -5))
                }
            }

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 7
                Repeater {
                    model: [25, 50, 75, 100]
                    BarButton {
                        required property int modelData
                        width: 72
                        label: modelData + "%"
                        active: Math.abs(root.level - modelData) < 3
                        onClicked: root.apply(modelData)
                    }
                }
            }
        }
    }
}
