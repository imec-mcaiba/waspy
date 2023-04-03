import sys

from PyQt5.QtWidgets import *
from widgets.plot_live_spectrum import PlotLiveSpectrum
from widgets.plot_upload_spectrum import PlotUploadSpectrum


class Window(QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.setFixedHeight(760)
        self.setFixedWidth(800)

        self.live_data_btn = QPushButton("Live Data")
        self.live_data_btn.clicked.connect(self.on_click_live_data_btn)
        self.live_data_btn.setStyleSheet("background-color: CornflowerBlue")
        self.upload_data_btn = QPushButton("Upload Data")
        self.upload_data_btn.clicked.connect(self.on_click_upload_data_btn)
        tabs_layout = QHBoxLayout()
        tabs_layout.addWidget(self.live_data_btn)
        tabs_layout.addWidget(self.upload_data_btn)

        self.live_data = PlotLiveSpectrum()
        self.upload_data = PlotUploadSpectrum()
        self.upload_data.hide()

        layout = QVBoxLayout()
        layout.addLayout(tabs_layout)
        layout.addWidget(self.live_data)
        layout.addWidget(self.upload_data)
        layout.addStretch()
        self.setLayout(layout)

    def on_click_live_data_btn(self):
        self.live_data.show()
        self.upload_data.hide()

        self.live_data_btn.setStyleSheet("background-color: CornflowerBlue")
        self.upload_data_btn.setStyleSheet("")
        return

    def on_click_upload_data_btn(self):
        self.live_data.hide()
        self.upload_data.show()

        self.live_data_btn.setStyleSheet("")
        self.upload_data_btn.setStyleSheet("background-color: CornflowerBlue")
        return

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())
