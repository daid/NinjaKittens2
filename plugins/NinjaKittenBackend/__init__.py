# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

#Shoopdawoop
from . import NinjaKittensBackend

from UM.i18n import i18nCatalog
catalog = i18nCatalog("nk")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "NinjaKittens Backend"),
            "author": "Daid",
            "description": catalog.i18nc("@info:whatsthis", "Provides the NinjaKittens backend"),
            "api": 2
        }
    }

def register(app):
    return { "backend": NinjaKittensBackend.NinjaKittensBackend() }

