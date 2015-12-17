from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Scene import SceneNode
from UM.Logger import Logger
from UM.Job import Job

from . import Slicer
from . import Stitcher
from . import PathResultDecorator
from . import OrderOptimizer


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

        order = OrderOptimizer.OrderOptimizer(paths)
        paths = order.getResults()

        self.buildResultNode(paths)

    def buildResultNode(self, paths):
        new_node = SceneNode()
        decorator = PathResultDecorator.PathResultDecorator()
        new_node.addDecorator(decorator)
        decorator.setPaths(paths)
        new_node.setParent(self._scene.getRoot())
