import sys
import matplotlib
matplotlib.use("Qt5Agg")
import time
import threading
from PyQt5.QtWidgets import QApplication
import numpy as np

import signal
import datetime

from MainWindow import *
from SensorDataCollector import SensorDataCollector

# Lock for thread-safe data handling
data_lock = threading.Lock()
time_start = time.time_ns()
print(f"ts={time_start}")

# Flag to signal threads to stop
stop_threads = threading.Event()


def main_plot(sensor_ips, sensor_name):
    sampling_rate = 1000
    
    collectors = []
    # Creating a sensorDataCollector for each sensor
    for index, ip in enumerate (sensor_ips):
        collector = SensorDataCollector(ip, 8080,sensor_name[index],stop_threads, data_lock, float(sampling_rate))
        collector.start()
        collectors.append(collector)
    # Creating the window for plotting
    app = QApplication(sys.argv)
    main_window = MainWindow(collectors, stop_threads, data_lock)
    main_window.show()

    def handle_interrupt():
        # For handle the interupt
        print("Interrupted by user, exiting...")
        stop_threads.set()
        app.quit()
    
    signal.signal(signal.SIGINT, lambda signal, frame: handle_interrupt())

    def user_input_handler():
        """ Function for write start writting a file """
        user_input = 0
        while True:
            print(f"Current state : {user_input}")
            user_input = input("Start writing data press 1, stop press 0: ")
            if user_input == '1':
                age = input("Enter age: ")
                weight = input("Enter weight: ")
                height = input("Enter height: ")
                sex = input("Enter gender: ")
                patho = input("Any pathology ?")
                time_start = time.time()
                # Start write in the file
                file_name =f"log_data_{str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))}.txt"
                file_handle = open(file_name, "w")
                file_handle.write(f"Age: {age}, Weight: {weight}, Height: {height}, Sexe: {sex}, Patho: {patho}, Time Start: {time_start}\n")
                file_handle.write(f"Sensors: {', '.join(sensor_name)}\n")
                # Start record each sensor
                for collector in collectors:
                    collector.start_writing(age, weight, time_start, file_name)
            elif user_input == '0':
                for collector in collectors:
                    # for dp in collector.data_to_write : # For write int in the file
                    #     file_handle.write(f"{dp}\t")
                    file_handle.write(f"{collector.data_to_write}")
                    file_handle.write(f".\n")
                    collector.stop_writing()
                file_handle.close()
                print("Finish Writting")
            else:
                print("Invalid input. Please enter 1 or 0.")

    input_thread = threading.Thread(target=user_input_handler, daemon=True)
    input_thread.start()

    # Interupt key board
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        handle_interrupt()
        print("Program exited")

    for collector in collectors:
        collector.join()

# Start the main function (uncomment find ip capteur if sensor or ip change)
if __name__ == '__main__':
    sensor_name = ['A1FAE7', 'ADCE05', 'A3E35A', 'AEAC7D', 'AEF6DE', 'A326FC', 'ADFB5F', '90A297'] #['AF99DD','AFFFF8']
    sensor_ips = ['192.168.1.107', '192.168.1.108', '192.168.1.102', '192.168.1.101', '192.168.1.105',
                 '192.168.1.103', '192.168.1.100', '192.168.1.104']#['192.168.240.109'] #['10.67.136.96', '10.67.145.83'] #['192.168.1.94', '192.168.1.121']
    # sensor_ips, sensor_name = find_IP_capts()
    main_plot(sensor_ips, sensor_name)


