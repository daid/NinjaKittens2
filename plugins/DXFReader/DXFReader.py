# Copyright (c) 2015 David Braam
# NinjaKittens is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshData import MeshData
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode

import math
import os

from . import DXFObjectReader
from . import DXFData
from . import NURBS


class DXFReader(MeshReader):
    def __init__(self):
        super(DXFReader, self).__init__()
        self._supported_extensions = [".dxf"]

        self._dxf = None
        self._mesh = None

    def read(self, file_name):
        self._dxf = DXFObjectReader.DXFObjectReader(open(file_name, "rt"))
        self._mesh = MeshData()
        for obj in self._dxf:
            if obj.getName() == "SECTION":
                if obj.get(2) == "ENTITIES":
                    self._handleEntities()
                elif obj.get(2) == "TABLES":
                    self._handleTables()
                else:
                    Logger.log("d", "DXF: Got unknown section: %s", obj.get(2))
                    for obj in self._dxf:
                        if obj.getName() == "ENDSEC":
                            break
                        else:
                            Logger.log("d", "DXF: %s", obj)
            elif obj.getName() == "EOF":
                pass
            else:
                Logger.log("e", "DXF: Unexpected object: %s", obj)

        self._mesh.calculateNormals()

        node = SceneNode()
        node.setMeshData(self._mesh)
        return node

    def _handleTables(self):
        for obj in self._dxf:
            if obj.getName() == "ENDSEC":
                break
            elif obj.getName() == "TABLE":
                if obj.get(2) == "":
                    pass
                else:
                    Logger.log("d", "DXF: Got unknown table: %s", obj.get(2))
                    for obj in self._dxf:
                        if obj.getName() == "ENDTAB":
                            break
                        else:
                            Logger.log("d", "DXF: %s", obj)
            else:
                Logger.log("e", "DXF: Unexpected object in tables section: %s", obj)

    def _handleEntities(self):
        for obj in self._dxf:
            if obj.getName() == "ENDSEC":
                break
            elif obj.getName() == "LINE":
                self._addLine(obj.get(10), obj.get(20), obj.get(11), obj.get(21))
            elif obj.getName() == "LWPOLYLINE":
                for n in range(0, obj.count(20) - 1):
                    self._addLine(obj.get(10, n), obj.get(20, n), obj.get(10, n + 1), obj.get(20, n + 1))
            elif obj.getName() == "ARC":
                cx = float(obj.get(10))
                cy = float(obj.get(20))
                r = float(obj.get(40))
                a_start = float(obj.get(50))
                a_end = float(obj.get(51))
                if a_end < a_start:
                    a_end += 360.0
                steps = math.ceil(((2.0 * math.pi * r) * (a_end - a_start) / 360.0) / 0.5)
                for n in range(0, steps):
                    a0 = a_start + (a_end - a_start) * n / steps
                    a1 = a_start + (a_end - a_start) * (n + 1) / steps
                    self._addLine(
                        cx + math.cos(math.radians(a0)) * r, cy + math.sin(math.radians(a0)) * r,
                        cx + math.cos(math.radians(a1)) * r, cy + math.sin(math.radians(a1)) * r
                    )
            elif obj.getName() == "CIRCLE":
                cx = float(obj.get(10))
                cy = float(obj.get(20))
                r = float(obj.get(40))
                steps = math.ceil((2.0 * math.pi * r) / 0.5)
                for n in range(0, steps):
                    a0 = 360.0 * n / steps
                    a1 = 360.0 * (n + 1) / steps
                    self._addLine(
                        cx + math.cos(math.radians(a0)) * r, cy + math.sin(math.radians(a0)) * r,
                        cx + math.cos(math.radians(a1)) * r, cy + math.sin(math.radians(a1)) * r
                    )
            elif obj.getName() == "ELLIPSE":
                cx = float(obj.get(10))
                cy = float(obj.get(20))
                emx = float(obj.get(11))
                emy = float(obj.get(21))
                r_major = math.sqrt(emx * emx + emy * emy)
                r_minor = r_major * float(obj.get(40))
                a_start = math.degrees(float(obj.get(41)))
                a_end = math.degrees(float(obj.get(42)))
                if a_end < a_start:
                    a_end += 360.0
                steps = math.ceil(((2.0 * math.pi * r) * (a_end - a_start) / 360.0) / 0.5)
                for n in range(0, steps):
                    a0 = a_start + (a_end - a_start) * n / steps
                    a1 = a_start + (a_end - a_start) * (n + 1) / steps
                    self._addLine(
                        cx + math.cos(math.radians(a0)) * r_major, cy + math.sin(math.radians(a0)) * r_minor,
                        cx + math.cos(math.radians(a1)) * r_major, cy + math.sin(math.radians(a1)) * r_minor
                    )
            elif obj.getName() == "SPLINE":
                nurbs = NURBS.NURBS(int(obj.get(71)))
                for n in range(0, obj.count(40)):
                    nurbs.addKnot(float(obj.get(40, n)))
                for n in range(0, obj.count(10)):
                    nurbs.addPoint(float(obj.get(10, n)), float(obj.get(20, n)))
                points = nurbs.calculate(2)
                distance = math.sqrt((points[0][0] - points[-1][0]) * (points[0][0] - points[-1][0]) + (points[0][1] - points[-1][1]) * (points[0][1] - points[-1][1]))
                if distance < 1.0:
                    point_count = int(max(2, distance / 0.1))
                elif distance < 5.0:
                    point_count = int(max(2, distance / 0.3))
                else:
                    point_count = int(max(2, distance / 0.5))
                points = nurbs.calculate(point_count)
                for n in range(0, len(points) - 1):
                    self._addLine(points[n][0], points[n][1], points[n + 1][0], points[n + 1][1])
            else:
                Logger.log("w", "DXF: Unknown entity: %s", str(obj))

    def _addLine(self, x0, y0, x1, y1):
        x0 = float(x0)
        x1 = float(x1)
        y0 = -float(y0)
        y1 = -float(y1)
        if x0 == x1 and y0 == y1:
            return
        self._mesh.addVertex(x0, 0, y0)
        self._mesh.addVertex(x1, 0, y1)
        self._mesh.addVertex(x1, 1, y1)
        self._mesh.addVertex(x0, 1, y0)
        self._mesh.addVertex(x1, 1, y1)
        self._mesh.addVertex(x0, 0, y0)
