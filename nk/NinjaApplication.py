# Copyright (c) 2015 Ultimaker B.V.

from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Camera import Camera
from UM.Scene.Platform import Platform
from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion
from UM.Resources import Resources
from UM.Scene.ToolHandle import ToolHandle
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Mesh.ReadMeshJob import ReadMeshJob
from UM.Logger import Logger
from UM.Preferences import Preferences
from UM.JobQueue import JobQueue
from UM.Settings.MachineInstance import MachineInstance

from UM.Scene.Selection import Selection
from UM.Scene.GroupDecorator import GroupDecorator

from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.SetTransformOperation import SetTransformOperation

from UM.i18n import i18nCatalog

from . import BuildVolume
from . import CameraAnimation
from . import NinjaSplashScreen

from PyQt5.QtCore import pyqtSlot, QUrl, Qt, pyqtSignal, pyqtProperty, QEvent, Q_ENUMS
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtQml import qmlRegisterUncreatableType

import platform
import sys
import os
import os.path
import numpy
import copy
numpy.seterr(all="ignore")

if platform.system() == "Linux": # Needed for platform.linux_distribution, which is not available on Windows and OSX
    # For Ubuntu: https://bugs.launchpad.net/ubuntu/+source/python-qt4/+bug/941826
    if platform.linux_distribution()[0] in ("Ubuntu", ): # Just in case it also happens on Debian, so it can be added
        from OpenGL import GL

try:
    from nk.NinjaVersion import NinjaVersion
except ImportError:
    NinjaVersion = "master" # [CodeStyle: Reflecting imported value]


