import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import requests
from matplotlib import animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


def get_caen_detectors():
    """
    Retrieves all Caen detectors
    """
    config = requests.get(f"http://localhost:8000/api/config").json()
    # print(config['rbs']['drivers']['caen']['detectors'])
    return config['rbs']['drivers']['caen']['detectors']


class Window(QDialog):

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # Detector Option
        self.detector_box = QComboBox()
        for d in get_caen_detectors():
            self.detector_box.addItem(d['identifier'], d)
        detector_lyt = QHBoxLayout()
        detector_lyt.addWidget(QLabel("Detector"))
        detector_lyt.addWidget(self.detector_box)
        detector_lyt.addStretch()

        # Binning Options
        self.bin_min = 0
        self.bin_max = 24576
        self.bin_nb = 1024
        self.binning_min_textbox = QLineEdit(str(self.bin_min))
        self.binning_min_textbox.setValidator(QIntValidator())
        self.binning_min_textbox.textChanged.connect(self._on_change_binning_min)
        self.binning_max_textbox = QLineEdit(str(self.bin_max))
        self.binning_max_textbox.setValidator(QIntValidator())
        self.binning_max_textbox.textChanged.connect(self._on_change_binning_max)
        self.binning_nb_of_bins_textbox = QLineEdit(str(self.bin_nb))
        self.binning_nb_of_bins_textbox.setValidator(QIntValidator())
        self.binning_nb_of_bins_textbox.textChanged.connect(self._on_change_binning_nb_of_bins)
        self.apply_binning_btn = QPushButton("Apply")
        self.apply_binning_btn.clicked.connect(self.apply_options)
        self.apply_enabled = {'min': True, 'max': True, 'nb': True}
        binning_lyt = QHBoxLayout()
        binning_lyt.addWidget(QLabel("Binning"))
        binning_lyt.addWidget(QLabel("Min"))
        binning_lyt.addWidget(self.binning_min_textbox)
        binning_lyt.addWidget(QLabel("Max"))
        binning_lyt.addWidget(self.binning_max_textbox)
        binning_lyt.addWidget(QLabel("Nb. of bins"))
        binning_lyt.addWidget(self.binning_nb_of_bins_textbox)
        binning_lyt.addWidget(self.apply_binning_btn)
        binning_lyt.addStretch()

        # Pause Button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.set_play_pause)

        # Acquisition Status
        self.pause_status = QLabel("Acquiring data...")

        # Pile-Up Status Message
        pile_up_lyt = QHBoxLayout()
        self.pile_up_text = QLabel("No pile-up [not functional]")
        self.icon_lbl = QLabel()
        icon = app.style().standardIcon(QStyle.SP_MessageBoxWarning)
        self.icon_lbl.setPixmap(icon.pixmap(24))
        self.icon_lbl.hide()
        pile_up_lyt.addWidget(self.icon_lbl)
        pile_up_lyt.addWidget(self.pile_up_text)
        pile_up_lyt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        status_lyt = QHBoxLayout()
        status_lyt.addWidget(self.pause_status)
        status_lyt.addLayout(pile_up_lyt)

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

        # Window Layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addLayout(detector_lyt)
        layout.addLayout(binning_lyt)
        layout.addWidget(self.pause_btn)
        layout.addLayout(status_lyt)
        layout.addWidget(self.canvas)
        layout.addStretch()
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

    def _on_change_binning_min(self):
        """
        Validation of user input value for binning minimum value
        """
        try:
            min = int(self.binning_min_textbox.text())
            max = int(self.binning_max_textbox.text())
            nb = int(self.binning_nb_of_bins_textbox.text())

            if min < 0 or min > max:
                self.binning_min_textbox.setStyleSheet("color: red")
                self.apply_enabled['min'] = False
            else:
                self.binning_min_textbox.setStyleSheet("")
                self.apply_enabled['min'] = True
            if nb > (max - min):
                self.binning_nb_of_bins_textbox.setStyleSheet("color: red")
                self.apply_enabled['nb'] = False
            else:
                self.binning_nb_of_bins_textbox.setStyleSheet("")
                self.apply_enabled['nb'] = True

        except Exception:
            print("Invalid values")
            self.apply_enabled['min'] = False
        self.refresh_apply_enabled()

    def _on_change_binning_max(self):
        """
        Validation of user input value for binning maximum value
        """
        try:
            min = int(self.binning_min_textbox.text())
            max = int(self.binning_max_textbox.text())
            nb = int(self.binning_nb_of_bins_textbox.text())

            if max < 0 or max < min:
                self.binning_max_textbox.setStyleSheet("color: red")
                self.apply_enabled['max'] = False
            else:
                self.binning_max_textbox.setStyleSheet("")
                self.apply_enabled['max'] = True
            if nb > (max - min):
                self.binning_nb_of_bins_textbox.setStyleSheet("color: red")
                self.apply_enabled['nb'] = False
            else:
                self.binning_nb_of_bins_textbox.setStyleSheet("")
                self.apply_enabled['nb'] = True

        except Exception:
            print("Invalid values")
            self.apply_enabled['max'] = False
        self.refresh_apply_enabled()

    def _on_change_binning_nb_of_bins(self):
        """
        Validation of user input value for number of bins
        """
        try:
            min = int(self.binning_min_textbox.text())
            max = int(self.binning_max_textbox.text())
            nb = int(self.binning_nb_of_bins_textbox.text())

            if nb <= 0 or nb > (max - min):
                self.binning_nb_of_bins_textbox.setStyleSheet("color: red")
                self.apply_enabled['nb'] = False
            else:
                self.binning_nb_of_bins_textbox.setStyleSheet("")
                self.apply_enabled['nb'] = True
        except Exception:
            print("Invalid values")
            self.apply_enabled['nb'] = False
        self.refresh_apply_enabled()

    def refresh_apply_enabled(self):
        """
        Decides whether the apply button should be enabled or disabled
        """
        min, max, nb = self.apply_enabled.values()
        # print(f"min {min} max {max} nb {nb}")
        self.apply_binning_btn.setEnabled(min and max and nb)

    def apply_options(self):
        """
        Sets the user input as binning values
        """
        self.bin_min = int(self.binning_min_textbox.text())
        self.bin_max = int(self.binning_max_textbox.text())
        self.bin_nb = int(self.binning_nb_of_bins_textbox.text())

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
        self.axes.set_title(f"Detector {self.detector_box.currentText()}")

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
        self.axes.plot(data)

    def get_data(self):
        """
        Retrieves data from the Waspy API (Mill)
        """
        while True:
            try:
                # data = requests.get(f"http://localhost:8000/api/rbs/caen/detector/{self.detector_box.currentText()}").json()
                board = self.detector_box.currentData()['board']
                channel = self.detector_box.currentData()['channel']
                data = requests.get(f"http://localhost:8000/api/rbs/caen/histogram/{board}/{channel}/pack/"
                                    f"{self.bin_min}-{self.bin_max}-{self.bin_nb}").json()
                self.check_pile_up()
            except Exception as e:
                data = None
            yield data

    def check_pile_up(self):
        """
        Retrieves whether the pile-up warning of Caen is triggered
        """
        if True:
            self.pile_up_text.setText("Pile-up detected! [not functional]")
            self.icon_lbl.show()
        else:
            self.pile_up_text.setText("No pile-up [not functional]")
            self.icon_lbl.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())
