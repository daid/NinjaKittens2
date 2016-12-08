from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Math.Color import Color

from . import Paths


## Simple decorator to indicate a scene node holds resulting path data
class PathResultDecorator(SceneNodeDecorator):
    _move_color = Color(0, 0, 0, 128)
    _cut_color = Color(255, 0, 0, 255)
    _engrave_color = Color(0, 0, 255, 255)

    def __init__(self):
        super().__init__()
        self._paths = None
        
    def getCutPaths(self):
        return self._cut_paths

    def getEngravePaths(self):
        return self._engrave_paths
    
    def setPaths(self, engrave_paths, cut_paths):
        self._cut_paths = cut_paths
        self._engrave_paths = engrave_paths
        self._mesh = MeshBuilder()

        last_point = None

        for path in engrave_paths.closed_paths:
            if last_point is not None:
                self._addMeshLine(last_point, path[0], self._move_color)

            last_point = path[0]
            for point in path[1:]:
                self._addMeshLine(last_point, point, self._engrave_color)
                last_point = point
            self._addMeshLine(last_point, path[0], self._engrave_color)
            last_point = path[0]

        for path in engrave_paths.open_paths:
            if last_point is not None:
                self._addMeshLine(last_point, path[0], self._move_color)

            last_point = path[0]
            for point in path[1:]:
                self._addMeshLine(last_point, point, self._engrave_color)
                last_point = point

        for path in cut_paths.closed_paths:
            if last_point is not None:
                self._addMeshLine(last_point, path[0], self._move_color)

            last_point = path[0]
            for point in path[1:]:
                self._addMeshLine(last_point, point, self._cut_color)
                last_point = point
            self._addMeshLine(last_point, path[0], self._cut_color)
            last_point = path[0]

        for path in cut_paths.open_paths:
            if last_point is not None:
                self._addMeshLine(last_point, path[0], self._move_color)

            last_point = path[0]
            for point in path[1:]:
                self._addMeshLine(last_point, point, self._cut_color)
                last_point = point

        self.getNode().setMeshData(self._mesh.build())

    def _addMeshLine(self, p0, p1, color):
        self._mesh.addVertex(p0[0] / Paths.SCALE, 0.0, p0[1] / Paths.SCALE)
        self._mesh.addVertex(p1[0] / Paths.SCALE, 0.0, p1[1] / Paths.SCALE)
        self._mesh.setVertexColor(self._mesh.getVertexCount() - 2, color)
        self._mesh.setVertexColor(self._mesh.getVertexCount() - 1, color)
