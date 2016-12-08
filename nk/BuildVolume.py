# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Scene.Platform import Platform
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Resources import Resources
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Math.Color import Color
from UM.Math.AxisAlignedBox import AxisAlignedBox

from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL


##  Build volume is a special kind of node that is responsible for rendering the printable area & disallowed areas.
class BuildVolume(SceneNode):
    VolumeOutlineColor = Color(12, 169, 227, 255)

    def __init__(self, parent = None):
        super().__init__(parent)

        self._width = 0
        self._height = 0
        self._depth = 0

        self._shader = None

        self._grid_mesh = None
        self._grid_shader = None

        self._disallowed_areas = []
        self._disallowed_area_mesh = None

        self.setCalculateBoundingBox(False)
        self._volume_aabb = None

        self._raft_thickness = 0.0
        self._adhesion_type = None
        self._platform = Platform(self)

        self._global_container_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

    def setWidth(self, width):
        if width: self._width = width

    def setHeight(self, height):
        if height: self._height = height

    def setDepth(self, depth):
        if depth: self._depth = depth

    def getDisallowedAreas(self):
        return self._disallowed_areas

    def setDisallowedAreas(self, areas):
        self._disallowed_areas = areas

    def render(self, renderer):
        if not self.getMeshData():
            return True

        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "default.shader"))
            self._grid_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "grid.shader"))

        renderer.queueNode(self, mode = RenderBatch.RenderMode.Lines)
        renderer.queueNode(self, mesh = self._grid_mesh, shader = self._grid_shader, backface_cull = True)
        if self._disallowed_area_mesh:
            renderer.queueNode(self, mesh = self._disallowed_area_mesh, shader = self._shader, transparent = True, backface_cull = True, sort = -9)

        return True

    ##  Recalculates the build volume & disallowed areas.
    def rebuild(self):
        if not self._width or not self._height or not self._depth:
            return

        min_w = -self._width / 2
        max_w = self._width / 2
        min_h = 0.0
        max_h = self._height
        min_d = -self._depth / 2
        max_d = self._depth / 2

        mb = MeshBuilder()

        # Outline 'cube' of the build volume
        mb.addLine(Vector(min_w, min_h, min_d), Vector(max_w, min_h, min_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, min_h, min_d), Vector(min_w, max_h, min_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, max_h, min_d), Vector(max_w, max_h, min_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(max_w, min_h, min_d), Vector(max_w, max_h, min_d), color = self.VolumeOutlineColor)

        mb.addLine(Vector(min_w, min_h, max_d), Vector(max_w, min_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, min_h, max_d), Vector(min_w, max_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, max_h, max_d), Vector(max_w, max_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(max_w, min_h, max_d), Vector(max_w, max_h, max_d), color = self.VolumeOutlineColor)

        mb.addLine(Vector(min_w, min_h, min_d), Vector(min_w, min_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(max_w, min_h, min_d), Vector(max_w, min_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, max_h, min_d), Vector(min_w, max_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(max_w, max_h, min_d), Vector(max_w, max_h, max_d), color = self.VolumeOutlineColor)

        self.setMeshData(mb.build())

        mb = MeshBuilder()
        mb.addQuad(
            Vector(min_w, min_h - 0.2, min_d),
            Vector(max_w, min_h - 0.2, min_d),
            Vector(max_w, min_h - 0.2, max_d),
            Vector(min_w, min_h - 0.2, max_d)
        )

        for n in range(0, 6):
            v = mb.getVertex(n)
            mb.setVertexUVCoordinates(n, v[0], v[2])
        self._grid_mesh = mb.build()

        self._volume_aabb = AxisAlignedBox(
            minimum = Vector(min_w, min_h - 1.0, min_d),
            maximum = Vector(max_w, max_h - self._raft_thickness, max_d))

    def getBoundingBox(self):
        return self._volume_aabb

    def _onGlobalContainerStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingPropertyChanged)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onSettingPropertyChanged)

            self._width = self._global_container_stack.getProperty("machine_width", "value")
            self._height = self._global_container_stack.getProperty("machine_height", "value")
            self._depth = self._global_container_stack.getProperty("machine_depth", "value")

            self.rebuild()
