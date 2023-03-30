import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import requests
from matplotlib import animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt



mill_url = "http://localhost:8000"
# mill_url = "https://169.254.150.100:8000"


def get_caen_detectors():
    """
    Retrieves all Caen detectors
    """
    config = requests.get(f"{mill_url}/api/config").json()
    return config['pellicle']['drivers']['caen']['detectors']


class Window(QDialog):

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # self.setMaximumHeight(660)

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
        self.apply_binning_btn.clicked.connect(self.apply_binning)
        self.apply_enabled = {'min': True, 'max': True, 'nb': True}
        binning_lyt = QHBoxLayout()
        binning_lyt.addWidget(QLabel("Binning:"))
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
        self.pause_btn.setMaximumWidth(100)

        # Acquisition Status
        self.pause_status = QLabel("Acquiring data...")

        # Pile-Up Status Message
        self.pile_up_text = QLabel("Pile-up counter: ")
        self.pile_up_value = QLabel("0")
        self.icon_lbl = QLabel()
        icon = app.style().standardIcon(QStyle.SP_MessageBoxWarning)
        self.icon_lbl.setPixmap(icon.pixmap(24))
        self.icon_lbl.hide()
        pile_up_lyt = QHBoxLayout()
        pile_up_lyt.addWidget(self.icon_lbl)
        pile_up_lyt.addWidget(self.pile_up_text)
        pile_up_lyt.addWidget(self.pile_up_value)
        pile_up_lyt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        status_lyt = QHBoxLayout()
        status_lyt.addWidget(self.pause_status)
        status_lyt.addLayout(pile_up_lyt)

        # Integration Window
        self.integrate_min = 0
        self.integrate_max = 100
        self.integrate_btn = QPushButton("Apply")
        self.integrate_btn.clicked.connect(self.apply_integration)
        self.integrate_min_text = QLineEdit(str(self.integrate_min))
        self.integrate_min_text.textChanged.connect(self._on_change_integration_window)
        self.integrate_max_text = QLineEdit(str(self.integrate_max))
        self.integrate_max_text.textChanged.connect(self._on_change_integration_window)
        self.integrate_value = QLabel("5")
        integrate_lyt = QHBoxLayout()
        integrate_lyt.addWidget(QLabel("Integrate window: "))
        integrate_lyt.addWidget(QLabel("Emin"))
        integrate_lyt.addWidget(self.integrate_min_text)
        integrate_lyt.addWidget(QLabel("Emax"))
        integrate_lyt.addWidget(self.integrate_max_text)
        integrate_lyt.addWidget(self.integrate_btn)
        integrate_lyt.addWidget(QLabel("| Value"))
        integrate_lyt.addWidget(self.integrate_value)

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
        layout.addWidget(self.toolbar)
        layout.addLayout(detector_lyt)
        layout.addLayout(binning_lyt)
        layout.addLayout(integrate_lyt)
        layout.addWidget(self.pause_btn)
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

        except ValueError:
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

        except ValueError:
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

        except ValueError:
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

    def apply_binning(self):
        """
        Sets the user input as binning values
        """
        self.bin_min = int(self.binning_min_textbox.text())
        self.bin_max = int(self.binning_max_textbox.text())
        self.bin_nb = int(self.binning_nb_of_bins_textbox.text())

    def _on_change_integration_window(self):
        try:
            emin = int(self.integrate_min_text.text())
            emax = int(self.integrate_max_text.text())

            if emin >= emax:
                self.integrate_min_text.setStyleSheet("color: red")
                self.integrate_max_text.setStyleSheet("color: red")
                self.integration_apply_enabled = False
            else:
                self.integrate_min_text.setStyleSheet("")
                self.integrate_max_text.setStyleSheet("")
                self.integration_apply_enabled = True

        except ValueError:
            print("Invalid values")
            self.integration_apply_enabled = False

        self.refresh_integration_apply_enabled()

    def refresh_integration_apply_enabled(self):
        self.integrate_btn.setEnabled(self.integration_apply_enabled)

    def apply_integration(self):
        self.integrate_min = int(self.integrate_min_text.text())
        self.integrate_max = int(self.integrate_max_text.text())

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

    def calculate_integration_window(self, data):
        self.integrate_value.setText(str(sum([data[i] for i in range(self.integrate_min, self.integrate_max)])))

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
        self.calculate_integration_window(data)

    def get_data(self):
        """
        Retrieves data from the Waspy API (Mill)
        """
        while True:
            try:
                board = self.detector_box.currentData()['board']
                channel = self.detector_box.currentData()['channel']
                data = requests.get(f"{mill_url}/api/pellicle/caen/histogram/{board}/{channel}/pack/"
                                    f"{self.bin_min}-{self.bin_max}-{self.bin_nb}").json()

                # self.check_pile_up(board, channel)
            except Exception as e:
                data = None
            yield data

    def check_pile_up(self, board, channel):
        caen_status = requests.get(f"{mill_url}/api/pellicle/caen/").json()
        self.pile_up_value.setText(str(caen_status['boards'][board]['channels'][channel]['pile_up']))
        if int(self.pile_up_value.text()) > 0:
            self.pile_up_value.setStyleSheet("color: red")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())
