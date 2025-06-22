import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import interp1d

# Class function of the respiratory rate 
class RespPM :
    def __init__(self) :
        self.bcg_signal = []
        self.smoothed_envelope =[]

    # Function to normalize a signal
    def normalize_signal(self, signal):
        normalized_signal = (signal - np.mean(signal))# / (np.std(signal))
        # normalized_signal = detrend(normalize_signal, type='constant')
        # return signal
        return normalized_signal

    # Function to apply a low-pass filter using the butter library
    def butter_lowpass_filter(self, data, cutoff, fs, order=6):
        nyquist = 0.5 * fs
        normal_cutoff = cutoff / nyquist
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        filtered_data = filtfilt(b, a, data)
        return filtered_data
    
    def butter_bandpass_filter(self, data, lowcut, highcut, fs, order=4):
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        y = filtfilt(b, a, data)
        return y
    
    def process_rpm(self, signal, fs):
    # Load and process BCG signals (normalize and then take the upper envelop of the signal to compute the rpm)
        cutoff_freq = 0.5  # Cutoff frequency for respiratory rate
       
        self.bcg_signal = self.normalize_signal(signal)
        hi = np.mean(self.bcg_signal)+8.5
        invertbcg = -self.bcg_signal
        invertbcg = self.butter_lowpass_filter (invertbcg, cutoff=cutoff_freq, fs=fs)
        minpeaks, _ = find_peaks(invertbcg, height=hi)
        minval= self.bcg_signal[minpeaks]
        if len(minpeaks) >1 :
            interp_func = interp1d(minpeaks, minval, kind='linear', fill_value="extrapolate")
            lower_envelope = interp_func(np.arange(len(self.bcg_signal)))
            self.smoothed_envelope = gaussian_filter1d(lower_envelope, sigma=30)
            peak_env, _ = find_peaks(-self.smoothed_envelope,height=hi, distance = 2000)

       
            peak_intervals = np.diff(peak_env) / float(fs)
            if len(peak_intervals) == 0:
                return 0  # In case no peaks are found
            # else :
            #     return 0
            respiratory_rate =60.0 / np.mean(peak_intervals)
        else :
            return 0
    
        return round (respiratory_rate, 2)

  