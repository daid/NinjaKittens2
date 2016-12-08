// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM
import NinjaKittens 1.0 as NinjaKittens

import "Menus"

Column
{
    id: base;

    property int totalHeightHeader: childrenRect.height
    property int currentExtruderIndex: ExtruderManager.activeExtruderIndex;

    spacing: UM.Theme.getSize("default_margin").height

    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    UM.I18nCatalog { id: catalog; name:"cura" }
}
