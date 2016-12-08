from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Scene import SceneNode
from UM.Logger import Logger
from UM.Job import Job

from nk import PathResultDecorator

from . import Slicer
from . import Stitcher
from . import OrderOptimizer
from . import FillLineGenerator


class NinjaJob(Job):
    def __init__(self, node, profile):
        super().__init__()
        self._node = node
        self._profile = profile

    def run(self):
        self._progress(0.0)

        stitcher = Stitcher.Stitcher()
        segment_count = 0
        for node in DepthFirstIterator(self._node):
            if type(node) is not SceneNode:
                continue
            if node.getDecorator(PathResultDecorator.PathResultDecorator):
                node.setParent(None)
                continue
            mesh = node.getMeshData()
            if mesh is None:
                continue
            segments = Slicer.Slicer(node).execute(0.5)
            segment_count += len(segments)
            stitcher.addSegments(segments)

        self._progress(0.1)

        Logger.log("i", "Sliced: %d segments" % (segment_count))
        paths = stitcher.getPaths()
        Logger.log("i", "OpenPaths: %s", len(paths.open_paths))
        Logger.log("i", "ClosedPaths: %s", len(paths.closed_paths))

        paths = paths.processEvenOdd()
        tool_diameter = self._profile["tool_diameter"]
        cut_method = self._profile["cut_method"]
        engrave_method = self._profile["engrave_method"]
        engrave_line_distance = self._profile["engrave_line_distance"]

        if cut_method == "cut_all_inside" or cut_method == "engrave_all":
            tool_diameter = -tool_diameter

        paths = paths.offset(tool_diameter / 2.0)

        cut_nodes = paths.buildTree()
        engrave_nodes = []

        self._progress(0.2)

        if cut_method == "engrave_all":
            engrave_nodes = cut_nodes
            cut_nodes = []
        elif cut_method == "cut_outline_engrave_rest":
            for node in cut_nodes:
                engrave_nodes += node.children
                node.children = []

        for n in range(0, len(engrave_nodes)):
            node = engrave_nodes[n].flatten()
            if engrave_method == "horizontal":
                node = FillLineGenerator.FillLineGenerator(90, engrave_line_distance, node).getResult()
            elif engrave_method == "vertical":
                node = FillLineGenerator.FillLineGenerator(0, engrave_line_distance, node).getResult()
            elif engrave_method == "cross":
                p_h = FillLineGenerator.FillLineGenerator(90, engrave_line_distance, node).getResult()
                node = FillLineGenerator.FillLineGenerator(0, engrave_line_distance, node).getResult()
                node.open_paths += p_h.open_paths
            elif engrave_method == "concentric":
                p = node
                while len(p.closed_paths) > 0:
                    p = p.offset(-engrave_line_distance)
                    node.closed_paths += p.closed_paths
            engrave_nodes[n] = node

        self._progress(0.3)

        order = OrderOptimizer.OrderOptimizer(engrave_nodes)
        engrave_paths = order.getResults()

        order = OrderOptimizer.OrderOptimizer(cut_nodes)
        cut_paths = order.getResults()

        self._progress(0.9)

        Logger.log('i', 'Cut: closed: %d open: %d', len(cut_paths.closed_paths), len(cut_paths.open_paths))
        Logger.log('i', 'Engrave: closed: %d open: %d', len(engrave_paths.closed_paths), len(engrave_paths.open_paths))

        self.buildResultNode(engrave_paths, cut_paths)

    def buildResultNode(self, engrave_paths, cut_paths):
        new_node = SceneNode()
        decorator = PathResultDecorator.PathResultDecorator()
        new_node.addDecorator(decorator)
        decorator.setPaths(engrave_paths, cut_paths)
        self.setResult(new_node)

    def _progress(self, amount):
        Logger.log('i', 'NinjaProgress: %i%%', int(amount * 100))
        self.progress.emit(amount)
