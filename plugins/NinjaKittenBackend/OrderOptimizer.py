from nk import Paths
from nk import PointUtil


class OrderOptimizer:
    def __init__(self, paths):
        self._base_nodes = paths.buildTree()
        self._result = Paths.Paths()

        depth = self._calculateTreeDepth()
        for n in reversed(range(0, depth)):
            paths = self._getPathsAtDepth(n)
            center_points = self._centerPoints(paths)
            order = self._calculateOrder(center_points)

            for n in order:
                self._result.closed_paths.append(paths.closed_paths[n])
            self._result.open_paths += paths.open_paths

    def _centerPoints(self, paths):
        center_points = []
        for poly in paths.closed_paths:
            center = (0, 0)
            for point in poly:
                center = PointUtil.add(center, point)
            center = (center[0] / len(poly), center[1] / len(poly))
            center_points.append(center)
        return center_points

    def _calculateOrder(self, center_points):
        done = [False] * len(center_points)
        start = None
        for n in range(0, len(center_points)):
            if start is None or center_points[start][0] > center_points[n][0]:
                start = n
        if start is None:
            return []
        done[n] = True
        result = [n]
        while len(result) < len(center_points):
            best_distance = None
            best = None
            for n in range(0, len(center_points)):
                if done[n]:
                    continue
                distance = PointUtil.lengthSquared(PointUtil.sub(center_points[start], center_points[n]))
                if best_distance is None or best_distance > distance:
                    best_distance = PointUtil.lengthSquared(PointUtil.sub(center_points[start], center_points[n]))
                    best = n
            done[best] = True
            result.append(best)
        return result

    def _calculateTreeDepth(self, nodes=None, depth=0):
        if nodes is None:
            nodes = self._base_nodes
        max_depth = depth
        for node in nodes:
            max_depth = max(max_depth, self._calculateTreeDepth(node.childs, depth + 1))
        return max_depth

    def _getPathsAtDepth(self, target_depth):
        result = Paths.Paths()
        self._getPathsAtDepthRecursive(target_depth, result, self._base_nodes, 0)
        return result

    def _getPathsAtDepthRecursive(self, target_depth, result_path, nodes, depth):
        if target_depth == depth:
            for node in nodes:
                result_path.closed_paths += node.closed_paths
                result_path.open_paths += node.open_paths
        else:
            for node in nodes:
                self._getPathsAtDepthRecursive(target_depth, result_path, node.childs, depth + 1)

    def getResults(self):
        return self._result
