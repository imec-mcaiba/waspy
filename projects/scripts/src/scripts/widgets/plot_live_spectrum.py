from PyQt5.QtWidgets import *
from matplotlib import pyplot as plt, animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from widgets.binning_widget import BinningWidget
from widgets.integrate_widget import IntegrateWidget

import requests

mill_url = "http://localhost:8000"
# mill_url = "https://mill.capitan.imec.be"


def get_caen_detectors():
    """
    Retrieves all Caen detectors
    """
    config = requests.get(f"{mill_url}/api/config").json()
    return config['rbs']['drivers']['caen']['detectors']


class PlotLiveSpectrum(QWidget):
    def __init__(self):
        super(PlotLiveSpectrum, self).__init__()

        self.detector_box = QComboBox()
        for d in get_caen_detectors():
            self.detector_box.addItem(d['identifier'], d)
        detector_lyt = QHBoxLayout()
        detector_lyt.addWidget(QLabel("Detector"))
        detector_lyt.addWidget(self.detector_box)
        detector_lyt.addStretch()

        # Binning Widget
        self.binning = BinningWidget()

        # Pause Button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.set_play_pause)
        self.pause_btn.setMaximumWidth(100)

        # Acquisition Status
        self.pause_status = QLabel("Acquiring data...")
        status_lyt = QHBoxLayout()
        status_lyt.addWidget(self.pause_status)

        # Integration Window
        self.integrate = IntegrateWidget()

        # Variables
        self.pause = False
        self.autoscale = True

        # Plot
        self.fig = plt.figure()
        ax_size = [0.11, 0.20, 1 - 0.140, 1 - 0.27]
        self.axes = self.fig.add_axes(ax_size)
        self.axes.set_title(f"Detector {self.detector_box.currentText()}")
        self.reset_axes()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ani = animation.FuncAnimation(self.fig, self.consume_data,
                                           frames=self.get_data(),
                                           interval=1000,
                                           repeat=True,
                                           cache_frame_data=False,
                                           blit=False)
        self.canvas.draw()
        self.toolbar.actions()[0].triggered.connect(self.on_click_home)

        # Window Layout
        layout = QVBoxLayout()
        layout.addLayout(detector_lyt)
        layout.addWidget(self.binning)
        layout.addWidget(self.integrate)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addLayout(status_lyt)
        self.setLayout(layout)

    def set_play_pause(self):
        """
        Handles pausing/resuming the FuncAnimation plot together with user feedback messages.
        """
        self.pause = not self.pause
        if self.pause:
            self.ani.pause()
            self.pause_btn.setText("Resume")
            self.pause_status.setText("Paused")
        else:
            self.ani.resume()
            self.pause_btn.setText("Pause")
            self.pause_status.setText("Acquiring data...")

    def on_click_home(self):
        self.axes.set_autoscale_on(True)
        self.autoscale = True

    def clear(self):
        """
        Clears plot area but needs to take into account the zoom region and autoscale mode
        """
        x_lim = self.axes.get_xlim()
        y_lim = self.axes.get_ylim()

        if not self.axes.get_autoscale_on():
            self.autoscale = False

        self.axes.clear()

        if not self.autoscale:
            self.axes.set_xlim(x_lim)
            self.axes.set_ylim(y_lim)

    def reset_axes(self):
        """
        Resets the x and y-axis
        """
        self.axes.set_xlabel("Energy Level")
        self.axes.set_ylabel("Occurrence")
        self.axes.grid(which='both')
        self.axes.yaxis.set_ticks_position('left')
        self.axes.xaxis.set_ticks_position('bottom')

    def consume_data(self, data):
        """
        Parameters
        ----------
        data

        Manages refreshing the plot with new data
        """
        if data is None:
            print("No data available !!")
            self.axes.set_facecolor('lightgrey')
            return
        else:
            self.axes.set_facecolor('white')
        self.clear()
        self.reset_axes()
        self.axes.set_title(f"Detector {self.detector_box.currentText()}")
        self.axes.plot(data)
        self.integrate.calculate_integration_window(data)

    def get_data(self):
        """
        Retrieves data from the Waspy API (Mill)
        """
        while True:
            try:
                board = self.detector_box.currentData()['board']
                channel = self.detector_box.currentData()['channel']
                data = requests.get(f"{mill_url}/api/rbs/caen/histogram/{board}/{channel}/pack/"
                                    f"{self.binning.bin_min}-{self.binning.bin_max}-{self.binning.bin_nb}").json()

            except Exception as e:
                data = None
            yield data
