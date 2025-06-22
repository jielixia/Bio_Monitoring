import threading
from collections import deque
import socket
import time
import numpy as np
from scipy.signal import find_peaks
from MouvDetector import MovementDetector
# Maximum number of data points to store
MAX_DATA_POINTS = 9000

class SensorDataCollector(threading.Thread):
    def __init__(self, sensor_ip, sensor_port, sensor_name, stop_threads, data_lock, sampling_rate=1000):
        super().__init__()
        self.sensor_ip = sensor_ip
        self.sensor_port = sensor_port
        self.sampling_rate = sampling_rate
        self.data_store = deque(maxlen=MAX_DATA_POINTS)
        self.timestamp = 0 
        self.sensor_name= sensor_name
        # self.data_to_write = [] #For write int in the file
        self.data_to_write = ''

        self.write_file = False
        self.file_handle = None

        self.stop_threads = stop_threads
        self.data_lock = data_lock

        self.i=0

        ########################
        ## PEAK
        self.valid_peaks = []
        self.data_wind = []
        self.data_windtime=[]

        self.nbpt=0
        self.data_peak = deque(maxlen=100)
        ## MOUV
        self.data_wind_mouv = []
        self.data_windtime_mouv=[]
        self.nbpt_mouv=0
        self.data_mouv =deque(maxlen=100)
        self.movement_detector = MovementDetector()
        ####################################

    def run(self):
        n=0
        while not self.stop_threads.is_set():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            try:
                sock.connect((self.sensor_ip, self.sensor_port))
                while not self.stop_threads.is_set():
                    if self.i==0 :
                        print(f"{time.time_ns()} of capt {self.sensor_name}")
                        self.i=1
                    data = sock.recv(1024).decode()
                    if not data:
                        break

                    
                    self.process_data(data)
                    ##
                    if self.write_file and self.file_handle:
                        self.data_to_write+=data
                    ##

                    time.sleep(0.001)
            except Exception as e:
                if not self.stop_threads.is_set():
                    print(f"Error collecting data from {self.sensor_ip}: {e}")
            finally:
                sock.close()
            if not self.stop_threads.is_set():
                time.sleep(5)

    def process_data(self, data):
        data_points = [int(val, 16) for val in data.split(',') if len(val) > 2]
        if data_points:
            length = len(data_points)
            T_end = self.timestamp + ((length - 1) / float(self.sampling_rate))
            T = (T_end / length)
            ts = np.arange(self.timestamp, T_end, 0.001)
            self.timestamp = T_end
            with self.data_lock:
                for t, dp in zip(ts, data_points[:-2]):
                    if self.data_store and t <= self.data_store[-1][0]:
                        t = self.data_store[-1][0]
                    self.data_store.append((t, dp))

                    ########################
                    self.data_wind.append(dp)
                    self.data_windtime.append(t)
                    self.nbpt+=1

                    self.data_wind_mouv.append(dp)
                    self.data_windtime_mouv.append(t)
                    self.nbpt_mouv+=1

                first_t = self.data_store[0][0]  # Get the first t value from data_store
                # Filter data_peak to keep only those entries where tp is greater than first_t
                self.data_peak = [(tp, peak) for tp, peak in self.data_peak if tp > first_t]
                self.data_mouv = [(ts, te) for ts, te in self.data_mouv if ts > first_t]

            
                if self.nbpt>=2000: ##PEAK
                    self.process_findPeaks()
                    mouvment_start, mov_end = self.movement_detector.detect_movement(self.data_wind_mouv)
                    if mouvment_start :
                        self.data_mouv.append((self.data_windtime_mouv[mouvment_start], self.data_windtime_mouv[mov_end]))
                    
                    self.data_windtime =[]
                    self.data_wind =[]
                    self.nbpt=0

                # if self.nbpt_mouv>=2000: # Window size for MOUV => 1sec
                    
                    self.data_windtime_mouv =[]
                    self.data_wind_mouv =[]
                    self.nbpt_mouv=0
                
                    ############################

                    # if self.write_file and self.file_handle: # For writing INT data in the file
                    #     self.data_to_write.append(dp)

    def start_writing(self, age, weight, time_start, file_name):
        self.write_file = True
        #self.file_handle = open(filename, 'w')
        # file_name = f"sensor_data_{self.sensor_ip.replace('.', '_')}.txt"
        self.file_handle = open(file_name, "a")
        # self.file_handle.write(f"Age: {age}, Weight: {weight}, Time Start: {time_start}\n")
        # self.file_handle.write(f"Sensor: {sensor_name[sensor_ips.index(self.sensor_ip)]}\n")
        
        
    def stop_writing(self):
        self.write_file = False
        if self.file_handle:

            # for dp in self.data_to_write :
            #     self.file_handle.write(f"{dp}\t")
            # self.file_handle.write(f".\n")
            # self.file_handle.close()
            self.file_handle = None
            #self.data_to_write.clear()
            self.data_to_write=''

#######################################
    
    def heart_beat_detection(self, bcg_signal) :
        ''' Detect the heartbeats in the BCG signal.
        Find the peaks in the BCG signal using the find_peaks function from scipy.signal. Add a distance constraint of fs/2 to avoid detecting multiple peaks for the same heartbeat.Add a threshold of 1e-8 to detect the peaks.
        Validate the peaks by checking if the RR interval is between 0.4 and 1.5 seconds.

        Parameters
        ----------
        bcg_signal : array
            BCG signal

        Returns
        -------
        valid_peaks : array
            Array containing the indices of the valid peaks
        '''
        #  Adaptative Peak Detection
        fs = 1000
        self.valid_peaks=[]
        distance = fs / 2 # fs set to 1000
        threshold = 610 # 1e-8 when you do EMD/elliptic/DWT
        peaks, properties = find_peaks(bcg_signal, distance=distance, height=threshold)  #distance=distance,
       
        # #  Validation of the peaks
        # valid_peaks = []
        for i in range(1, len(peaks)):
            rr_interval = (peaks[i] - peaks[i - 1]) / fs
            if 0.4 < rr_interval < 1.5:
                
                self.valid_peaks.append(peaks[i])
                
        


    def process_findPeaks (self) :
        t_list = []
               
        self.heart_beat_detection(self.data_wind) 
       
        t_list = [self.data_windtime[i] for i in self.valid_peaks]
        val_peaks = [self.data_wind[i] for i in self.valid_peaks]
      
        for tp, peak in zip(t_list, val_peaks): 
            self.data_peak.append((tp, peak))


###############################################################