class NinjaApplication(QtApplication):
    class ResourceTypes:
        QmlFiles = Resources.UserType + 1
    Q_ENUMS(ResourceTypes)

    def __init__(self):
        Resources.addSearchPath(os.path.join(QtApplication.getInstallPrefix(), "share", "nk"))
        if not hasattr(sys, "frozen"):
            Resources.addSearchPath(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))

        super().__init__(name="nk", version=NinjaVersion)

        self.setWindowIcon(QIcon(Resources.getPath(Resources.Images, "nk-icon.png")))

        self.setRequiredPlugins([
            "NinjaKittenBackend",
            "MeshView",
            "STLReader",
            "SelectionTool",
            "CameraTool",
            "TrotecWriter",
            "LocalFileOutputDevice"
        ])
        self._volume = None
        self._platform = None
        self._output_devices = {}
        self._i18n_catalog = None
        self._previous_active_tool = None
        self._platform_activity = False
        self._job_name = None

        self.getController().getScene().sceneChanged.connect(self.updatePlatformActivity)

        Resources.addType(self.ResourceTypes.QmlFiles, "qml")

        Preferences.getInstance().addPreference("nk/active_machine", "")
        Preferences.getInstance().addPreference("nk/active_mode", "simple")
        Preferences.getInstance().addPreference("nk/recent_files", "")
        Preferences.getInstance().addPreference("nk/categories_expanded", "")
        Preferences.getInstance().addPreference("view/center_on_select", True)
        Preferences.getInstance().addPreference("mesh/scale_to_fit", True)

        JobQueue.getInstance().jobFinished.connect(self._onJobFinished)

        self._recent_files = []
        files = Preferences.getInstance().getValue("nk/recent_files").split(";")
        for f in files:
            if not os.path.isfile(f):
                continue

            self._recent_files.append(QUrl.fromLocalFile(f))

        self._addAllMachines()

    def _addAllMachines(self):
        # Check if there is an instance of each known machine, else add it
        manager = self.getMachineManager()
        for machine_definition in manager.getMachineDefinitions():
            if machine_definition.isVisible():
                if manager.findMachineInstance(machine_definition.getName()) is None:
                    manager.addMachineInstance(MachineInstance(manager, name=machine_definition.getName(), definition=machine_definition))
        # No machine selected? Select the first one
        if manager.getActiveMachineInstance() is None:
            manager.setActiveMachineInstance(manager.getMachineInstance(0))

    ##  Handle loading of all plugin types (and the backend explicitly)
    #   \sa PluginRegistery
    def _loadPlugins(self):
        self._plugin_registry.addPluginLocation(os.path.join(QtApplication.getInstallPrefix(), "lib", "nk"))
        if not hasattr(sys, "frozen"):
            self._plugin_registry.addPluginLocation(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "plugins"))
            self._plugin_registry.loadPlugin("ConsoleLogger")

        self._plugin_registry.loadPlugins()

        if self.getBackend() is None:
            raise RuntimeError("Could not load the backend plugin!")

    def addCommandLineOptions(self, parser):
        super().addCommandLineOptions(parser)
        parser.add_argument("file", nargs="*", help="Files to load after starting the application.")
        parser.add_argument("--debug", dest="debug-mode", action="store_true", default=False, help="Enable detailed crash reports.")

    def run(self):
        self._i18n_catalog = i18nCatalog("nk")

        i18nCatalog.setTagReplacements({
            "filename": "font color=\"black\"",
            "message": "font color=UM.Theme.colors.message_text;",
        })

        self.showSplashMessage(self._i18n_catalog.i18nc("@info:progress", "Setting up scene..."))

        controller = self.getController()

        controller.setActiveView("SolidView")
        controller.setCameraTool("CameraTool")
        controller.setSelectionTool("SelectionTool")

        t = controller.getTool("TranslateTool")
        if t:
            t.setEnabledAxis([ToolHandle.XAxis, ToolHandle.ZAxis])

        Selection.selectionChanged.connect(self.onSelectionChanged)

        root = controller.getScene().getRoot()
        self._platform = Platform(root)

        self._volume = BuildVolume.BuildVolume(root)

        self.getRenderer().setBackgroundColor(QColor(245, 245, 245))

        camera = Camera("3d", root)
        camera.setPosition(Vector(-80, 950, 700))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0))
        controller.getScene().setActiveCamera("3d")

        self.getController().getTool("CameraTool").setOrigin(Vector(0, 0, 0))

        self._camera_animation = CameraAnimation.CameraAnimation()
        self._camera_animation.setCameraTool(self.getController().getTool("CameraTool"))

        self.showSplashMessage(self._i18n_catalog.i18nc("@info:progress", "Loading interface..."))

        self.setMainQml(Resources.getPath(self.ResourceTypes.QmlFiles, "NinjaKittens.qml"))
        self.initializeEngine()

        if self._engine.rootObjects:
            self.closeSplash()

            for file in self.getCommandLineOption("file", []):
                self._openFile(file)

            self.exec_()

    #   Handle Qt events
    def event(self, event):
        if event.type() == QEvent.FileOpen:
            self._openFile(event.file())

        return super().event(event)

    def registerObjects(self, engine):
        engine.rootContext().setContextProperty("App", self)

        qmlRegisterUncreatableType(NinjaApplication, "NinjaKittens", 1, 0, "ResourceTypes", "Just an Enum type")

    def onSelectionChanged(self):
        if Selection.hasSelection():
            if not self.getController().getActiveTool():
                if self._previous_active_tool:
                    self.getController().setActiveTool(self._previous_active_tool)
                    self._previous_active_tool = None
                else:
                    self.getController().setActiveTool("TranslateTool")
            if Preferences.getInstance().getValue("view/center_on_select"):
                self._camera_animation.setStart(self.getController().getTool("CameraTool").getOrigin())
                self._camera_animation.setTarget(Selection.getSelectedObject(0).getWorldPosition())
                self._camera_animation.start()
        else:
            if self.getController().getActiveTool():
                self._previous_active_tool = self.getController().getActiveTool().getPluginId()
                self.getController().setActiveTool(None)
            else:
                self._previous_active_tool = None

    requestAddPrinter = pyqtSignal()
    activityChanged = pyqtSignal()

    @pyqtProperty(bool, notify = activityChanged)
    def getPlatformActivity(self):
        return self._platform_activity

    def updatePlatformActivity(self, node = None):
        count = 0
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            count += 1

        self._platform_activity = True if count > 0 else False
        self.activityChanged.emit()

    @pyqtSlot(str)
    def setJobName(self, name):
        if self._job_name != name:
            self._job_name = name
            self.jobNameChanged.emit()

    jobNameChanged = pyqtSignal()

    @pyqtProperty(str, notify = jobNameChanged)
    def jobName(self):
        return self._job_name

    ##  Remove an object from the scene
    @pyqtSlot("quint64")
    def deleteObject(self, object_id):
        node = self.getController().getScene().findObject(object_id)

        if not node and object_id != 0: #Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if node:
            if node.getParent():
                group_node = node.getParent()
                if not group_node.callDecoration("isGroup"):
                    op = RemoveSceneNodeOperation(node)
                else:
                    while group_node.getParent().callDecoration("isGroup"):
                        group_node = group_node.getParent()
                    op = RemoveSceneNodeOperation(group_node)
            op.push()

    ##  Create a number of copies of existing object.
    @pyqtSlot("quint64", int)
    def multiplyObject(self, object_id, count):
        node = self.getController().getScene().findObject(object_id)

        if not node and object_id != 0: #Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if node:
            op = GroupedOperation()
            for i in range(count):
                if node.getParent() and node.getParent().callDecoration("isGroup"):
                    new_node = copy.deepcopy(node.getParent()) #Copy the group node.
                    new_node.callDecoration("setConvexHull",None)

                    op.addOperation(AddSceneNodeOperation(new_node,node.getParent().getParent()))
                else:
                    new_node = copy.deepcopy(node)
                    new_node.callDecoration("setConvexHull", None)
                    op.addOperation(AddSceneNodeOperation(new_node, node.getParent()))

            op.push()

    ##  Center object on platform.
    @pyqtSlot("quint64")
    def centerObject(self, object_id):
        node = self.getController().getScene().findObject(object_id)
        if not node and object_id != 0: #Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if not node:
            return

        if node.getParent() and node.getParent().callDecoration("isGroup"):
            node = node.getParent()

        if node:
            op = SetTransformOperation(node, Vector())
            op.push()
    
    ##  Delete all mesh data on the scene.
    @pyqtSlot()
    def deleteAll(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue #Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue #Grouped nodes don't need resetting as their parent (the group) is resetted)
            nodes.append(node)
        if nodes:
            op = GroupedOperation()

            for node in nodes:
                op.addOperation(RemoveSceneNodeOperation(node))

            op.push()

    ## Reset all transformations on nodes with mesh data. 
    @pyqtSlot()
    def resetAll(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue #Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue #Grouped nodes don't need resetting as their parent (the group) is resetted)
            nodes.append(node)

        if nodes:
            op = GroupedOperation()

            for node in nodes:
                # Ensure that the object is above the build platform
                op.addOperation(SetTransformOperation(node, Vector(0,0,0), Quaternion(), Vector(1, 1, 1)))

            op.push()

    ##  Get logging data of the backend engine
    #   \returns \type{string} Logging data
    @pyqtSlot(result=str)
    def getEngineLog(self):
        log = ""

        for entry in self.getBackend().getLog():
            log += entry.decode()

        return log

    recentFilesChanged = pyqtSignal()

    @pyqtProperty("QVariantList", notify = recentFilesChanged)
    def recentFiles(self):
        return self._recent_files

    @pyqtSlot("QStringList")
    def setExpandedCategories(self, categories):
        categories = list(set(categories))
        categories.sort()
        joined = ";".join(categories)
        if joined != Preferences.getInstance().getValue("nk/categories_expanded"):
            Preferences.getInstance().setValue("nk/categories_expanded", joined)
            self.expandedCategoriesChanged.emit()

    expandedCategoriesChanged = pyqtSignal()

    @pyqtProperty("QStringList", notify = expandedCategoriesChanged)
    def expandedCategories(self):
        return Preferences.getInstance().getValue("nk/categories_expanded").split(";")

    @pyqtSlot(str, result = "QVariant")
    def getSettingValue(self, key):
        if not self.getMachineManager().getActiveProfile():
            return None
        return self.getMachineManager().getActiveProfile().getSettingValue(key)
        #return self.getActiveMachine().getSettingValueByKey(key)
    
    ##  Change setting by key value pair
    @pyqtSlot(str, "QVariant")
    def setSettingValue(self, key, value):
        if not self.getMachineManager().getActiveProfile():
            return

        self.getMachineManager().getActiveProfile().setSettingValue(key, value)
        
    @pyqtSlot()
    def groupSelected(self):
        group_node = SceneNode()
        group_decorator = GroupDecorator()
        group_node.addDecorator(group_decorator)
        group_node.setParent(self.getController().getScene().getRoot())
        center = Selection.getSelectionCenter()
        group_node.setPosition(center)
        group_node.setCenterPosition(center)

        for node in Selection.getAllSelectedObjects():
            world = node.getWorldPosition()
            node.setParent(group_node)
            node.setPosition(world - center)

        for node in group_node.getChildren():
            Selection.remove(node)

        Selection.add(group_node)

    @pyqtSlot()
    def ungroupSelected(self):
        ungrouped_nodes = []
        selected_objects = Selection.getAllSelectedObjects()[:] #clone the list
        for node in selected_objects:
            if node.callDecoration("isGroup" ):
                children_to_move = []
                for child in node.getChildren():
                    if type(child) is SceneNode:
                        children_to_move.append(child)

                for child in children_to_move:
                    position = child.getWorldPosition()
                    child.setParent(node.getParent())
                    child.setPosition(position - node.getParent().getWorldPosition())
                    child.scale(node.getScale())
                    child.rotate(node.getOrientation())

                    Selection.add(child)
                    child.callDecoration("setConvexHull",None)
                node.setParent(None)
                ungrouped_nodes.append(node)
        for node in ungrouped_nodes:
            Selection.remove(node)

    def _createSplashScreen(self):
        return NinjaSplashScreen.NinjaSplashScreen()

    def _onFileLoaded(self, job):
        node = job.getResult()
        if node != None:
            node.setSelectable(True)
            node.setName(os.path.basename(job.getFileName()))

            op = AddSceneNodeOperation(node, self.getController().getScene().getRoot())
            op.push()

            self.getController().getScene().sceneChanged.emit(node) #Force scene change.

    def _onJobFinished(self, job):
        if type(job) is not ReadMeshJob or not job.getResult():
            return

        f = QUrl.fromLocalFile(job.getFileName())
        if f in self._recent_files:
            self._recent_files.remove(f)

        self._recent_files.insert(0, f)
        if len(self._recent_files) > 10:
            del self._recent_files[10]

        pref = ""
        for path in self._recent_files:
            pref += path.toLocalFile() + ";"

        Preferences.getInstance().setValue("nk/recent_files", pref)
        self.recentFilesChanged.emit()

    def _openFile(self, file):
        job = ReadMeshJob(os.path.abspath(file))
        job.finished.connect(self._onFileLoaded)
        job.start()

    def _onAddMachineRequested(self):
        self.requestAddPrinter.emit()

    ##  Display text on the splash screen.
    def showSplashMessage(self, message):
        if self._splash:
            self._splash.showMessage(message, Qt.AlignHCenter | Qt.AlignBottom, Qt.white)
            self.processEvents()
