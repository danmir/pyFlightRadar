from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebKit import *
from PyQt5.QtWidgets import *
from PyQt5 import QtGui, Qt
from PyQt5.QtWebKitWidgets import *
import os, json, sys


class FlightFinderWidget(QWidget):
    def __init__(self, main_window, flapi):
        super(FlightFinderWidget, self).__init__()
        self.main_window = main_window
        self.flapi = flapi

        self.lbl = QLabel("Flight number ", self)
        self.qle = QLineEdit(self)
        self.find_button = QPushButton("Find", self)

        layout = QHBoxLayout()
        layout.addWidget(self.lbl)
        layout.addWidget(self.qle)
        layout.addWidget(self.find_button)
        self.setLayout(layout)

        # self.qle.textChanged[str].connect(self.on_changed)
        self.find_button.clicked.connect(self.on_clicked)

    def on_clicked(self):
        data = self.flapi.get_aircrafts_by_flight_num(self.qle.text())
        if data == "No such flight":
            msgBox = QMessageBox()
            msgBox.setText("Такого рейса не найдено")
            msgBox.setModal(True)
            msgBox.setInformativeText("Возможно вы ввели не тот номер. Есть, допустим, рейс Aeroflot SU1501 и он же AFL1501 ")
            msgBox.setStandardButtons(QMessageBox.Ok)
            ret = msgBox.exec_()
        else:
            # Stop timer
            self.main_window.main_timer.stop()
            # Set map to plane position
            frame = self.main_window.web.page().mainFrame()
            frame.evaluateJavaScript('var pos = new google.maps.LatLng({}, {}); map.setCenter(pos);'.format(data[1], data[2]))
            frame.evaluateJavaScript('repaint_by_hand()')
            # print(data[18])
            frame.evaluateJavaScript('show_marker_by_flight_id("{}")'.format(data[18]))
            # Start updating timer again
            self.main_window.main_timer.start(3000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlightFinderWidget()
    window.show()
    sys.exit(app.exec_())