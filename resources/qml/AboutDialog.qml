// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    id: base

    //: About dialog title
    title: catalog.i18nc("@title:window","About NinjaKittens")
    minimumWidth: 400
    minimumHeight: 300;
    //UM.I18nCatalog { id: catalog; }


    Image
    {
        id: logo
        width: parent.width * 0.75
        height: width * (1/4.25)

        source: UM.Theme.images.logo

        sourceSize.width: width
        sourceSize.height: height
        anchors.centerIn: parent
        anchors.verticalCenterOffset : -(height * 0.5)
        UM.I18nCatalog{id: catalog; name:"nk"}
    }

    Label
    {
        id: version

        text: "NinjaKittens %1".arg(UM.Application.version)
        font: UM.Theme.fonts.large
        anchors.horizontalCenter : logo.horizontalCenter
        anchors.horizontalCenterOffset : (logo.width * 0.25)
        anchors.top: logo.bottom
        anchors.topMargin : 5
    }

    Label
    {
        id: description
        width: parent.width

        //: About dialog application description
        text: catalog.i18nc("@label","We have cookies.")
        wrapMode: Text.WordWrap
        anchors.top: version.bottom
        anchors.topMargin : 10
    }

    Label
    {
        id: author_note
        width: parent.width

        //: About dialog application author note
        text: catalog.i18nc("@info:credit","NinjaKittens has been developed by cats, and catlike creatures.")
        wrapMode: Text.WordWrap
        anchors.top: description.bottom
    }

    rightButtons: Button
    {
        //: Close about dialog button
        text: catalog.i18nc("@action:button","Close");

        onClicked: base.visible = false;
    }
}

