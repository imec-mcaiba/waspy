import sys

from PyQt5.QtWidgets import *
from widgets.plot_live_spectrum import PlotLiveSpectrum
from widgets.plot_upload_spectrum import PlotUploadSpectrum

BUTTON_COLOR = "CornflowerBlue"


class Window(QDialog):
    def __init__(self, lab, data_file=None):
        super(Window, self).__init__()

        self.setFixedSize(760, 800)
        self.setWindowTitle("plot_histogram.py")

        # Window Buttons
        self.live_data_btn = QPushButton("Live Data")
        self.live_data_btn.clicked.connect(self.on_click_live_data_btn)
        self.live_data_btn.setStyleSheet(f"background-color: {BUTTON_COLOR}")
        self.upload_data_btn = QPushButton("Upload Data")
        self.upload_data_btn.clicked.connect(self.on_click_upload_data_btn)
        tabs_layout = QHBoxLayout()
        tabs_layout.addWidget(self.live_data_btn)
        tabs_layout.addWidget(self.upload_data_btn)

        # Windows
        self.live_data = PlotLiveSpectrum(lab)
        self.upload_data = PlotUploadSpectrum(data_file)
        self.upload_data.hide()

        # Main Layout
        layout = QVBoxLayout()
        layout.addLayout(tabs_layout)
        layout.addWidget(self.live_data)
        layout.addWidget(self.upload_data)
        layout.addStretch()
        self.setLayout(layout)

    def on_click_live_data_btn(self):
        self.live_data.show()
        self.upload_data.hide()

        self.live_data_btn.setStyleSheet(f"background-color: {BUTTON_COLOR}")
        self.upload_data_btn.setStyleSheet("")

    def on_click_upload_data_btn(self):
        self.live_data.hide()
        self.upload_data.show()

        self.live_data_btn.setStyleSheet("")
        self.upload_data_btn.setStyleSheet(f"background-color: {BUTTON_COLOR}")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    if len(sys.argv) >= 3:
        data_file = sys.argv[2]
    else: data_file = None

    try:
        main = Window(sys.argv[1], data_file)
    except IndexError:
        main = Window("dev")
    main.show()
    sys.exit(app.exec_())
