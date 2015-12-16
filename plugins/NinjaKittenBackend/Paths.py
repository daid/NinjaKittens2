import pyclipper


SCALE = 1000.0


class Paths:
    def __init__(self):
        self.closed_paths = []
        self.open_paths = []

    def processEvenOdd(self):
        c = pyclipper.Pyclipper()
        if len(self.closed_paths) > 0:
            c.AddPaths(self.closed_paths, pyclipper.PT_SUBJECT, True)
        result = Paths()
        result.closed_paths = c.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        result.open_paths = self.open_paths
        return result

    def offset(self, distance):
        co = pyclipper.PyclipperOffset()
        if len(self.closed_paths) > 0:
            co.AddPaths(self.closed_paths, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
        result = Paths()
        result.closed_paths = co.Execute(int(distance * SCALE))
        result.open_paths = self.open_paths
        return result
