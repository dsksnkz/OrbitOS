import QtQuick

Rectangle {
    id: root

    property string label: ""
    property string hint: ""
    property bool active: false
    property bool compact: false
    signal clicked(int button)
    signal wheel(int delta)

    implicitWidth: Math.max(compact ? 28 : 34, textItem.implicitWidth + (compact ? 10 : 16))
    implicitHeight: 28
    radius: 3
    scale: mouse.pressed ? 0.92 : (mouse.containsMouse ? 1.025 : 1.0)
    color: active ? "#f5f5f5" : (mouse.containsMouse ? "#242424" : "#101010")
    border.width: active ? 0 : 1
    border.color: mouse.containsMouse ? "#f5f5f5" : "#3a3a3a"

    Text {
        id: textItem
        anchors.centerIn: parent
        text: root.label
        color: root.active ? "#050505" : "#f5f5f5"
        font.family: "JetBrainsMono Nerd Font"
        font.pixelSize: 12
        font.weight: root.active ? Font.DemiBold : Font.Medium
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: event => root.clicked(event.button)
        onWheel: event => root.wheel(event.angleDelta.y)
    }

    Behavior on color { ColorAnimation { duration: 150; easing.type: Easing.OutCubic } }
    Behavior on border.color { ColorAnimation { duration: 150; easing.type: Easing.OutCubic } }
    Behavior on implicitWidth { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }
    Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutBack } }
}
