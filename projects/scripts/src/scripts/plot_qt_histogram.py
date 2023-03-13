import sys
import time
import random
import numpy as np

from PyQt5.QtWidgets import QPushButton, QLineEdit, QHBoxLayout, QComboBox, QGridLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasAgg, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

import matplotlib.pyplot as plt

from waspy.iba.rbs_entities import Detector


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        self.detector = Detector(board="33", channel=0, identifier="", bins_min=0, bins_max=8192,
                                     bins_width=1024)
        title_string = "Histogram board=" + self.detector.board + ", channel=" + str(self.detector.channel)
        self.fig = plt.figure(title_string)
        self.title_text = plt.figtext(0.20, 0.94, title_string, size='x-large', color='blue')

        dynamic_canvas = FigureCanvas(self.fig)
        layout.addWidget(dynamic_canvas)
        layout.addWidget(NavigationToolbar(dynamic_canvas, self))

        horizontal = QGridLayout()
        horizontal.addWidget(QLabel("Board"), 0, 0)
        horizontal.addWidget(QLabel("Channel"), 0, 1)
        horizontal.addWidget(QLabel("Bins min"), 0, 2)
        horizontal.addWidget(QLabel("Bins max"), 0, 3)
        horizontal.addWidget(QLabel("Bins width"), 0, 4)
        horizontal.addWidget(QLineEdit(), 1, 0)
        horizontal.addWidget(QLineEdit(), 1, 1)
        horizontal.addWidget(QLineEdit(), 1, 2)
        horizontal.addWidget(QLineEdit(), 1, 3)
        horizontal.addWidget(QLineEdit(), 1, 4)
        layout.addLayout(horizontal)

        layout.addWidget(QPushButton("Update values"))
        layout.addWidget(QPushButton("Play/Pause"))

        # self._dynamic_fig = dynamic_canvas.figure
        # ax_size = [0.11, 0.20, 1 - 0.110,
        #            1 - 0.27]  # [left, bottom, width, height] as fractions of figure width and height.
        # self._dyn_axes = self._dynamic_fig.add_axes(ax_size)

        self._axes = dynamic_canvas.figure.subplots()
        self._reset_axes()
        self._line, = self._axes.plot([], [])
        self._timer = dynamic_canvas.new_timer(1000)
        self._timer.add_callback(self._update_canvas)
        self._timer.start()

    def _reset_axes(self):
        self._axes.clear()
        self._axes.set_xlabel("Energy Level")
        self._axes.set_ylabel("Occurrence")
        self._axes.grid(which='both')
        self._axes.set_xlim(0, 1024)
        self._axes.set_ylim(0, 50000)
        # self._axes.yaxis.set_ticks_position('left')
        # self._axes.xaxis.set_ticks_position('bottom')

    def _update_canvas(self):
        print("get data")
        # resp_code, data = get_packed_histogram("http://localhost:20200/api/latest", self.detector)
        # self._reset_axes()

        data = [random.randrange(1, 50, 1) for i in range(1024)]

        x_values = range(len(data))

        # self._line.set_data(x_values, data)
        self._line.figure.canvas.draw()



if __name__ == "__main__":
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow()
    app.show()
    app.activateWindow()
    app.raise_()
    #qapp.sql_insert()
