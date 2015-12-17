import math

SCALE = 1000.0


def sub(p0, p1):
    return p0[0] - p1[0], p0[1] - p1[1]


def add(p0, p1):
    return p0[0] + p1[0], p0[1] + p1[1]


def lengthSquared(point):
    return point[0] * point[0] + point[1] * point[1]


def length(point):
    return math.sqrt(lengthSquared(point))