import os
import threading
import queue
import imp

from UM.Preferences import Preferences
from UM.Resources import Resources
from UM.Logger import Logger
from UM.Application import Application
from UM.Settings.MachineInstance import MachineInstance


# Helper function to load the modules of plugins. As we cannot get a reference to the modules from the plugin manager
def loadPlugin(id):
    file, path, desc = imp.find_module(id, [ os.path.join(os.path.dirname(__file__), "plugins") ])
    return imp.load_module(id, file, path, desc)


# Get references to objects we need to use for headless processing
NinjaJob = loadPlugin("NinjaKittenBackend").NinjaJob
TrotecFileWriter = loadPlugin("TrotecWriter").TrotecFileWriter


class HeadlessApplication(Application):
    def __init__(self):
        # Hack to prevent Uranium to create config directories
        Resources.getStoragePathForType = lambda type: "NO_PATH"
        # Search in our own path for plugins and stuff
        Resources.addSearchPath(os.path.join(os.path.abspath(os.path.dirname(__file__))))
        super().__init__(name="nk_headless", version="1.0")
        # Do not load the FileLogger (yes, more hacks)
        self.getPluginRegistry()._plugins['FileLogger'] = None
        self.getPluginRegistry().addPluginLocation(os.path.join(os.path.abspath(os.path.dirname(__file__)), "plugins"))
        self.getPluginRegistry().loadPlugins()

        # Add machines so we
        manager = self.getMachineManager()
        manager.loadAll()
        for machine_definition in manager.getMachineDefinitions():
            if machine_definition.isVisible():
                manager.addMachineInstance(MachineInstance(manager, name=machine_definition.getName(), definition=machine_definition))
        if manager.getActiveMachineInstance() is None:
            manager.setActiveMachineInstance(manager.getMachineInstance(0))
        manager.setActiveProfile(manager.getProfiles()[0])

    def run(self):
        #self.processFile("C:/??.dxf")
        pass

    def processFile(self, filename):
        Logger.log("i", "Loading mesh: %s", filename)
        node = self.getMeshFileHandler().read(filename, center=True)

        Logger.log("i", "Running job")
        job = NinjaJob.NinjaJob(node, Application.getInstance().getMachineManager().getActiveProfile())
        job.run()

        if job.getResult() is not None:
            Logger.log("i", "Going to write output")
            output_filename = "%s.tsf" % (filename)
            stream = open(output_filename, "wb")
            writer = TrotecFileWriter.TrotecFileWriter(output_filename)
            writer.write(stream, job.getResult())
            stream.close()
        else:
            output_filename = "%s.error.txt" % (filename)
            stream = open(output_filename, "wt")
            stream.write(job.getError())
            stream.close()
        Logger.log("i", "Finished")

    def functionEvent(self, event):
        pass #ignore all events, we are running synchronized


if __name__ == "__main__":
    app = HeadlessApplication.getInstance()
    app.run()
