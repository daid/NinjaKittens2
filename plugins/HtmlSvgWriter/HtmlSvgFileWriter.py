from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger

from nk import Paths


class HtmlSvgFileWriter(MeshWriter):
    def __init__(self, filename):
        super().__init__()

    def write(self, stream, node, mode=MeshWriter.OutputMode.BinaryMode):
        if mode != MeshWriter.OutputMode.BinaryMode:
            Logger.log("e", "GCode Writer does not support non-text mode")
            return False
        self._stream = stream

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
        for path in engrave_paths.open_paths:
            self._processPathMinMax(path)
        for path in engrave_paths.closed_paths:
            self._processPathMinMax(path)
        for path in cut_paths.open_paths:
            self._processPathMinMax(path)
        for path in cut_paths.closed_paths:
            self._processPathMinMax(path)

        canvas_size = 1000
        self._scale = min(canvas_size / (self._max_x - self._min_x), canvas_size / (self._max_y - self._min_y))
        self._write("<!DOCTYPE html><html><body>\n")
        self._write("Size: %f %f<br>" % (self._max_x - self._min_x, self._max_y - self._min_y))
        self._write("<svg xmlns=\"http://www.w3.org/2000/svg\" version=\"1.1\" style=\"width:%dpx;height:%dpx\">\n" % (canvas_size, canvas_size))
        self._outputPaths(engrave_paths, 255, 0, 0)
        self._outputPaths(cut_paths, 0, 0, 255)
        self._write("</svg>\n")
        self._write("</body></html>")

        return True

    def _write(self, data):
        self._stream.write(data.encode("utf-8"))

    def _outputPaths(self, paths, r, g, b):
        for poly in paths.open_paths:
            self._write("<path fill=\"none\" stroke=\"#%02x%02x%02x\" stroke-width=\"1\" d=\"" % (r, g, b))
            self._write("M%f,%f" % self._convertPoint(poly[0]))
            for point in poly[1:]:
                self._write("L%f,%f" % self._convertPoint(point))
            self._write("\" />\n")
        for poly in paths.closed_paths:
            self._write("<polygon points=\"")
            for point in poly:
                self._write("%f,%f " % self._convertPoint(point))
            self._write("\" style=\"fill:none;stroke:#%02x%02x%02x;stroke-width:1\" />\n" % (r, g, b))

    def _convertPoint(self, point):
        return ((point[0] / Paths.SCALE) - self._min_x) * self._scale, ((point[1] / Paths.SCALE) - self._min_y) * self._scale

    def _processPathMinMax(self, path):
        for point in path:
            self._min_x = min(self._min_x, point[0] / Paths.SCALE)
            self._max_x = max(self._max_x, point[0] / Paths.SCALE)
            self._min_y = min(self._min_y, point[1] / Paths.SCALE)
            self._max_y = max(self._max_y, point[1] / Paths.SCALE)
