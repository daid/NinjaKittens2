// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.2 as UM
import NinjaKittens 1.0 as NinjaKittens

import "Menus"

UM.MainWindow
{
    id: base
    //: NinjaKittens application window title
    title: catalog.i18nc("@title:window","NinjaKittens2");
    viewportRect: Qt.rect(0, 0, (base.width - sidebar.width) / base.width, 1.0)
    property bool monitoringPrint: false
    Component.onCompleted:
    {
        Printer.setMinimumWindowSize(UM.Theme.getSize("window_minimum_size"))

        // Workaround silly issues with QML Action's shortcut property.
        //
        // Currently, there is no way to define shortcuts as "Application Shortcut".
        // This means that all Actions are "Window Shortcuts". The code for this
        // implements a rather naive check that just checks if any of the action's parents
        // are a window. Since the "Actions" object is a singleton it has no parent by
        // default. If we set its parent to something contained in this window, the
        // shortcut will activate properly because one of its parents is a window.
        //
        // This has been fixed for QtQuick Controls 2 since the Shortcut item has a context property.
        NinjaKittens.Actions.parent = backgroundItem
    }

    Item
    {
        id: backgroundItem;
        anchors.fill: parent;
        UM.I18nCatalog{id: catalog; name:"cura"}

        signal hasMesh(string name) //this signal sends the filebase name so it can be used for the JobSpecs.qml
        function getMeshName(path){
            //takes the path the complete path of the meshname and returns only the filebase
            var fileName = path.slice(path.lastIndexOf("/") + 1)
            var fileBase = fileName.slice(0, fileName.lastIndexOf("."))
            return fileBase
        }

        //DeleteSelection on the keypress backspace event
        Keys.onPressed: {
            if (event.key == Qt.Key_Backspace)
            {
                NinjaKittens.Actions.deleteSelection.trigger()
            }
        }

        UM.ApplicationMenu
        {
            id: menu
            window: base

            Menu
            {
                id: fileMenu
                title: catalog.i18nc("@title:menu menubar:toplevel","&File");

                MenuItem {
                    action: NinjaKittens.Actions.open;
                }

                RecentFilesMenu { }

                MenuSeparator { }

                MenuItem
                {
                    text: catalog.i18nc("@action:inmenu menubar:file", "&Save Selection to File");
                    enabled: UM.Selection.hasSelection;
                    iconName: "document-save-as";
                    onTriggered: UM.OutputDeviceManager.requestWriteSelectionToDevice("local_file", PrintInformation.jobName, { "filter_by_machine": false });
                }
                Menu
                {
                    id: saveAllMenu
                    title: catalog.i18nc("@title:menu menubar:file","Save &All")
                    iconName: "document-save-all";
                    enabled: devicesModel.rowCount() > 0 && UM.Backend.progress > 0.99;

                    Instantiator
                    {
                        model: UM.OutputDevicesModel { id: devicesModel; }

                        MenuItem
                        {
                            text: model.description;
                            onTriggered: UM.OutputDeviceManager.requestWriteToDevice(model.id, PrintInformation.jobName, { "filter_by_machine": false });
                        }
                        onObjectAdded: saveAllMenu.insertItem(index, object)
                        onObjectRemoved: saveAllMenu.removeItem(object)
                    }
                }

                MenuItem { action: NinjaKittens.Actions.reloadAll; }

                MenuSeparator { }

                MenuItem { action: NinjaKittens.Actions.quit; }
            }

            Menu
            {
                title: catalog.i18nc("@title:menu menubar:toplevel","&Edit");

                MenuItem { action: NinjaKittens.Actions.undo; }
                MenuItem { action: NinjaKittens.Actions.redo; }
                MenuSeparator { }
                MenuItem { action: NinjaKittens.Actions.selectAll; }
                MenuItem { action: NinjaKittens.Actions.deleteSelection; }
                MenuItem { action: NinjaKittens.Actions.deleteAll; }
                MenuItem { action: NinjaKittens.Actions.resetAllTranslation; }
                MenuItem { action: NinjaKittens.Actions.resetAll; }
                MenuSeparator { }
                MenuItem { action: NinjaKittens.Actions.groupObjects;}
                MenuItem { action: NinjaKittens.Actions.mergeObjects;}
                MenuItem { action: NinjaKittens.Actions.unGroupObjects;}
            }

            ViewMenu { title: catalog.i18nc("@title:menu", "&View") }

            Menu
            {
                id: extension_menu
                title: catalog.i18nc("@title:menu menubar:toplevel","E&xtensions");

                Instantiator
                {
                    id: extensions
                    model: UM.ExtensionModel { }

                    Menu
                    {
                        id: sub_menu
                        title: model.name;
                        visible: actions != null
                        enabled:actions != null
                        Instantiator
                        {
                            model: actions
                            MenuItem
                            {
                                text: model.text
                                onTriggered: extensions.model.subMenuTriggered(name, model.text)
                            }
                            onObjectAdded: sub_menu.insertItem(index, object)
                            onObjectRemoved: sub_menu.removeItem(object)
                        }
                    }

                    onObjectAdded: extension_menu.insertItem(index, object)
                    onObjectRemoved: extension_menu.removeItem(object)
                }
            }

            Menu
            {
                title: catalog.i18nc("@title:menu menubar:toplevel","P&references");

                MenuItem { action: NinjaKittens.Actions.preferences; }
            }

            Menu
            {
                //: Help menu
                title: catalog.i18nc("@title:menu menubar:toplevel","&Help");

                MenuItem { action: NinjaKittens.Actions.showEngineLog; }
                MenuItem { action: NinjaKittens.Actions.documentation; }
                MenuItem { action: NinjaKittens.Actions.reportBug; }
                MenuSeparator { }
                MenuItem { action: NinjaKittens.Actions.about; }
            }
        }

        UM.SettingPropertyProvider
        {
            id: machineExtruderCount

            containerStackId: NinjaKittens.MachineManager.activeMachineId
            key: "machine_extruder_count"
            watchedProperties: [ "value" ]
            storeIndex: 0
        }

        Item
        {
            id: contentItem;

            y: menu.height
            width: parent.width;
            height: parent.height - menu.height;

            Keys.forwardTo: menu

            DropArea
            {
                anchors.fill: parent;
                onDropped:
                {
                    if(drop.urls.length > 0)
                    {
                        for(var i in drop.urls)
                        {
                            UM.MeshFileHandler.readLocalFile(drop.urls[i]);
                            if (i == drop.urls.length - 1)
                            {
                                var meshName = backgroundItem.getMeshName(drop.urls[i].toString())
                                backgroundItem.hasMesh(decodeURIComponent(meshName))
                            }
                        }
                    }
                }
            }

            Loader
            {
                id: view_panel

                anchors.top: viewModeButton.bottom
                anchors.topMargin: UM.Theme.getSize("default_margin").height;
                anchors.left: viewModeButton.left;

                height: childrenRect.height;

                source: UM.ActiveView.valid ? UM.ActiveView.activeViewPanel : "";
            }

            Button
            {
                id: openFileButton;
                text: catalog.i18nc("@action:button","Open File");
                iconSource: UM.Theme.getIcon("load")
                style: UM.Theme.styles.tool_button
                tooltip: '';
                anchors
                {
                    top: parent.top;
                    left: parent.left;
                }
                action: NinjaKittens.Actions.open;
            }

            Image
            {
                id: logo
                anchors
                {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width;
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").height;
                }

                source: UM.Theme.getImage("logo");
                width: UM.Theme.getSize("logo").width;
                height: UM.Theme.getSize("logo").height;
                z: -1;

                sourceSize.width: width;
                sourceSize.height: height;
            }



            Toolbar
            {
                id: toolbar;

                property int mouseX: base.mouseX
                property int mouseY: base.mouseY

                anchors {
                    top: openFileButton.bottom;
                    topMargin: UM.Theme.getSize("window_margin").height;
                    left: parent.left;
                }
            }

            Sidebar
            {
                id: sidebar;

                anchors
                {
                    top: parent.top;
                    bottom: parent.bottom;
                    right: parent.right;
                }
                onMonitoringPrintChanged: base.monitoringPrint = monitoringPrint
                width: UM.Theme.getSize("sidebar").width;
            }

            Button
            {
                id: viewModeButton

                anchors
                {
                    top: toolbar.bottom;
                    topMargin: UM.Theme.getSize("window_margin").height;
                    left: parent.left;
                }
                text: catalog.i18nc("@action:button","View Mode");
                iconSource: UM.Theme.getIcon("viewmode");

                style: UM.Theme.styles.tool_button;
                tooltip: '';
                menu: ViewMenu { }
            }

            Rectangle
            {
                id: viewportOverlay

                color: UM.Theme.getColor("viewport_overlay")
                anchors
                {
                    top: parent.top
                    bottom: parent.bottom
                    left:parent.left
                    right: sidebar.left
                }
                visible: opacity > 0
                opacity: base.monitoringPrint ? 0.75 : 0

                Behavior on opacity { NumberAnimation { duration: 100; } }

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.AllButtons

                    onWheel: wheel.accepted = true
                }
            }

            Image
            {
                id: cameraImage
                width: Math.min(viewportOverlay.width, sourceSize.width)
                height: sourceSize.height * width / sourceSize.width
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenterOffset: - UM.Theme.getSize("sidebar").width / 2
                visible: base.monitoringPrint
                source: NinjaKittens.MachineManager.printerOutputDevices.length > 0 ? NinjaKittens.MachineManager.printerOutputDevices[0].cameraImage : ""
            }

            UM.MessageStack
            {
                anchors
                {
                    horizontalCenter: parent.horizontalCenter
                    horizontalCenterOffset: -(UM.Theme.getSize("sidebar").width/ 2)
                    top: parent.verticalCenter;
                    bottom: parent.bottom;
                }
            }
        }
    }

    UM.PreferencesDialog
    {
        id: preferences

        Component.onCompleted:
        {
            //; Remove & re-add the general page as we want to use our own instead of uranium standard.
            removePage(0);
            insertPage(0, catalog.i18nc("@title:tab","General"), Qt.resolvedUrl("Preferences/GeneralPage.qml"));

            removePage(1);
            insertPage(1, catalog.i18nc("@title:tab","Settings"), Qt.resolvedUrl("Preferences/SettingVisibilityPage.qml"));

            insertPage(2, catalog.i18nc("@title:tab", "Printers"), Qt.resolvedUrl("Preferences/MachinesPage.qml"));

            insertPage(3, catalog.i18nc("@title:tab", "Materials"), Qt.resolvedUrl("Preferences/MaterialsPage.qml"));

            insertPage(4, catalog.i18nc("@title:tab", "Profiles"), Qt.resolvedUrl("Preferences/ProfilesPage.qml"));

            //Force refresh
            setPage(0);
        }

        onVisibleChanged:
        {
            if(!visible)
            {
                // When the dialog closes, switch to the General page.
                // This prevents us from having a heavy page like Setting Visiblity active in the background.
                setPage(0);
            }
        }
    }

    Connections
    {
        target: NinjaKittens.Actions.preferences
        onTriggered: preferences.visible = true
    }

    Connections
    {
        target: NinjaKittens.Actions.addProfile
        onTriggered:
        {
            NinjaKittens.ContainerManager.createQualityChanges();
            preferences.setPage(4);
            preferences.show();

            // Show the renameDialog after a very short delay so the preference page has time to initiate
            showProfileNameDialogTimer.start();
        }
    }

    Connections
    {
        target: NinjaKittens.Actions.configureMachines
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(2);
        }
    }

    Connections
    {
        target: NinjaKittens.Actions.manageProfiles
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(4);
        }
    }

    Connections
    {
        target: NinjaKittens.Actions.manageMaterials
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(3)
        }
    }

    Connections
    {
        target: NinjaKittens.Actions.configureSettingVisibility
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(1);
            preferences.getCurrentItem().scrollToSection(source.key);
        }
    }

    Timer
    {
        id: showProfileNameDialogTimer
        repeat: false
        interval: 1

        onTriggered: preferences.getCurrentItem().showProfileNameDialog()
    }

    // BlurSettings is a way to force the focus away from any of the setting items.
    // We need to do this in order to keep the bindings intact.
    Connections
    {
        target: NinjaKittens.MachineManager
        onBlurSettings:
        {
            contentItem.focus = true
        }
    }

    Menu
    {
        id: objectContextMenu;

        property variant objectId: -1;
        MenuItem { action: NinjaKittens.Actions.centerObject; }
        MenuItem { action: NinjaKittens.Actions.deleteObject; }
        MenuItem { action: NinjaKittens.Actions.multiplyObject; }
        MenuSeparator { }
        MenuItem { action: NinjaKittens.Actions.selectAll; }
        MenuItem { action: NinjaKittens.Actions.deleteAll; }
        MenuItem { action: NinjaKittens.Actions.reloadAll; }
        MenuItem { action: NinjaKittens.Actions.resetAllTranslation; }
        MenuItem { action: NinjaKittens.Actions.resetAll; }
        MenuSeparator { }
        MenuItem { action: NinjaKittens.Actions.groupObjects; }
        MenuItem { action: NinjaKittens.Actions.mergeObjects; }
        MenuItem { action: NinjaKittens.Actions.unGroupObjects; }

        Connections
        {
            target: NinjaKittens.Actions.deleteObject
            onTriggered:
            {
                if(objectContextMenu.objectId != 0)
                {
                    Printer.deleteObject(objectContextMenu.objectId);
                    objectContextMenu.objectId = 0;
                }
            }
        }

        Connections
        {
            target: NinjaKittens.Actions.multiplyObject
            onTriggered:
            {
                if(objectContextMenu.objectId != 0)
                {
                    Printer.multiplyObject(objectContextMenu.objectId, 1);
                    objectContextMenu.objectId = 0;
                }
            }
        }

        Connections
        {
            target: NinjaKittens.Actions.centerObject
            onTriggered:
            {
                if(objectContextMenu.objectId != 0)
                {
                    Printer.centerObject(objectContextMenu.objectId);
                    objectContextMenu.objectId = 0;
                }
            }
        }
    }

    Menu
    {
        id: contextMenu;
        MenuItem { action: NinjaKittens.Actions.selectAll; }
        MenuItem { action: NinjaKittens.Actions.deleteAll; }
        MenuItem { action: NinjaKittens.Actions.reloadAll; }
        MenuItem { action: NinjaKittens.Actions.resetAllTranslation; }
        MenuItem { action: NinjaKittens.Actions.resetAll; }
        MenuSeparator { }
        MenuItem { action: NinjaKittens.Actions.groupObjects; }
        MenuItem { action: NinjaKittens.Actions.mergeObjects; }
        MenuItem { action: NinjaKittens.Actions.unGroupObjects; }
    }

    Connections
    {
        target: UM.Controller
        onContextMenuRequested:
        {
            if(objectId == 0)
            {
                contextMenu.popup();
            } else
            {
                objectContextMenu.objectId = objectId;
                objectContextMenu.popup();
            }
        }
    }

    Connections
    {
        target: NinjaKittens.Actions.quit
        onTriggered: base.visible = false;
    }

    Connections
    {
        target: NinjaKittens.Actions.toggleFullScreen
        onTriggered: base.toggleFullscreen();
    }

    FileDialog
    {
        id: openDialog;

        //: File open dialog title
        title: catalog.i18nc("@title:window","Open file")
        modality: UM.Application.platform == "linux" ? Qt.NonModal : Qt.WindowModal;
        //TODO: Support multiple file selection, workaround bug in KDE file dialog
        //selectMultiple: true
        nameFilters: UM.MeshFileHandler.supportedReadFileTypes;
        folder: CuraApplication.getDefaultPath("dialog_load_path")
        onAccepted:
        {
            //Because several implementations of the file dialog only update the folder
            //when it is explicitly set.
            var f = folder;
            folder = f;

            CuraApplication.setDefaultPath("dialog_load_path", folder);
            UM.MeshFileHandler.readLocalFile(fileUrl)
            var meshName = backgroundItem.getMeshName(fileUrl.toString())
            backgroundItem.hasMesh(decodeURIComponent(meshName))
        }
    }

    Connections
    {
        target: NinjaKittens.Actions.open
        onTriggered: openDialog.open()
    }

    EngineLog
    {
        id: engineLog;
    }

    Connections
    {
        target: NinjaKittens.Actions.showEngineLog
        onTriggered: engineLog.visible = true;
    }

    AddMachineDialog
    {
        id: addMachineDialog
        onMachineAdded:
        {
            machineActionsWizard.firstRun = addMachineDialog.firstRun
            machineActionsWizard.start(id)
        }
    }

    // Dialog to handle first run machine actions
    UM.Wizard
    {
        id: machineActionsWizard;

        title: catalog.i18nc("@title:window", "Add Printer")
        property var machine;

        function start(id)
        {
            var actions =  NinjaKittens.MachineActionManager.getFirstStartActions(id)
            resetPages() // Remove previous pages

            for (var i = 0; i < actions.length; i++)
            {
                actions[i].displayItem.reset()
                machineActionsWizard.appendPage(actions[i].displayItem, catalog.i18nc("@title", actions[i].label));
            }

            //Only start if there are actions to perform.
            if (actions.length > 0)
            {
                machineActionsWizard.currentPage = 0;
                show()
            }
        }
    }

    MessageDialog
    {
        id: messageDialog
        modality: Qt.ApplicationModal
        onAccepted: Printer.messageBoxClosed(clickedButton)
        onApply: Printer.messageBoxClosed(clickedButton)
        onDiscard: Printer.messageBoxClosed(clickedButton)
        onHelp: Printer.messageBoxClosed(clickedButton)
        onNo: Printer.messageBoxClosed(clickedButton)
        onRejected: Printer.messageBoxClosed(clickedButton)
        onReset: Printer.messageBoxClosed(clickedButton)
        onYes: Printer.messageBoxClosed(clickedButton)
    }

    Connections
    {
        target: Printer
        onShowMessageBox:
        {
            messageDialog.title = title
            messageDialog.text = text
            messageDialog.informativeText = informativeText
            messageDialog.detailedText = detailedText
            messageDialog.standardButtons = buttons
            messageDialog.icon = icon
            messageDialog.visible = true
        }
    }

    Connections
    {
        target: NinjaKittens.Actions.addMachine
        onTriggered: addMachineDialog.visible = true;
    }

    AboutDialog
    {
        id: aboutDialog
    }

    Connections
    {
        target: NinjaKittens.Actions.about
        onTriggered: aboutDialog.visible = true;
    }

    Connections
    {
        target: Printer
        onRequestAddPrinter:
        {
            addMachineDialog.visible = true
            addMachineDialog.firstRun = false
        }
    }

    Timer
    {
        id: startupTimer;
        interval: 100;
        repeat: false;
        running: true;
        onTriggered:
        {
            if(!base.visible)
            {
                base.visible = true;
                restart();
            }
            else if(NinjaKittens.MachineManager.activeMachineId == null || NinjaKittens.MachineManager.activeMachineId == "")
            {
                addMachineDialog.open();
            }
        }
    }
}

