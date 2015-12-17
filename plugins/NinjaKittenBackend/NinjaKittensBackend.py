# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Backend.Backend import Backend
from UM.Application import Application
from UM.Scene.Scene import SceneNode
from UM.i18n import i18nCatalog

from PyQt5.QtCore import QTimer

from . import NinjaJob

catalog = i18nCatalog("nk")


class NinjaKittensBackend(Backend):
    def __init__(self):
        super().__init__()

        self._scene = Application.getInstance().getController().getScene()
        self._scene.sceneChanged.connect(self._onSceneChanged)

        Application.getInstance().getMachineManager().activeMachineInstanceChanged.connect(self._processScene)

        self._profile = None
        Application.getInstance().getMachineManager().activeProfileChanged.connect(self._onActiveProfileChanged)
        self._onActiveProfileChanged()

        self._change_timer = QTimer()
        self._change_timer.setInterval(100)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._runJob)

    def _onSceneChanged(self, source):
        if type(source) is not SceneNode:
            return

        if source is self._scene.getRoot():
            return

        if source.getMeshData() is None:
            return

        if source.hasDecoration("getPaths"):
            return

        self._processScene()

    def _onActiveProfileChanged(self):
        if self._profile:
            self._profile.settingValueChanged.disconnect(self._onSettingChanged)

        self._profile = Application.getInstance().getMachineManager().getActiveProfile()
        if self._profile:
            self._profile.settingValueChanged.connect(self._onSettingChanged)
            self._processScene()

    def _onSettingChanged(self, setting):
        self._processScene()

    # We have no external engine.
    def getEngineCommand(self):
        return None

    def forceSlice(self):   # hack called when node is removed...
        self._processScene()

    # Do not create a socket, as we do not connect to an external executable
    def _createSocket(self):
        pass

    def _processScene(self):
        self._change_timer.start()
        self.processingProgress.emit(0.0)

    def _runJob(self):
        job = NinjaJob.NinjaJob()
        job.start()
        self.processingProgress.emit(1.0)
