import base64
import zlib
import os

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger

from nk import Paths


class TrotecFileWriter(MeshWriter):
    def __init__(self, filename):
        super().__init__()
        self._dpi = 333.0
        self._max_y = None
        self._max_x = None
        self._min_y = None
        self._min_x = None
        self._family_id = 0
        self._filename = filename

    def write(self, stream, node, mode=MeshWriter.OutputMode.BinaryMode):
        if mode != MeshWriter.OutputMode.BinaryMode:
            Logger.log("e", "GCode Writer does not support non-text mode")
            return False

        engrave_paths = None
        cut_paths = None
        for node in DepthFirstIterator(node):
            if node.hasDecoration("getCutPaths"):
                cut_paths = node.callDecoration("getCutPaths")
            if node.hasDecoration("getEngravePaths"):
                engrave_paths = node.callDecoration("getEngravePaths")

        self._min_x = 10000000000
        self._max_x = -10000000000
        self._min_y = 10000000000
        self._max_y = -10000000000
        self._family_id = 0
        for path in engrave_paths.open_paths:
            self._processPathMinMax(path)
        for path in engrave_paths.closed_paths:
            self._processPathMinMax(path)
        for path in cut_paths.open_paths:
            self._processPathMinMax(path)
        for path in cut_paths.closed_paths:
            self._processPathMinMax(path)

        self._writeTag(stream, "!-- Version:Driver 10.5.0.168")
        self._writeTag(stream, "!-- Version:Bezier 10.5.0.168")
        self._writeTag(stream, "!-- PrintingApplication", "unidrive.exe")
        self._writeTag(stream, "BegGroup", "Header")
        self._writeTag(stream, "Version", "1.7")
        self._writeTag(stream, "Speedy")
        self._writeTag(stream, "ProcessMode", "Standard")
        self._writeTag(stream, "Resolution", "%d" % (self._dpi))
        self._writeTag(stream, "Cutline", "none")
        self._writeTag(stream, "Size.Orig", "%.2f;%.2f" % (self._max_x - self._min_x + 1.0, self._max_y - self._min_y + 1.0))
        self._writeTag(stream, "Size", "%.2f;%.2f" % (self._max_x - self._min_x + 1.0, self._max_y - self._min_y + 1.0))
        self._writeTag(stream, "MaterialGroup", "Standard")
        self._writeTag(stream, "MaterialName", "Standard")
        self._writeTag(stream, "JobName", "%s" % (os.path.basename(self._filename)))
        self._writeTag(stream, "JobNumber", "1")
        self._writeTag(stream, "AutoPosition")
        self._writeTag(stream, "EndGroup", "Header")
        self._writeTag(stream, "BegGroup", "JobMeta")
        self._writeTag(stream, "Meta", "Halftoning; Color")
        self._writeTag(stream, "EndGroup", "JobMeta")
        self._writeTag(stream, "BegGroup", "DrawCommands")
        self._outputPaths(stream, engrave_paths, 255, 0, 0)
        self._outputPaths(stream, cut_paths, 0, 0, 255)
        self._writeTag(stream, "EndGroup", "DrawCommands")

        return True

    def _writeTag(self, stream, key, value=None):
        if value is not None:
            stream.write(("<%s: %s>\r\n" % (key, value)).encode("utf-8"))
        else:
            stream.write(("<%s>\r\n" % (key)).encode("utf-8"))

    def _outputPaths(self, stream, paths, r, g, b):
        for poly in paths.open_paths:
            self._writeTag(stream, "BegGroup", "Family_%d" % (self._family_id))
            stream.write(('<DrawPolygon: %i;%i;%i;%i' % (len(poly), r, g, b)).encode('utf-8'))
            for point in poly:
                stream.write((';%i;%i' % self._convertPoint(point)).encode('utf-8'))
            stream.write(b'>\r\n')
            self._writeTag(stream, "EndGroup", "Family_%d" % (self._family_id))
            self._family_id += 1
        for poly in paths.closed_paths:
            self._writeTag(stream, "BegGroup", "Family_%d" % (self._family_id))
            stream.write(('<DrawPolygon: %i;%i;%i;%i' % (len(poly) + 1, r, g, b)).encode('utf-8'))
            for point in poly:
                stream.write((';%i;%i' % self._convertPoint(point)).encode('utf-8'))
            stream.write((';%i;%i' % self._convertPoint(poly[0])).encode('utf-8'))
            stream.write(b'>\r\n')
            self._writeTag(stream, "EndGroup", "Family_%d" % (self._family_id))
            self._family_id += 1

    def _convertPoint(self, point):
        return ((point[0] / Paths.SCALE) - self._min_x) / 25.4 * self._dpi, ((point[1] / Paths.SCALE) - self._min_y) / 25.4 * self._dpi

    def _processPathMinMax(self, path):
        for point in path:
            self._min_x = min(self._min_x, point[0] / Paths.SCALE)
            self._max_x = max(self._max_x, point[0] / Paths.SCALE)
            self._min_y = min(self._min_y, point[1] / Paths.SCALE)
            self._max_y = max(self._max_y, point[1] / Paths.SCALE)
