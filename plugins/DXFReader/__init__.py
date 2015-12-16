# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from . import DXFReader

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("nk")

def getMetaData():
    return {
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "DXF Reader"),
            "author": "Daid",
            "version": "1.0",
            "description": i18n_catalog.i18nc("@info:whatsthis", "Provides support for reading DXF files."),
            "api": 2
        },
        "mesh_reader": {
            "extension": "dxf",
            "description": i18n_catalog.i18nc("@item:inlistbox", "DXF File")
        }
    }

def register(app):
    return { "mesh_reader": DXFReader.DXFReader() }
