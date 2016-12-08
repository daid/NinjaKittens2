

class Slicer:
    def __init__(self, node):
        self._mesh_data = node.getMeshData().getTransformed(node.getWorldTransformation())
        self._slice_height = None
        self._segments = None

    def execute(self, height):
        self._slice_height = height
        self._segments = []
        if self._mesh_data.hasIndices():
            for indices in self._mesh_data.getIndices():
                self._handleFace(indices[0], indices[1], indices[2])
        else:
            for n in range(0, self._mesh_data.getVertexCount(), 3):
                self._handleFace(n, n + 1, n + 2)
        return self._segments

    def _handleFace(self, index0, index1, index2):
        v0 = self._mesh_data.getVertex(index0)
        v1 = self._mesh_data.getVertex(index1)
        v2 = self._mesh_data.getVertex(index2)

        if v0[1] < self._slice_height and v1[1] >= self._slice_height and v2[1] >= self._slice_height:
            segment = self._project2d(v0, v2, v1)
        elif v0[1] > self._slice_height and v1[1] < self._slice_height and v2[1] < self._slice_height:
            segment = self._project2d(v0, v1, v2)
        elif v1[1] < self._slice_height and v0[1] >= self._slice_height and v2[1] >= self._slice_height:
            segment = self._project2d(v1, v0, v2)
        elif v1[1] > self._slice_height and v0[1] < self._slice_height and v2[1] < self._slice_height:
            segment = self._project2d(v1, v2, v0)
        elif v2[1] < self._slice_height and v1[1] >= self._slice_height and v0[1] >= self._slice_height:
            segment = self._project2d(v2, v1, v0)
        elif v2[1] > self._slice_height and v1[1] < self._slice_height and v0[1] < self._slice_height:
            segment = self._project2d(v2, v0, v1)
        else:
            return
        self._segments.append(segment)

    def _project2d(self, v0, v1, v2):
        p0 = (v0[0] + (v1[0] - v0[0]) * (self._slice_height - v0[1]) / (v1[1] - v0[1]), v0[2] + (v1[2] - v0[2]) * (self._slice_height - v0[1]) / (v1[1] - v0[1]))
        p1 = (v0[0] + (v2[0] - v0[0]) * (self._slice_height - v0[1]) / (v2[1] - v0[1]), v0[2] + (v2[2] - v0[2]) * (self._slice_height - v0[1]) / (v2[1] - v0[1]))
        return p0, p1
