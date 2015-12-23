import time
import math

from UM.Logger import Logger

from nk import Paths
from nk import PointUtil


def _hash(point):
    return (point[0] // 1000) ^ ((point[1] // 1000) << 32)


def _hashes(point):
    yield _hash((point[0] - 1000, point[1]))
    yield _hash(point)
    yield _hash((point[0] + 1000, point[1]))
    yield _hash((point[0] - 1000, point[1] - 1000))
    yield _hash((point[0], point[1] - 1000))
    yield _hash((point[0] + 1000, point[1] - 1000))
    yield _hash((point[0] - 1000, point[1] + 1000))
    yield _hash((point[0], point[1] + 1000))
    yield _hash((point[0] + 1000, point[1] + 1000))
    raise StopIteration()


class OrderOptimizer:
    def __init__(self, base_nodes):
        self._base_nodes = base_nodes
        self._result = Paths.Paths()

        depth = self._calculateTreeDepth()
        for n in reversed(range(0, depth)):
            paths = self._getPathsAtDepth(n)
            center_points = self._centerPoints(paths)
            order = self._calculateClosedOrder(center_points)

            for n in order:
                self._result.closed_paths.append(paths.closed_paths[n].copy())
            order = self._calculateOpenOrder(paths.open_paths)
            for n in order:
                self._result.open_paths.append(paths.open_paths[n].copy())

        self._orderStartPoints()

    def _centerPoints(self, paths):
        center_points = []
        for poly in paths.closed_paths:
            center = (0, 0)
            for point in poly:
                center = PointUtil.add(center, point)
            center = (center[0] / len(poly), center[1] / len(poly))
            center_points.append(center)
        return center_points

    def _calculateClosedOrder(self, center_points):
        done = [False] * len(center_points)
        start = None
        for n in range(0, len(center_points)):
            if start is None or center_points[start][0] > center_points[n][0]:
                start = n
        if start is None:
            return []
        done[start] = True
        result = [start]
        while len(result) < len(center_points):
            best_distance = None
            best = None
            for n in range(0, len(center_points)):
                if done[n]:
                    continue
                distance = PointUtil.lengthSquared(PointUtil.sub(center_points[start], center_points[n]))
                if best_distance is None or best_distance > distance:
                    best_distance = distance
                    best = n
            done[best] = True
            result.append(best)
            start = best
        return result

    def _calculateOpenOrder(self, paths):
        quick_finds = 0
        slow_finds = 0
        slow_time = 0.0
        Logger.log("i", "Line order optimizer, start")

        hash_map = {}
        for n in range(0, len(paths)):
            h = _hash(paths[n][0])
            if h not in hash_map:
                hash_map[h] = []
            hash_map[h].append(n)
            h = _hash(paths[n][-1])
            if h not in hash_map:
                hash_map[h] = []
            hash_map[h].append(n)

        todo = set(range(0, len(paths)))
        start = None
        for n in range(0, len(paths)):
            if start is None or paths[start][0][0] > paths[n][0][0]:
                start = n
        if start is None:
            return []
        todo.remove(start)
        result = [start]
        while len(result) < len(paths):
            best_distance = None
            best = None
            for h in _hashes(paths[start][0]):
                if h in hash_map:
                    for n in hash_map[h]:
                        if n not in todo:
                            continue
                        distance = min(
                            PointUtil.lengthSquared(PointUtil.sub(paths[start][0], paths[n][0])),
                            PointUtil.lengthSquared(PointUtil.sub(paths[start][0], paths[n][-1])),
                            PointUtil.lengthSquared(PointUtil.sub(paths[start][-1], paths[n][0])),
                            PointUtil.lengthSquared(PointUtil.sub(paths[start][-1], paths[n][-1]))
                        )
                        if best_distance is None or best_distance > distance:
                            best_distance = distance
                            best = n
            for h in _hashes(paths[start][-1]):
                if h in hash_map:
                    for n in hash_map[h]:
                        if n not in todo:
                            continue
                        distance = min(
                            PointUtil.lengthSquared(PointUtil.sub(paths[start][0], paths[n][0])),
                            PointUtil.lengthSquared(PointUtil.sub(paths[start][0], paths[n][-1])),
                            PointUtil.lengthSquared(PointUtil.sub(paths[start][-1], paths[n][0])),
                            PointUtil.lengthSquared(PointUtil.sub(paths[start][-1], paths[n][-1]))
                        )
                        if best_distance is None or best_distance > distance:
                            best_distance = distance
                            best = n
            if best is None:
                slow_finds += 1
                t = time.time()
                for n in todo:
                    distance = min(
                        PointUtil.lengthSquared(PointUtil.sub(paths[start][0], paths[n][0])),
                        PointUtil.lengthSquared(PointUtil.sub(paths[start][0], paths[n][-1])),
                        PointUtil.lengthSquared(PointUtil.sub(paths[start][-1], paths[n][0])),
                        PointUtil.lengthSquared(PointUtil.sub(paths[start][-1], paths[n][-1]))
                    )
                    if best_distance is None or best_distance > distance:
                        best_distance = distance
                        best = n
                slow_time += time.time() - t
            else:
                quick_finds += 1
            todo.remove(best)
            result.append(best)
            start = best
        Logger.log("i", "Line order optimizer, quick: %d, slow: %d (%f)", quick_finds, slow_finds, slow_time)
        return result

    def _calculateTreeDepth(self, nodes=None, depth=0):
        if nodes is None:
            nodes = self._base_nodes
        max_depth = depth
        for node in nodes:
            max_depth = max(max_depth, self._calculateTreeDepth(node.children, depth + 1))
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
                self._getPathsAtDepthRecursive(target_depth, result_path, node.children, depth + 1)

    def _orderStartPoints(self):
        if len(self._result.open_paths) > 1:
            start = self._result.open_paths[0][0]
            for n in range(1, len(self._result.open_paths)):
                if PointUtil.lengthSquared(PointUtil.sub(start, self._result.open_paths[n][0])) > PointUtil.lengthSquared(PointUtil.sub(start, self._result.open_paths[n][-1])):
                    self._result.open_paths[n].reverse()
                start = self._result.open_paths[n][-1]
        if len(self._result.closed_paths) > 1:
            start = self._result.closed_paths[0][0]
            for n in range(1, len(self._result.closed_paths)):
                best = self._findClosestIndexTo(start, self._result.closed_paths[n])
                self._result.closed_paths[n] = self._result.closed_paths[n][best:] + self._result.closed_paths[n][:best]
                start = self._result.closed_paths[n][0]
            best = self._findClosestIndexTo(self._result.closed_paths[1][0], self._result.closed_paths[0])
            self._result.closed_paths[0] = self._result.closed_paths[0][best:] + self._result.closed_paths[0][:best]

    def _findClosestIndexTo(self, point, path):
        best = None
        best_distance = None
        for m in range(0, len(path)):
            distance = PointUtil.lengthSquared(PointUtil.sub(point, path[m]))
            if best_distance is None or best_distance > distance:
                best_distance = distance
                best = m
        return best

    def getResults(self):
        return self._result
