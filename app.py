#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5.uic import loadUi


class Example(QMainWindow):

    def __init__(self):
        super().__init__()

        loadUi("roboul_main.ui", self)

        self.description_label.setText("Qt's awesum")

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    roboul_main = Example()
    sys.exit(app.exec_())
