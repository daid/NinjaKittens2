# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import HtmlSvgOutputDevicePlugin

def getMetaData():
    return {
        "plugin": {
            "name": "HTML SVG Writer",
            "author": "Daid",
            "version": "1.0",
            "description": "Writes a HTML SVG file for debugging",
            "api": 3
        }
    }

def register(app):
    return { "output_device": HtmlSvgOutputDevicePlugin.HtmlSvgOutputDevicePlugin() }
