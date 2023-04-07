from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *


class IntegrateWidget(QWidget):
    def __init__(self):
        super(IntegrateWidget, self).__init__()

        self.data = []

        # Default Values
        self.integrate_min = 0
        self.integrate_max = 100

        # Integration Parameters
        self.integrate_min_text = QLineEdit(str(self.integrate_min))
        self.integrate_min_text.setValidator(QIntValidator())
        self.integrate_min_text.textChanged.connect(self._on_change_integration_window)
        self.integrate_max_text = QLineEdit(str(self.integrate_max))
        self.integrate_max_text.setValidator(QIntValidator())
        self.integrate_max_text.textChanged.connect(self._on_change_integration_window)

        # Apply Button
        self.hide_checkbox = QCheckBox("Hide")
        self.integrate_btn = QPushButton("Apply")
        self.integrate_btn.clicked.connect(self.apply_integration)

        # Sub Layouts
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Ch. min"))
        min_layout.addWidget(self.integrate_min_text)
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Ch. max"))
        max_layout.addWidget(self.integrate_max_text)
        apply_layout = QHBoxLayout()
        apply_layout.addWidget(self.integrate_btn)
        apply_layout.addWidget(self.hide_checkbox)

        # Main Layout
        layout = QVBoxLayout()
        layout.addLayout(min_layout)
        layout.addLayout(max_layout)
        layout.addLayout(apply_layout)
        self.setLayout(layout)

    def calculate_integration_window(self, data):
        if self.integrate_max > len(data) - 1:
            self.integrate_max = len(data) - 1
            self.integrate_max_text.setText(str(self.integrate_max))
        if self.integrate_min > len(data) - 1:
            self.integrate_min = len(data) - 1
            self.integrate_min_text.setText(str(self.integrate_min))
        #if self.integrate_min == self.integrate_max:
        #    return data[self.integrate_min]
        return sum([data[i] for i in range(self.integrate_min, self.integrate_max+1)])

    def _on_change_integration_window(self):
        try:
            emin = int(self.integrate_min_text.text())
            emax = int(self.integrate_max_text.text())

            if emin > emax or emin < 0 or emax < 0:
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
        if self.data:
            self.calculate_integration_window(self.data)

