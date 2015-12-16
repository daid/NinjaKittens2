#!/usr/bin/env python3

# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import sys
import os

def exceptHook(type, value, traceback):
    import nk.CrashHandler
    nk.CrashHandler.show(type, value, traceback)

sys.excepthook = exceptHook

if True: # To make the code style checker stop complaining
    import nk.NinjaApplication

if sys.platform == "win32" and hasattr(sys, "frozen"):
    dirpath = os.path.expanduser("~/AppData/Local/nk/")
    os.makedirs(dirpath, exist_ok = True)
    sys.stdout = open(os.path.join(dirpath, "stdout.log"), "w")
    sys.stderr = open(os.path.join(dirpath, "stderr.log"), "w")

app = nk.NinjaApplication.NinjaApplication.getInstance()
app.run()
