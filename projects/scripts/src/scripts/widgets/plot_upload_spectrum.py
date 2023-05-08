import os
import re
from pathlib import Path
from uuid import uuid4

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import *
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

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
    def __init__(self, data_file):
        super(PlotUploadSpectrum, self).__init__()

        self.data = []
        self.latest_dir = "C:\\"

        # Upload File Widget
        self.upload_btn = QPushButton('Upload File')
        self.upload_btn.setFixedWidth(100)
        self.upload_btn.clicked.connect(self.on_click_upload)
        self.status = QLabel("")
        upload_button_layout = QHBoxLayout()
        upload_button_layout.addWidget(self.upload_btn)
        upload_button_layout.addWidget(self.status)



        file_name_lbl = QLabel("File Name")
        integration_value_lbl = QLabel("Integration Value")
        space = QLabel("")
        space.setFixedWidth(80)

        column_layout = QHBoxLayout()
        column_layout.addWidget(file_name_lbl)
        column_layout.addWidget(integration_value_lbl)
        column_layout.addWidget(space)

        self.scrollLayout = QFormLayout()
        self.scrollWidget = QWidget()
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFixedHeight(100)
        self.scrollArea.setWidget(self.scrollWidget)

        upload_layout = QVBoxLayout()
        upload_layout.addLayout(upload_button_layout)
        upload_layout.addLayout(column_layout)
        upload_layout.addWidget(self.scrollArea)
        upload_box = QGroupBox("Upload Files")
        upload_box.setLayout(upload_layout)

        # Integration Widget
        self.integrate = IntegrateWidget()
        self.integrate.integrate_btn.clicked.connect(self.refresh_integration)
        self.integrate.hide_checkbox.stateChanged.connect(self.refresh_integration)
        integrate_layout = QHBoxLayout()
        integrate_layout.addWidget(self.integrate)
        integrate_box = QGroupBox("Integration Window")
        integrate_box.setLayout(integrate_layout)
        integrate_box.setFixedWidth(200)

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
        self.autoscale = True
        self.update_file_list()

        # Binning and Integrate Layout
        sub_layout = QHBoxLayout()
        sub_layout.addWidget(upload_box)
        sub_layout.addWidget(integrate_box)


        if data_file:
            self.init_data_file_upload(data_file)

        # Main Layout
        layout = QVBoxLayout()
        layout.addLayout(sub_layout)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


    def init_data_file_upload(self, filename):
        path = Path(filename)
        for d in self.data:
            if d['path'] == path:
                self.status.setText(f"File \"{d['file_name']}\" already uploaded")
                self.status.setStyleSheet('color: red')
                return
        try:
            yields, energies = parse_file(filename)
        except UnicodeDecodeError:
            self.status.setText(f"Cannot decode file \"{os.path.basename(filename)}\"")
            self.status.setStyleSheet('color: red')
            return
        new_data = {
            "id": uuid4(),
            "path": path,
            "file_name": os.path.basename(filename),
            "yields": yields,
            "energies": energies,
            "integrate_value": self.integrate.calculate_integration_window(yields)
        }
        self.data.append(new_data)
        self.update_file_list()
        self.status.setText(f"File \"{new_data['file_name']}\" uploaded")
        self.status.setStyleSheet('')

    def on_click_upload(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select a File", self.latest_dir)
        if filename:
            path = Path(filename)
            self.latest_dir = os.path.dirname(path)
            for d in self.data:
                if d['path'] == path:
                    self.status.setText(f"File \"{d['file_name']}\" already uploaded")
                    self.status.setStyleSheet('color: red')
                    return
            try:
                yields, energies = parse_file(filename)
            except UnicodeDecodeError:
                self.status.setText(f"Cannot decode file \"{os.path.basename(filename)}\"")
                self.status.setStyleSheet('color: red')
                return

            if len(yields) == 0 or len(energies) == 0:
                self.status.setText(f"Cannot decode file \"{os.path.basename(filename)}\"")
                self.status.setStyleSheet('color: red')
                return

            new_data = {
                "id": uuid4(),
                "path": path,
                "file_name": os.path.basename(filename),
                "yields": yields,
                "energies": energies,
                "integrate_value": self.integrate.calculate_integration_window(yields)
            }
            self.data.append(new_data)
            self.update_file_list()
            self.status.setText(f"File \"{new_data['file_name']}\" uploaded")
            self.status.setStyleSheet('')

    def update_file_list(self):
        # Clear scrollLayout
        while self.scrollLayout.rowCount() > 0:
            self.scrollLayout.removeRow(0)

        # Add widgets to scrollLayout
        for d in self.data:
            file_upload_widget = FileUploadWidget(d)
            self.scrollLayout.addRow(file_upload_widget)
        self.plot_graph()

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

        if not self.data:
            self.autoscale = True

        self.axes.clear()

        if not self.autoscale:
            self.axes.set_xlim(x_lim)
            self.axes.set_ylim(y_lim)

    def plot_graph(self):
        self.clear_plot()
        self.axes.set_facecolor('white')
        self.axes.set_xlabel("Channel")
        self.axes.set_ylabel("Occurrence")
        self.axes.grid(which='both')
        for d in self.data:
            self.axes.plot(d['energies'], d['yields'])
            self.axes.legend([d['file_name'] for d in self.data])
        if not self.data:
            self.axes.set_facecolor('lightgrey')
        elif not self.integrate.hide_checkbox.isChecked():
            self.axes.axvline(self.integrate.integrate_min, color="red", linestyle="dotted")
            self.axes.axvline(self.integrate.integrate_max, color="red", linestyle="dotted")
        self.canvas.draw()

    def refresh_integration(self):
        for d in self.data:
            d['integrate_value'] = self.integrate.calculate_integration_window(d['yields'])
        self.update_file_list()


class FileUploadWidget(QWidget):
    def __init__(self, data):
        super(FileUploadWidget, self).__init__()

        self.data = data

        self.file_name_lbl = QLabel(self.data['file_name'])
        self.integrate_value = QLabel(str(self.data['integrate_value']))
        self.remove_btn = QPushButton('remove')
        self.remove_btn.setFixedWidth(80)
        self.remove_btn.clicked.connect(self.on_remove)

        # Main Layout
        layout = QHBoxLayout()
        layout.addWidget(self.file_name_lbl)
        layout.addWidget(self.integrate_value)
        layout.addWidget(self.remove_btn)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def on_remove(self):
        for d in self.parent().parent().parent().parent().parent().data:
            if self.data['id'] == d["id"]:
                self.parent().parent().parent().parent().parent().data.remove(d)
        self.parent().parent().parent().parent().parent().plot_graph()
        self.parent().layout().removeRow(self)
