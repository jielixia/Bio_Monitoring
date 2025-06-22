
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget,QPushButton, QHBoxLayout

import pyqtgraph as pg
from capteur_convert_name2num import *

class MainWindow(QMainWindow):
    def __init__(self, collectors, stop_threads, data_lock):
        super().__init__()
        self.setWindowTitle("Real-time Sensor Data Plot")
        self.setGeometry(100, 100, 1400, 600 * len(collectors))

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        self.plots = {}
        self.curves = {}
        self.threads = []
        self.buttons = {}
        self.plot_visible = {}
        self.collectors = collectors
        #########
        self.peakcurves = {}
        self.peak_detection_active = False  # Flag for peak detection
        self.regions = {}  # Store regions for each plot
        self.movement_detection_active = False  # Flag for movement detection
        #########
        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)

        self.data_lock = data_lock
        self.stop_threads = stop_threads

        for collector in self.collectors:
            win = pg.GraphicsLayoutWidget(show=True)
            plot = win.addPlot()
            plot = pg.PlotWidget(title=f"Sensor {convertname2num([collector.sensor_name])[0]}")
            self.layout.addWidget(plot)
            self.plots[collector.sensor_ip] = plot
            self.curves[collector.sensor_ip] = plot.plot(pen='y')
            ########################
            self.peakcurves[collector.sensor_ip] = plot.plot(pen=None, symbol='+', symbolSize=15, symbolBrush='r')
            self.regions[collector.sensor_ip] = []  # Initialize empty list for regions
            ############################
            self.plot_visible[collector.sensor_ip] = True

            button = QPushButton(f"Toggle Sensor {convertname2num([collector.sensor_name])[0]}")
            button.clicked.connect(lambda checked, ip=collector.sensor_ip: self.toggle_plot(ip))
            button_layout.addWidget(button)
            self.buttons[collector.sensor_ip] = button

        # Button to start/stop movement detection
        self.start_stop_button = QPushButton("Start Movement Detection")
        self.start_stop_button.setStyleSheet("background-color: #E99A9F; color: black;")
        self.start_stop_button.clicked.connect(self.toggle_movement_detection)
        button_layout.addWidget(self.start_stop_button)

        # Button to start/stop peak detection
        self.start_peak_button = QPushButton("Start Peak Detection")
        self.start_peak_button.setStyleSheet("background-color: lightblue; color: black;")
        self.start_peak_button.clicked.connect(self.toggle_peak_detection)
        button_layout.addWidget(self.start_peak_button)

        # Initialize the QTimer for updating plots
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)  # Update every 100 ms

    def update_data(self):
        with self.data_lock:
            for collector in self.collectors:
                if self.plot_visible[collector.sensor_ip]:
                    if collector.data_store:
                        x_vals, y_vals = zip(*collector.data_store)
                        
                        ################# PEAK DEATECTION
                        if collector.data_peak: 
                            x_peak, peak_val = zip(*collector.data_peak) 
                        else:
                            x_peak, peak_val = [], []  # Assign empty lists or handle appropriately

                        if self.peak_detection_active:
                            self.peakcurves[collector.sensor_ip].setData(x_peak, peak_val)
                        else :
                            self.peakcurves[collector.sensor_ip].setData([],[])
                        ########################

                        ########################## MOUV DETECTION
                        # Clear previous regions
                        for region in self.regions[collector.sensor_ip]:
                            self.plots[collector.sensor_ip].removeItem(region)
                        self.regions[collector.sensor_ip] = []  # Reset the region list
    
                        if self.movement_detection_active:
                            if collector.data_mouv:
                                t_start, t_end = zip(*collector.data_mouv)
                                for ts, te in zip(t_start, t_end):
                                    lr = pg.LinearRegionItem([ts, te], brush=(200, 50, 50, 100))
                                    self.plots[collector.sensor_ip].addItem(lr)
                                    self.regions[collector.sensor_ip].append(lr)  # Track the region
                                    
                        #########################################
                        # Signal
                        self.curves[collector.sensor_ip].setData(x_vals, y_vals)
                        
            

    def toggle_movement_detection(self):
        self.movement_detection_active = not self.movement_detection_active
        if self.movement_detection_active:
            self.start_stop_button.setText("Stop Movement Detection")
        else:
            self.start_stop_button.setText("Start Movement Detection")

    def toggle_peak_detection(self):
        self.peak_detection_active = not self.peak_detection_active
        if self.peak_detection_active:
            self.start_peak_button.setText("Stop Peak Detection")
        else:
            self.start_peak_button.setText("Start Peak Detection")

    def toggle_plot(self, sensor_ip):
      
        plot = self.plots[sensor_ip]
        self.plot_visible[sensor_ip] = not self.plot_visible[sensor_ip]
        if self.plot_visible[sensor_ip]:
            self.curves[sensor_ip].setPen(pg.mkPen('y'))
            plot.show()
        else:
            self.curves[sensor_ip].setPen(pg.mkPen(None))
            plot.hide()

    def closeEvent(self, event):
        self.stop_threads.set()
        for thread in self.threads:
            thread.stop()
        for thread in self.threads:
            thread.join()
        event.accept()
