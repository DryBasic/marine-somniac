from .EXGChannel import EXGChannel
from typing import Self
import numpy as np
import wfdb.processing
from sleepecg import detect_heartbeats


class ECGChannel(EXGChannel):
    def get_heart_rate(self, search_radius=200) -> Self:
        """
        Gets heart rate at 1 Hz and extrapolates it to the same frequency as input data
        search_radius: search radius to look for peaks (200 ~= 150 bpm upper bound)
        """
        rpeaks = detect_heartbeats(self.signal, self.freq)  # using sleepecg
        rpeaks_corrected = wfdb.processing.correct_peaks(
            self.signal, rpeaks, search_radius=search_radius, smooth_window_size=50, peak_dir="up"
        )
        # MIGHT HAVE TO UPDATE search_radius
        heart_rates = [60 / ((rpeaks_corrected[i+1] - rpeaks_corrected[i]) / self.freq) for i in range(len(rpeaks_corrected) - 1)]
        # Create a heart rate array matching the frequency of the ECG trace
        hr_data = np.zeros_like(self.signal)
        # Assign heart rate values to the intervals between R-peaks
        for i in range(len(rpeaks_corrected) - 1):
            start_idx = rpeaks_corrected[i]
            end_idx = rpeaks_corrected[i+1]
            hr_data[start_idx:end_idx] = heart_rates[i]

        return self._return(hr_data, step_size=1)