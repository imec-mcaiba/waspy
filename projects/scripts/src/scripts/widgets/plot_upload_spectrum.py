import os
from pathlib import Path
import re

from PyQt5.QtWidgets import *
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from widgets.binning_widget import BinningWidget
from widgets.integrate_widget import IntegrateWidget


def parse_file(filename):
    yields = []
    energies = []
    with open(filename) as f:
        lines = f.readlines()
        for line in lines:
            reg_exp_line = "(\d*), (\d*)"
            re_data = re.search(reg_exp_line, line)
            if re_data:
                energies.append(int(re_data.group(1)))
                yields.append(int(re_data.group(2)))

    return yields, energies


class PlotUploadSpectrum(QWidget):
    def __init__(self):
        super(PlotUploadSpectrum, self).__init__()

        # Upload File
        file_browse = QPushButton('Browse')
        file_browse.clicked.connect(self.on_click_browse)
        self.filename_edit = QLineEdit()
        self.filename_edit.textChanged.connect(self.on_text_change)
        upload_layout = QHBoxLayout()
        upload_layout.addWidget(QLabel('Upload File:'))
        upload_layout.addWidget(self.filename_edit)
        upload_layout.addWidget(file_browse)

        # Binning Widget
        self.binning = BinningWidget()

        # Integration Window
        self.integrate = IntegrateWidget()

        # Status
        self.status = QLabel("No data uploaded.")

        # Plot
        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        ax_size = [0.11, 0.20, 1 - 0.140, 1 - 0.27]
        self.axes = self.fig.add_axes(ax_size)
        self.axes.set_xlabel("Energy Level")
        self.axes.set_ylabel("Occurrence")
        self.axes.grid(which='both')
        self.axes.yaxis.set_ticks_position('left')
        self.axes.xaxis.set_ticks_position('bottom')
        self.axes.set_facecolor('lightgrey')
        self.canvas.draw()

        # Window Layout
        layout = QVBoxLayout()
        layout.addLayout(upload_layout)
        # layout.addWidget(self.binning)
        layout.addWidget(self.integrate)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.status)
        self.setLayout(layout)

    def on_click_browse(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select a File", "C:\\")
        if filename:
            path = Path(filename)
            self.filename_edit.setText(str(path))

    def on_text_change(self):
        if os.path.isfile(self.filename_edit.text()):
            print("Parsing file...")
            self.status.setText(f"Plotting {self.filename_edit.text()}")
            self.filename_edit.setStyleSheet('')
            yields, energies = parse_file(self.filename_edit.text())
            self.plot_graph(yields, energies, os.path.basename(self.filename_edit.text()))

            self.integrate.data = yields
            self.integrate.calculate_integration_window(yields)

        else:
            self.filename_edit.setStyleSheet('color:red')
            print("Not a correct file name")

    def plot_graph(self, yields, energies, filename):
        self.axes.clear()
        self.axes.set_facecolor('white')
        self.axes.set_xlabel("Energy Level")
        self.axes.set_ylabel("Occurrence")
        self.axes.grid(which='both')
        self.axes.plot(energies, yields)
        self.axes.set_title(filename)
        self.canvas.draw()
