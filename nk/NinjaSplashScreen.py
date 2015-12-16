# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QFont
from PyQt5.QtWidgets import QSplashScreen

from UM.Resources import Resources
from UM.Application import Application

class NinjaSplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setPixmap(QPixmap(Resources.getPath(Resources.Images, "nk.png")))
