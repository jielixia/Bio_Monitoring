from scipy.signal import find_peaks
import numpy as np

class Findpeak :
    def __init__(self) :
        pass

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
        valid_peaks=[]
        distance = fs / 2 # fs set to 1000
        threshold = np.mean(bcg_signal)+8 #1e-8 when you do EMD/elliptic/DWT
        peaks, _ = find_peaks(bcg_signal, distance=distance, height=threshold)  #distance=distance,
       
        # #  Validation of the peaks
        # valid_peaks = []
        for i in range(1, len(peaks)):
            rr_interval = (peaks[i] - peaks[i - 1]) / fs
            if 0.4 < rr_interval < 1.5:
                
                valid_peaks.append(peaks[i])

        return valid_peaks
                

    def process_findPeaks (self, data_wind, data_windtime, valid_peaks, data_peak) :
        t_list = []
               
        valid_peaks = self.heart_beat_detection(data_wind) 
       
        t_list = [data_windtime[i] for i in valid_peaks]
        val_peaks = [data_wind[i] for i in valid_peaks]

        peak_intervals = np.diff(valid_peaks) / float(1000)
        if len(peak_intervals) == 0:
            heart_rate = 0  # In case no peaks are found
        else :
            heart_rate =60.0 / np.mean(peak_intervals)
      
      
        for tp, peak in zip(t_list, val_peaks): 
            data_peak.append((tp, peak))

        return data_peak, round(heart_rate, 2)
    

