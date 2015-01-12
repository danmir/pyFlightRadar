from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebKit import *
from PyQt5.QtWidgets import *
from PyQt5 import QtGui, Qt
from PyQt5.QtWebKitWidgets import *
import os, json, sys


class FromToIataFilterWidget(QWidget):
    def __init__(self, main_window, flapi):
        super(FromToIataFilterWidget, self).__init__()
        self.main_window = main_window
        self.flapi = flapi

        self.qle = QLineEdit(self)
        self.find_button_from = QPushButton("From IATA find", self)
        self.find_button_to = QPushButton("To IATA find", self)
        self.reset_button = QPushButton("Reset button", self)

        layout = QHBoxLayout()
        layout.addWidget(self.find_button_from)
        layout.addWidget(self.qle)
        layout.addWidget(self.find_button_to)
        layout.addWidget(self.reset_button)
        self.setLayout(layout)

        # self.qle.textChanged[str].connect(self.on_changed)
        self.find_button_from.clicked.connect(self.on_clicked_from)
        self.find_button_to.clicked.connect(self.on_clicked_to)
        self.reset_button.clicked.connect(self.reset)

    def on_changed(self, text):
        self.lbl.setText(text)
        self.lbl.adjustSize()

    def reset(self):
        self.main_window.to_filter = False
        self.main_window.from_filter = False
        frame = self.main_window.web.page().mainFrame()
        frame.evaluateJavaScript('repaint_by_hand()')

    def check_iata(self, iata):
        iata = self.qle.text()
        data = self.flapi.is_there_airport_with_iata(iata)
        if not data:
            msgBox = QMessageBox()
            msgBox.setText("Аэропотра с таким кодом IATA нет")
            msgBox.setModal(True)
            msgBox.setInformativeText("Возможно вы перепутали с кодом ICAO")
            msgBox.setStandardButtons(QMessageBox.Ok)
            ret = msgBox.exec_()
            return False
        return True

    def on_clicked_from(self):
        from_iata = self.qle.text()
        if self.check_iata(from_iata):
            self.main_window.from_filter = True
            self.main_window.to_filter = False
            self.main_window.from_filter_iata = from_iata

            frame = self.main_window.web.page().mainFrame()
            frame.evaluateJavaScript('repaint_by_hand()')

    def on_clicked_to(self):
        to_iata = self.qle.text()
        if self.check_iata(to_iata):
            self.main_window.to_filter = True
            self.main_window.from_filter = False
            self.main_window.to_filter_iata = to_iata

            frame = self.main_window.web.page().mainFrame()
            frame.evaluateJavaScript('repaint_by_hand()')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FromToIataFilterWidget()
    window.show()
    sys.exit(app.exec_())
