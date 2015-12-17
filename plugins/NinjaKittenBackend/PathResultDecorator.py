from UM.Mesh.MeshData import MeshData
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
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

        mesh = MeshData()
        for path in paths.closed_paths:
            mesh.addVertex(path[0][0] / Paths.SCALE, 2, path[0][1] / Paths.SCALE)
            for point in path[1:]:
                mesh.addVertex(point[0] / Paths.SCALE, 2, point[1] / Paths.SCALE)
                mesh.addVertex(point[0] / Paths.SCALE, 2, point[1] / Paths.SCALE)
            mesh.addVertex(path[0][0] / Paths.SCALE, 2, path[0][1] / Paths.SCALE)
        for path in paths.open_paths:
            mesh.addVertex(path[0][0] / Paths.SCALE, 2, path[0][1] / Paths.SCALE)
            for point in path[1:-2]:
                mesh.addVertex(point[0] / Paths.SCALE, 2, point[1] / Paths.SCALE)
                mesh.addVertex(point[0] / Paths.SCALE, 2, point[1] / Paths.SCALE)
            mesh.addVertex(path[-1][0] / Paths.SCALE, 2, path[-1][1] / Paths.SCALE)

        self.getNode().setMeshData(mesh)
