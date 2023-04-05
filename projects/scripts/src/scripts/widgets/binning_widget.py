from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *


class BinningWidget(QWidget):
    def __init__(self):
        super(BinningWidget, self).__init__()

        # Default Values
        self.bin_min = 0
        self.bin_max = 24576
        self.bin_nb = 1024

        # Binning Parameters
        self.binning_min_textbox = QLineEdit(str(self.bin_min))
        self.binning_min_textbox.setValidator(QIntValidator())
        self.binning_min_textbox.textChanged.connect(self._on_change_binning_min)
        self.binning_max_textbox = QLineEdit(str(self.bin_max))
        self.binning_max_textbox.setValidator(QIntValidator())
        self.binning_max_textbox.textChanged.connect(self._on_change_binning_max)
        self.binning_nb_of_bins_textbox = QLineEdit(str(self.bin_nb))
        self.binning_nb_of_bins_textbox.setValidator(QIntValidator())
        self.binning_nb_of_bins_textbox.textChanged.connect(self._on_change_binning_nb_of_bins)

        # Apply Button
        self.apply_binning_btn = QPushButton("Apply")
        self.apply_binning_btn.clicked.connect(self.apply_binning)
        self.apply_enabled = {'min': True, 'max': True, 'nb': True}

        # Sub Layouts
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Min"))
        min_layout.addWidget(self.binning_min_textbox)
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max"))
        max_layout.addWidget(self.binning_max_textbox)
        nb_bins_layout = QHBoxLayout()
        nb_bins_layout.addWidget(QLabel("Nb. of bins"))
        nb_bins_layout.addWidget(self.binning_nb_of_bins_textbox)

        # Main Layout
        layout = QVBoxLayout()
        layout.addLayout(min_layout)
        layout.addLayout(max_layout)
        layout.addLayout(nb_bins_layout)
        layout.addWidget(self.apply_binning_btn)
        layout.addStretch()
        self.setLayout(layout)

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
        self.apply_binning_btn.setEnabled(min and max and nb)

    def apply_binning(self):
        """
        Sets the user input as binning values
        """
        self.bin_min = int(self.binning_min_textbox.text())
        self.bin_max = int(self.binning_max_textbox.text())
        self.bin_nb = int(self.binning_nb_of_bins_textbox.text())
