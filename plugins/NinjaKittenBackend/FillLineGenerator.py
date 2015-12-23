from nk import PointMatrix
from nk import Paths


class FillLineGenerator:
    def __init__(self, angle, line_spacing, paths):
        self._result = Paths.Paths()

        line_spacing = line_spacing * Paths.SCALE
        matrix = PointMatrix.PointMatrix(angle)

        cut_list = {}

        for path in paths.closed_paths:
            p1 = matrix.apply(path[-1])
            for p0 in path:
                p0 = matrix.apply(p0)
                idx0 = int(p0[0] // line_spacing)
                idx1 = int(p1[0] // line_spacing)
                x_min = p0[0]
                x_max = p1[0]
                if x_min > x_max:
                    x_min, x_max = x_max, x_min
                if idx0 > idx1:
                    idx0, idx1 = idx1, idx0
                for idx in range(idx0, idx1 + 1):
                    x = idx * line_spacing + line_spacing // 2
                    if x < x_min or x >= x_max:
                        continue
                    y = p0[1] + (p1[1] - p0[1]) * (x - p0[0]) // (p1[0] - p0[0])
                    if idx not in cut_list:
                        cut_list[idx] = []
                    cut_list[idx].append(y)
                p1 = p0

        for idx, y_list in cut_list.items():
            x = idx * line_spacing + line_spacing // 2
            y_list.sort()
            for y_values in zip(y_list[::2], y_list[1::2]):
                p0 = matrix.unapply((x, y_values[0]))
                p1 = matrix.unapply((x, y_values[1]))
                self._result.open_paths.append([p0, p1])

    def getResult(self):
        return self._result
