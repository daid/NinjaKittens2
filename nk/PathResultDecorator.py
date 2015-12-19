from UM.Mesh.MeshData import MeshData
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Math.Color import Color

from . import Paths


## Simple decorator to indicate a scene node holds resulting path data
class PathResultDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._paths = None
        
    def getPaths(self):
        return self._paths
    
    def setPaths(self, paths):
        self._paths = paths

        last_point = None

        mesh = MeshData()
        for path in paths.closed_paths:
            if last_point is not None:
                mesh.addVertex(last_point[0] / Paths.SCALE, 0.0, last_point[1] / Paths.SCALE)
                mesh.setVertexColor(mesh.getVertexCount() - 1, Color(255, 0, 0, 255))
                mesh.addVertex(path[0][0] / Paths.SCALE, 0.0, path[0][1] / Paths.SCALE)
                mesh.setVertexColor(mesh.getVertexCount() - 1, Color(255, 0, 0, 255))

            mesh.addVertex(path[0][0] / Paths.SCALE, 0.0, path[0][1] / Paths.SCALE)
            mesh.setVertexColor(mesh.getVertexCount() - 1, Color(0, 0, 0, 255))
            for point in path[1:]:
                mesh.addVertex(point[0] / Paths.SCALE, 0.0, point[1] / Paths.SCALE)
                mesh.setVertexColor(mesh.getVertexCount() - 1, Color(0, 0, 0, 255))
                mesh.addVertex(point[0] / Paths.SCALE, 0.0, point[1] / Paths.SCALE)
                mesh.setVertexColor(mesh.getVertexCount() - 1, Color(0, 0, 0, 255))
            mesh.addVertex(path[0][0] / Paths.SCALE, 0.0, path[0][1] / Paths.SCALE)
            mesh.setVertexColor(mesh.getVertexCount() - 1, Color(0, 0, 0, 255))
            last_point = path[0]

        for path in paths.open_paths:
            if last_point is not None:
                mesh.addVertex(last_point[0] / Paths.SCALE, 0.0, last_point[1] / Paths.SCALE)
                mesh.setVertexColor(mesh.getVertexCount() - 1, Color(255, 0, 0, 255))
                mesh.addVertex(path[0][0] / Paths.SCALE, 0.0, path[0][1] / Paths.SCALE)
                mesh.setVertexColor(mesh.getVertexCount() - 1, Color(255, 0, 0, 255))

            mesh.addVertex(path[0][0] / Paths.SCALE, 0.0, path[0][1] / Paths.SCALE)
            mesh.setVertexColor(mesh.getVertexCount() - 1, Color(0, 0, 0, 255))
            for point in path[1:-2]:
                mesh.addVertex(point[0] / Paths.SCALE, 0.0, point[1] / Paths.SCALE)
                mesh.setVertexColor(mesh.getVertexCount() - 1, Color(0, 0, 0, 255))
                mesh.addVertex(point[0] / Paths.SCALE, 0.0, point[1] / Paths.SCALE)
                mesh.setVertexColor(mesh.getVertexCount() - 1, Color(0, 0, 0, 255))
            mesh.addVertex(path[-1][0] / Paths.SCALE, 0.0, path[-1][1] / Paths.SCALE)
            mesh.setVertexColor(mesh.getVertexCount() - 1, Color(0, 0, 0, 255))
            last_point = path[-1]

        self.getNode().setMeshData(mesh)
