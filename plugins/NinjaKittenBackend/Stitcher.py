from UM.Logger import Logger

from nk import PointUtil
from nk import Paths


def _hash(point):
    return (point[0] // 10) ^ ((point[1] // 10) << 32)


def _hashes(point):
    yield _hash((point[0] - 10, point[1]))
    yield _hash(point)
    yield _hash((point[0] + 10, point[1]))
    yield _hash((point[0] - 10, point[1] - 10))
    yield _hash((point[0], point[1] - 10))
    yield _hash((point[0] + 10, point[1] - 10))
    yield _hash((point[0] - 10, point[1] + 10))
    yield _hash((point[0], point[1] + 10))
    yield _hash((point[0] + 10, point[1] + 10))
    raise StopIteration()


class _PathInfo:
    def __init__(self, path, point_index):
        self.path = path
        self.point_index = point_index


class Stitcher:
    def __init__(self):
        self._endpoints_map = {}
        self._closed_paths = []

    def addSegments(self, segments):
        for segment in segments:
            self.addSegment(segment)

    def addSegment(self, segment):
        p0 = (int(segment[0][0] * PointUtil.SCALE), int(segment[0][1] * PointUtil.SCALE))
        p1 = (int(segment[1][0] * PointUtil.SCALE), int(segment[1][1] * PointUtil.SCALE))

        info0 = self._findEndpoint(p0)
        info1 = self._findEndpoint(p1)
        if info0 is not None and info1 is not None:
            if info0.path == info1.path:
                self._closed_paths.append(info0.path)
                return
            if info0.point_index == -1 and info1.point_index == 0:
                info0.path += info1.path
                self._addInfoToHashMap(info0, info0.path[-1])
                self._removeInfo(self._findOtherInfo(info1))
                return
            if info0.point_index == 0 and info1.point_index == -1:
                info1.path += info0.path
                self._addInfoToHashMap(info1, info1.path[-1])
                self._removeInfo(self._findOtherInfo(info0))
                return
            if info0.point_index == 0 and info1.point_index == 0:
                self._removeInfo(self._findOtherInfo(info0))
                self._removeInfo(self._findOtherInfo(info1))
                info0.path.reverse()
                info0.path += info1.path
                self._addInfoToHashMap(_PathInfo(info0.path, 0), info0.path[0])
                self._addInfoToHashMap(_PathInfo(info0.path, -1), info0.path[-1])
                return
            if info0.point_index == -1 and info1.point_index == -1:
                self._removeInfo(self._findOtherInfo(info0))
                self._removeInfo(self._findOtherInfo(info1))
                info1.path.reverse()
                info0.path += info1.path
                self._addInfoToHashMap(_PathInfo(info0.path, 0), info0.path[0])
                self._addInfoToHashMap(_PathInfo(info0.path, -1), info0.path[-1])
                return
            Logger.log('d', '%d %d', info0.point_index, info1.point_index)
        if info0 is not None:
            self._addToPath(info0, p1)
            if info1 is not None:
                self._addInfoToHashMap(info1, info1.path[info1.point_index])
            return
        if info1 is not None:
            self._addToPath(info1, p0)
            return

        # No endpoint found to attach this segment, make a new path
        path = [p0, p1]
        self._addInfoToHashMap(_PathInfo(path, 0), p0)
        self._addInfoToHashMap(_PathInfo(path, -1), p1)

    def _addToPath(self, info, point):
        if info.point_index == 0:
            info.path.insert(0, point)
        else:
            info.path.append(point)
        self._addInfoToHashMap(info, point)

    def _findOtherInfo(self, info):
        if info.point_index == 0:
            index = -1
        else:
            index = 0
        hash = _hash(info.path[index])
        for i in self._endpoints_map[hash]:
            if i.path == info.path:
                return i
        return None

    def _addInfoToHashMap(self, info, point):
        hash = _hash(point)
        if hash not in self._endpoints_map:
            self._endpoints_map[hash] = []
        self._endpoints_map[hash].append(info)

    def _removeInfo(self, info):
        hash = _hash(info.path[info.point_index])
        self._endpoints_map[hash].remove(info)

    def _findEndpoint(self, point):
        best = None
        best_hash = None
        best_distance = 10 * 10
        for hash in _hashes(point):
            if hash in self._endpoints_map:
                for info in self._endpoints_map[hash]:
                    p = info.path[info.point_index]
                    distance = PointUtil.lengthSquared(PointUtil.sub(p, point))
                    if distance < best_distance:
                        best_distance = distance
                        best_hash = hash
                        best = info
        if best is not None:
            self._endpoints_map[best_hash].remove(best)
        return best

    def getPaths(self):
        paths = Paths.Paths()
        paths.closed_paths = self._closed_paths
        for hash_lists in self._endpoints_map.values():
            for info in hash_lists:
                if info.point_index == 0:
                    paths.open_paths.append(info.path)

        for distance in [100, 250]:
            n = 0
            while n < len(paths.open_paths):
                m = self._findOpenPathCloseTo(paths.open_paths[n][-1], paths.open_paths, distance)
                if m is not None and m != n:
                    paths.open_paths[n] += paths.open_paths[m]
                    paths.open_paths.pop(m)
                    if m < n:
                        n -= 1
                    continue
                n += 1

        n = 0
        while n < len(paths.open_paths):
            if PointUtil.length(PointUtil.sub(paths.open_paths[n][0], paths.open_paths[n][-1])) < 200:
                paths.closed_paths.append(paths.open_paths[n])
                paths.open_paths.pop(n)
                continue
            n += 1

        return paths

    def _findOpenPathCloseTo(self, point, open_paths, distance):
        for n in range(0, len(open_paths)):
            if PointUtil.length(PointUtil.sub(open_paths[n][0], point)) < distance:
                return n
        return None
