from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Scene import SceneNode
from UM.Logger import Logger
from UM.Job import Job
from UM.Mesh.MeshData import MeshData

from . import Paths
from . import Slicer
from . import Stitcher
from . import PathResultDecorator


class NinjaJob(Job):
    def __init__(self):
        super().__init__()
        self._scene = Application.getInstance().getController().getScene()
        self._profile = Application.getInstance().getMachineManager().getActiveProfile()

    def run(self):
        stitcher = Stitcher.Stitcher()
        segment_count = 0
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is not SceneNode:
                continue
            if node.hasDecoration("getPaths"):
                self._scene.getRoot().removeChild(node)
                continue
            mesh = node.getMeshData()
            if mesh is None:
                continue
            segments = Slicer.Slicer(node).execute(0.5)
            segment_count += len(segments)
            stitcher.addSegments(segments)

        Logger.log("i", "Sliced: %d segments" % (segment_count))
        paths = stitcher.getPaths()
        Logger.log("i", "OpenPaths: %s", len(paths.open_paths))
        Logger.log("i", "ClosedPaths: %s", len(paths.closed_paths))

        paths = paths.processEvenOdd()
        tool_diameter = self._profile.getSettingValue("tool_diameter")
        paths = paths.offset(tool_diameter / 2.0)

        self.buildResultNode(paths)

    def buildResultNode(self, paths):
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

        new_node = SceneNode()
        decorator = PathResultDecorator.PathResultDecorator()
        decorator.setPaths(paths)
        new_node.addDecorator(decorator)
        new_node.setMeshData(mesh)
        new_node.setParent(self._scene.getRoot())
