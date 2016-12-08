import os
import time
import argparse
import traceback

from UM.Logger import Logger

from plugins.DXFReader import DXFReader
from plugins.NinjaKittenBackend import NinjaJob
from plugins.TrotecWriter import TrotecFileWriter
from plugins.HtmlSvgWriter import HtmlSvgFileWriter

class HeadlessApplication:
    def __init__(self):
        self.__readers = [
            {"class": DXFReader.DXFReader},
        ]
        self.__writers = [
            {"class": TrotecFileWriter.TrotecFileWriter, "prefix": "Ts300_", "extension": ".tsf", "settings": {
                'tool_diameter': 0.1,
                'cut_method': 'cut_all_outside',
                'engrave_method': 'horizontal',
                'engrave_line_distance': 1.0,
            }},
            {"class": TrotecFileWriter.TrotecFileWriter, "prefix": "Ts300_engrave_", "extension": ".tsf", "settings": {
                'tool_diameter': 0.1,
                'cut_method': 'cut_outline_engrave_rest',
                'engrave_method': 'horizontal',
                'engrave_line_distance': 1.0,
            }},
            {"class": HtmlSvgFileWriter.HtmlSvgFileWriter, "prefix": "Debug_", "extension": ".html", "settings": {
                'tool_diameter': 0.1,
                'cut_method': 'cut_outline_engrave_rest',
                'engrave_method': 'horizontal',
                'engrave_line_distance': 1.0,
            }},
        ]

    def __formatFilename(self, full_path, prefix, extension):
        return os.path.join(os.path.dirname(full_path), "%s%s%s" % (prefix, os.path.basename(full_path), extension))

    def run(self, path):
        for reader in self.__readers:
            reader["instance"] = reader["class"]()
        while True:
            try:
                for filename in os.listdir(path):
                    full_path = os.path.join(path, filename)
                    if os.path.isfile(full_path):
                        if self.__needToProcessFile(full_path):
                            try:
                                self.__processFile(full_path)
                            except:
                                self.__writeException(self.__formatFilename(full_path, "", ".error.log"))
            except:
                self.__writeException(os.path.join(path, "_nk2.error.log"))
            time.sleep(15)

    def __needToProcessFile(self, full_path):
        for reader in self.__readers:
            if reader["instance"].acceptsFile(full_path):
                result_error_log_file = self.__formatFilename(full_path, "", ".error.log")
                if os.path.isfile(result_error_log_file):
                    return False
                for writer in self.__writers:
                    result_file = self.__formatFilename(full_path, writer["prefix"], writer["extension"])
                    result_error_log_file = self.__formatFilename(full_path, writer["prefix"], writer["extension"] + ".error.log")
                    if not os.path.isfile(result_file) and not os.path.isfile(result_error_log_file):
                        return True
                return False

    def __processFile(self, full_path):
        Logger.log("i", "Loading mesh: %s", full_path)
        node = None
        for reader in self.__readers:
            if reader["instance"].acceptsFile(full_path):
                node = reader["class"]().read(full_path)
                break

        for writer in self.__writers:
            result_file = self.__formatFilename(full_path, writer["prefix"], writer["extension"])
            result_error_log_file = self.__formatFilename(full_path, writer["prefix"], writer["extension"] + ".error.log")

            try:
                Logger.log("i", "Running job")
                job = NinjaJob.NinjaJob(node, writer["settings"])
                job.run()
                Logger.log("i", "Going to write output: %s", result_file)
                stream = open(result_file, "wb")
                writer = writer["class"](result_file)
                writer.write(stream, job.getResult())
                stream.close()
            except:
                self.__writeException(result_error_log_file)
        Logger.log("i", "Finished")

    def __writeException(self, filename):
        error_string = traceback.format_exc()
        Logger.log("e", error_string)
        stream = open(filename, "at")
        stream.write(error_string)
        stream.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('path')

    args = parser.parse_args()
    app = HeadlessApplication()
    app.run(args.path)
