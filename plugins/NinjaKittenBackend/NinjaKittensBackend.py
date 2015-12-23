# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import threading

from UM.Logger import Logger
from UM.Backend.Backend import Backend
from UM.Application import Application
from UM.Scene.Scene import SceneNode
from UM.i18n import i18nCatalog

from nk import PathResultDecorator

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

        self._change_timer = None

    def _onSceneChanged(self, source):
        if type(source) is not SceneNode:
            return

        if source is self._scene.getRoot():
            return

        if source.getMeshData() is None:
            return

        if source.getDecorator(PathResultDecorator.PathResultDecorator):
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
        if self._change_timer is not None:
            self._change_timer.cancel()
        self._change_timer = threading.Timer(0.5, self._runJob)
        self._change_timer.start()
        self.processingProgress.emit(0.0)

    def _runJob(self):
        job = NinjaJob.NinjaJob(Application.getInstance().getController().getScene().getRoot(), Application.getInstance().getMachineManager().getActiveProfile())
        job.progress.connect(self.processingProgress)
        job.finished.connect(self._onJobFinished)
        job.start()

    def _onJobFinished(self, job):
        result = job.getResult()
        if result is not None:
            result.setParent(self._scene.getRoot())
        if job.getError() is not None:
            Logger.log("e", "Error in Ninja job: %s", job.getError())
        self.processingProgress.emit(1.0)
