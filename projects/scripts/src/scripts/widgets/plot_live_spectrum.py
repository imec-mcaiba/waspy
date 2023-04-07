from PyQt5.QtWidgets import *
from matplotlib import pyplot as plt, animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from widgets.binning_widget import BinningWidget
from widgets.integrate_widget import IntegrateWidget

import requests


def get_caen_detectors(mill_url, measurement_type):
    """
    Retrieves all Caen detectors
    """
    try:
        config = requests.get(f"{mill_url}/api/config").json()
        return config[f'{measurement_type}']['drivers']['caen']['detectors']
    except requests.exceptions.ConnectionError:
        return []


class PlotLiveSpectrum(QWidget):
    def __init__(self, lab):
        super(PlotLiveSpectrum, self).__init__()

        if lab == "vdg":
            self.mill_url = "https://169.254.150.100:8000"
            self.measurement_type = "pellicle"
        elif lab == "imec":
            self.mill_url = "https://mill.capitan.imec.be"
            self.measurement_type = "rbs"
        else:
            self.mill_url = "http://localhost:8000"
            self.measurement_type = "rbs"

        # Detector Options
        self.detector_box = QComboBox()
        for d in get_caen_detectors(self.mill_url, self.measurement_type):
            self.detector_box.addItem(d['identifier'], d)
        detector_layout = QHBoxLayout()
        detector_layout.addWidget(QLabel("Detector"))
        detector_layout.addWidget(self.detector_box)
        detector_layout.addStretch()

        # Binning Widget
        self.binning = BinningWidget()
        binning_layout = QVBoxLayout()
        binning_layout.addWidget(self.binning)
        binning_box = QGroupBox("Binning")
        binning_box.setLayout(binning_layout)

        # Integration Widget
        self.integrate = IntegrateWidget()
        self.value_label = QLabel("Value: ")
        self.integrate_value = QLabel(str(0))
        integrate_value_layout = QHBoxLayout()
        integrate_value_layout.addWidget(self.value_label)
        integrate_value_layout.addWidget(self.integrate_value)
        integrate_value_layout.addStretch()

        integrate_layout = QVBoxLayout()
        integrate_layout.addWidget(self.integrate)
        integrate_layout.addLayout(integrate_value_layout)
        integrate_box = QGroupBox("Integration Window")
        integrate_box.setLayout(integrate_layout)

        # Pause Button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.set_play_pause)
        self.pause_btn.setMaximumWidth(100)

        # Acquisition Status
        self.pause_status = QLabel("Acquiring data...")
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.pause_status)

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

        # Binning and Integrate Layout
        binning_integrate_layout = QHBoxLayout()
        binning_integrate_layout.addWidget(binning_box)
        binning_integrate_layout.addWidget(integrate_box)

        # Main Layout
        layout = QVBoxLayout()
        layout.addLayout(detector_layout)
        layout.addLayout(binning_integrate_layout)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addLayout(status_layout)
        layout.setContentsMargins(0, 0, 0, 0)
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
            self.pause_status.setStyleSheet("")

    def on_click_home(self):
        self.axes.set_autoscale_on(True)
        self.autoscale = True

    def clear_plot(self):
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
        self.axes.set_xlabel("Channel")
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
            self.pause_status.setText("No data available")
            self.pause_status.setStyleSheet("color: red")
            self.axes.set_facecolor('lightgrey')
            return
        else:
            self.axes.set_facecolor('white')
        self.clear_plot()
        self.reset_axes()
        self.axes.set_title(f"Detector {self.detector_box.currentText()}")
        self.axes.plot(data)

        if data and not self.integrate.hide_checkbox.isChecked():
            self.axes.axvline(self.integrate.integrate_min, color="red", linestyle="dotted")
            self.axes.axvline(self.integrate.integrate_max, color="red", linestyle="dotted")
        self.integrate_value.setText(str(self.integrate.calculate_integration_window(data)))

    def get_data(self):
        """
        Retrieves data from the Waspy API (Mill)
        """
        while True:
            try:
                board = self.detector_box.currentData()['board']
                channel = self.detector_box.currentData()['channel']
                data = requests.get(f"{self.mill_url}/api/{self.measurement_type}/caen/histogram/{board}/{channel}/pack/"
                                    f"{self.binning.bin_min}-{self.binning.bin_max}-{self.binning.bin_nb}").json()

            except Exception as e:
                data = None
            yield data
