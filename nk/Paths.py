import pyclipper


SCALE = 1000.0


class Paths:
    def __init__(self):
        self.closed_paths = []
        self.open_paths = []
        self.childs = []

    def __repr__(self):
        return "Paths{%d, %d}" % (len(self.closed_paths), len(self.open_paths))

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

    def buildTree(self):
        c = pyclipper.Pyclipper()
        if len(self.closed_paths) > 0:
            c.AddPaths(self.closed_paths, pyclipper.PT_SUBJECT, True)
        root = c.Execute2(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        ret = []
        for node in root.Childs:
            ret.append(self._buildTree(node))
        return ret

    def _buildTree(self, node):
        paths = Paths()
        if node.IsOpen:
            paths.open_paths = [node.Contour]
        else:
            paths.closed_paths = [node.Contour]
        for n in node.Childs:
            paths.childs.append(self._buildTree(n))
        return paths
