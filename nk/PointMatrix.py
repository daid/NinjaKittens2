import math


class PointMatrix:
    def __init__(self, angle):
        self._matrix = [
            math.cos(math.radians(angle)),
            -math.sin(math.radians(angle)),
            math.sin(math.radians(angle)),
            math.cos(math.radians(angle))
        ]

    def apply(self, point):
        return int(point[0] * self._matrix[0] + point[1] * self._matrix[1]), int(point[0] * self._matrix[2] + point[1] * self._matrix[3])

    def unapply(self, point):
        return int(point[0] * self._matrix[0] + point[1] * self._matrix[2]), int(point[0] * self._matrix[1] + point[1] * self._matrix[3])
