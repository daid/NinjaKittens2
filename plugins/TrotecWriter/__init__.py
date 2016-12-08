# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import TrotecOutputDevicePlugin

from UM.i18n import i18nCatalog
catalog = i18nCatalog("nk")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Trotec Writer"),
            "author": "Daid",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Writes Trotec lasercut to a file"),
            "api": 3
        }
    }

def register(app):
    return { "output_device": TrotecOutputDevicePlugin.TrotecFileOutputDevicePlugin() }
