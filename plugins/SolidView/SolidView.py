# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.View.RenderBatch import RenderBatch

from UM.View.GL.OpenGL import OpenGL

from nk import PathResultDecorator


## Standard view for mesh models. 
class SolidView(View):
    def __init__(self):
        super().__init__()

        self._shader = None

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "mesh.shader"))

        for node in DepthFirstIterator(scene.getRoot()):
            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    if node.getDecorator(PathResultDecorator.PathResultDecorator):
                        renderer.queueNode(node, shader=self._shader, mode=RenderBatch.RenderMode.Lines)
                    else:
                        renderer.queueNode(node, shader=self._shader)
                if node.callDecoration("isGroup"):
                    renderer.queueNode(scene.getRoot(), mesh=node.getBoundingBoxMesh(), mode=RenderBatch.RenderMode.LineLoop)

    def endRendering(self):
        pass
