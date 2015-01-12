import os
import json
import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import *

from get_planes import FlightRadarAPI
from Widgets.flight_finder_widget import FlightFinderWidget
from Widgets.from_to_iata_filter_widget import FromToIataFilterWidget


def linear_list_search(inp_list, input_value):
    for l in inp_list:
        if l[0] == input_value:
            return l
    return -1


class DownloadThread(QThread):
    data_downloaded = pyqtSignal(object, object)

    def __init__(self, flapi, flights_inform):
        QThread.__init__(self)
        self.flights_inform = flights_inform
        self.flapi = flapi

    def run(self):
        full_data = self.flapi.get_aircraft_info(self.flights_inform[0])
        s_full_data = json.dumps(full_data)
        self.data_downloaded.emit(self.flights_inform, s_full_data)


class Browser(QWidget):
    def __init__(self):
        super(Browser, self).__init__()
        # QApplication.__init__(self, [])
        # self.window = QWidget()
        # self.window.setWindowTitle("pyFlightRadar")

        # Model
        self.flapi = FlightRadarAPI()
        self.all_planes = self.flapi.get_aircrafts()
        print(self.all_planes)

        # if filters is on
        self.from_filter = False
        self.to_filter = False
        self.from_filter_iata = None
        self.to_filter_iata = None

        pyDir = os.path.abspath(os.path.dirname(__file__))
        baseUrl = QUrl.fromLocalFile(os.path.join(pyDir, "map.html"))
        print(baseUrl)

        self.web = QWebView(self)
        self.web.setMinimumSize(800, 800)
        self.web.page().mainFrame().addToJavaScriptWindowObject('self', self)
        self.web.setUrl(baseUrl)

        # self.text = QTextEdit(self.window)

        # self.remove_all_planes_button = QPushButton("remove markers", self.window)
        # self.load_all_planes_button = QPushButton("load all planes (very slow)", self)
        self.get_me_to_ekb_button = QPushButton("Go to Ekb", self)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.web)
        # self.layout.addWidget(self.text)
        # self.layout.addWidget(self.remove_all_planes_button)
        # self.layout.addWidget(self.load_all_planes_button)
        self.layout.addWidget(self.get_me_to_ekb_button)

        self.flight_finder_widget = FlightFinderWidget(self, self.flapi)
        self.layout.addWidget(self.flight_finder_widget)

        self.from_to_iata_filter_widget = FromToIataFilterWidget(self, self.flapi)
        self.layout.addWidget(self.from_to_iata_filter_widget)

        # self.remove_all_planes_button.clicked.connect(self.remove_all_planes)
        # self.load_all_planes_button.clicked.connect(self.load_all_planes)
        self.get_me_to_ekb_button.clicked.connect(self.get_me_to_ekb)

        # Current state of map bounds
        self.lat_ne = None
        self.lng_ne = None
        self.lat_sw = None
        self.lng_sw = None

        # Save current aircrafts data
        self.aircrafts = None

        # self.window.show()
        # self.exec_()


    @pyqtSlot(float, float)
    def print_center(self, lat, lng):
        """
        Print current center of map. Calling from javascript
        :param lat: current map latitude
        :param lng: current map longitude
        """
        print(lat, lng)

    @pyqtSlot(float, float, float, float)
    def print_bounds(self, lat_ne, lng_ne, lat_sw, lng_sw):
        """
        Print current borders of map. Calling from javascript
        :param lat_ne: latitude north east
        :param lng_ne: longitude north east
        :param lat_sw: latitude south west
        :param lng_sw: longitude south west
        """
        print(lat_ne, lng_ne, lat_sw, lng_sw)

    @pyqtSlot(float, float, float, float)
    def load_aircrafts_by_bounds(self, lat_ne, lng_ne, lat_sw, lng_sw):
        """
        Getting and loading aircrafts by given bounds. Before that remove all planes on map.
        Works on bound changed event
        :param lat_ne: latitude north east
        :param lng_ne: longitude north east
        :param lat_sw: latitude south west
        :param lng_sw: longitude south west
        """
        # Save current state of map
        self.lat_ne = lat_ne
        self.lng_ne = lng_ne
        self.lat_sw = lat_sw
        self.lng_sw = lng_sw

        self.remove_all_planes()
        # if filters is set
        if self.from_filter:
            aircrafts = self.flapi.get_aircrafts_by_bounds(lat_ne, lat_sw, lng_sw, lng_ne, filter_type="from_iata",
                                                           iata=self.from_filter_iata)
        elif self.to_filter:
            aircrafts = self.flapi.get_aircrafts_by_bounds(lat_ne, lat_sw, lng_sw, lng_ne, filter_type="to_iata",
                                                           iata=self.to_filter_iata)
        else:
            aircrafts = self.flapi.get_aircrafts_by_bounds(lat_ne, lat_sw, lng_sw, lng_ne)

        # print(aircrafts)

        self.aircrafts = aircrafts

        self.threads = []
        if len(aircrafts):
            for aircraft in aircrafts:
                downloader = DownloadThread(self.flapi, aircraft)
                downloader.data_downloaded.connect(self.on_data_ready)
                self.threads.append(downloader)
                downloader.start()
                # 0 -flight_id, 2- latitude, 3 - longitude, 4 - track
                # self._add_marker(aircraft[0], aircraft[3], aircraft[2], aircraft[4])
                # print(aircraft)

    def on_data_ready(self, flights_inform, s_full_data):
        # print(flights_inform, s_full_data)
        self._add_marker(flights_inform[0], flights_inform[3], flights_inform[2], flights_inform[4], s_full_data)

    def refresh(self):
        """
        After initial loading refresh aircrafts positions on map. There are 3 options
        1) add aircraft
        2) update aircraft position
        3) remove aircraft (for ex. when landed)
        """
        # if filters is set
        if self.from_filter:
            new_aircrafts = self.flapi.get_aircrafts_by_bounds(self.lat_ne, self.lat_sw, self.lng_sw, self.lng_ne,
                                                               filter_type="from_iata",
                                                               iata=self.from_filter_iata)
        elif self.to_filter:
            new_aircrafts = self.flapi.get_aircrafts_by_bounds(self.lat_ne, self.lat_sw, self.lng_sw, self.lng_ne,
                                                               filter_type="to_iata",
                                                               iata=self.to_filter_iata)
        else:
            new_aircrafts = self.flapi.get_aircrafts_by_bounds(self.lat_ne, self.lat_sw, self.lng_sw, self.lng_ne)
        # print(new_aircrafts)
        new_aircrafts_set = set()
        for aircraft in new_aircrafts:
            new_aircrafts_set.add(aircraft[0])

        aircrafts_set = set()
        for aircraft in self.aircrafts:
            aircrafts_set.add(aircraft[0])

        for aircraft in new_aircrafts_set:
            if aircraft not in aircrafts_set:
                # Add new (Add new thread to download)
                data = linear_list_search(new_aircrafts, aircraft)
                downloader = DownloadThread(self.flapi, data)
                downloader.data_downloaded.connect(self.on_data_ready)
                self.threads.append(downloader)
                downloader.start()
                # self._add_marker(data[0], data[2], data[3], data[4])
            else:
                # Update
                data = linear_list_search(new_aircrafts, aircraft)
                self._move_marker(aircraft, data[2], data[3], data[4])
                aircrafts_set.remove(aircraft)

        if not len(aircrafts_set):
            for aircraft in aircrafts_set:
                # Delete
                self._remove_marker(aircraft)
        self.aircrafts = new_aircrafts

    # Markers work
    def _add_marker(self, flight_id, lat, lon, track, s_full_data):
        """
        Get detailed information on flight id
        Add aircraft on map
        :param flight_id: Flight id of a plane
        :param lat: plane curr latitude
        :param lon: plane curr longitude
        :param track: plane curr rotation
        :param s_full_data: detailed data about the flight in json format
        """
        # full_data = self.flapi.get_aircraft_info(flight_id)
        # s_full_data = json.dumps(full_data)

        frame = self.web.page().mainFrame()
        # print(lon, lat, track, s_full_data, flight_id)
        frame.evaluateJavaScript("addMarker({}, {}, {}, '{}', '{}')".format(lon, lat, track, s_full_data, flight_id))

    def _move_marker(self, flight_id, lat, lon, track):
        frame = self.web.page().mainFrame()
        frame.evaluateJavaScript('changeMarkerPos("{}", {}, {}, {})'.format(flight_id, lat, lon, track))

    def _remove_marker(self, flight_id):
        frame = self.web.page().mainFrame()
        frame.evaluateJavaScript('removeMarker("{}")'.format(flight_id))

    def remove_all_planes(self):
        frame = self.web.page().mainFrame()
        frame.evaluateJavaScript('clearOverlays()')

    def _plane_data_maker(self, data):
        pass

    @pyqtSlot()
    def loaded_complete(self):
        """
        Calling this function from javascript when "tilesloaded" event on google maps emmitTed
        """
        # frame = self.web.page().mainFrame()
        # frame.evaluateJavaScript('alert("tilesloaded")')

        # msgBox = QMessageBox()
        # msgBox.setText("Welcome to pyFlightRadar")
        # msgBox.setModal(True)
        # msgBox.setInformativeText("Version 0.1")
        # msgBox.setStandardButtons(QMessageBox.Ok)
        # ret = msgBox.exec_()

        # Start updating
        self.start_timer()
        print("Tiles loaded")

    @pyqtSlot()
    def load_all_planes(self):
        """
        Load all aircrafts all around the world
        (Very slow)
        """
        frame = self.web.page().mainFrame()
        for flight_id in self.all_planes:
            try:
                flight_number = self.flapi.get_aircraft_info(flight_id)["flight"]
            except KeyError:
                flight_number = ""
            try:
                # print(flight_id)
                frame.evaluateJavaScript('addMarker({}, {}, "{}", "{}")'.format(self.all_planes[flight_id][1],
                                                                                self.all_planes[flight_id][2],
                                                                                flight_number,
                                                                                str(flight_id)))
            except:
                print("{} - {}".format(flight_id, self.all_planes[flight_id]))
                print("This is not valid flight_id")
        frame.evaluateJavaScript('alert(count)')

    @pyqtSlot()
    def get_me_to_ekb(self):
        frame = self.web.page().mainFrame()
        frame.evaluateJavaScript('var pos = new google.maps.LatLng(56.7974, 60.556641); map.setCenter(pos);')
        frame.evaluateJavaScript('repaint_by_hand()')

    def start_timer(self):
        """
        Event for map refreshing
        """
        self.main_timer = QTimer(self)
        self.main_timer.timeout.connect(self.refresh)
        self.main_timer.start(3000)


# Browser()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Browser()
    window.setWindowTitle("pyFlightRadar")
    window.show()
    sys.exit(app.exec_())
