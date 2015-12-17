import base64
import zlib
import os

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application

class TrotecFileWriter(MeshWriter):
    def __init__(self, filename):
        super().__init__()
        self._bmp_magic = b"""eJztyTEKwkAURdFvJzbBHVimTG3CIAMpg4UuwiaQFWTlwjgDVu5AOOdxqzc9nnndrpdhHFJe9tc5
mlTra3sX8T5GHOqa2/f/VUppAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPCHpvme1y2dPr1q6Hs="""
        self._dpi = 500.0
        self._max_y = None
        self._max_x = None
        self._min_y = None
        self._min_x = None
        self._filename = filename

    def write(self, stream, node, mode=MeshWriter.OutputMode.BinaryMode):
        if mode != MeshWriter.OutputMode.BinaryMode:
            Logger.log("e", "GCode Writer does not support non-text mode")
            return False

        cut_paths = []
        for node in DepthFirstIterator(node):
            if node.hasDecoration("getPaths"):
                paths = node.callDecoration("getPaths")
                cut_paths += paths.closed_paths

        min_x = 10000000000
        max_x = -10000000000
        min_y = 10000000000
        max_y = -10000000000
        for path in cut_paths:
            for point in path:
                min_x = min(min_x, point[0] / 1000.0)
                max_x = max(max_x, point[0] / 1000.0)
                min_y = min(min_y, point[1] / 1000.0)
                max_y = max(max_y, point[1] / 1000.0)
        self._max_y = max_y
        self._max_x = max_x
        self._min_y = min_y
        self._min_x = min_x

        stream.write(b'<!-- Version: 9.4.2.1034>\r\n')
        stream.write(b'<!-- PrintingApplication: ps2tsf.exe>\r\n')
        stream.write(b'<BegGroup: Header>\r\n')
        stream.write(b'<ProcessMode: Standard>\r\n')
        stream.write(('<Size: %.2f;%.2f>\r\n' % (max_x - min_x + 1.0, max_y - min_y + 1.0)).encode('utf-8'))
        stream.write(b'<MaterialGroup: Rubber>\r\n')
        stream.write(b'<MaterialName: 2.3 mm>\r\n')
        stream.write(('<JobName: %s>\r\n' % (os.path.basename(self._filename))).encode('utf-8'))
        stream.write(b'<JobNumber: 1>\r\n')
        stream.write(('<Resolution: %i>\r\n' % (self._dpi)).encode('utf-8'))
        stream.write(b'<Cutline: none>\r\n')
        stream.write(b'<EndGroup: Header>\r\n')
        stream.write(b'<BegGroup: Bitmap>\r\n')
        stream.write(zlib.decompress(base64.decodebytes(self._bmp_magic)))
        stream.write(b'<EndGroup: Bitmap>\r\n')
        stream.write(b'<BegGroup: DrawCommands>\r\n')

        for poly in cut_paths:
            stream.write(('<DrawPolygon: %i;255;0;0' % (len(poly) + 1)).encode('utf-8'))
            for point in poly:
                stream.write((';%i;%i' % self._convertPoint(point)).encode('utf-8'))
            stream.write((';%i;%i' % self._convertPoint(poly[0])).encode('utf-8'))
            stream.write(b'>\r\n')
        stream.write(b'<EndGroup: DrawCommands>\r\n')

        return True

    def _convertPoint(self, point):
        return (((point[0] / 1000.0) - self._min_x) / 25.4 * self._dpi, ((point[1] / 1000.0) - self._min_y) / 25.4 * self._dpi)
