# Copyright (c) 2015 David Braam
# NinjaKittens is released under the terms of the AGPLv3 or higher.

from . import DXFReader

def getMetaData():
    return {
        "plugin": {
            "name": "DXF Reader",
            "author": "Daid",
            "version": "1.0",
            "description": "Provides support for reading DXF files.",
            "api": 3
        },
        "mesh_reader": [
            {
                "extension": "dxf",
                "description": "DXF File"
            }
        ]
    }

def register(app):
    return { "mesh_reader": DXFReader.DXFReader() }
