from .Channel import Channel
import numpy as np
from typing import Self
import mne
from scipy.integrate import simpson
from scipy.signal import welch
from scipy.signal.windows import hann

class EXGChannel(Channel):
    def get_rolling_band_power_multitaper(self, freq_range:tuple[float, float]=(0.5, 4), ref_power:float=1e-13,
                                          window_sec:int=2, step_size:int=1, in_dB:bool=True) -> Self:
        """
        Gets rolling band power for specified frequency range, data frequency and window size
        freq_range: range of frequencies in form of (lower, upper) to calculate power of
        ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
        window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
        step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
        in_dB: boolean for whether to convert the output into decibals
        """
        def get_band_power_multitaper(a, start, end) -> np.array:
            a = a[start:end]
            # TODO: maybe edit this later so there is a buffer before and after?
            psd, freqs = mne.time_frequency.psd_array_multitaper(a, sfreq=self.freq,
                                                                 fmin=freq_range[0], fmax=freq_range[1], adaptive=True, 
                                                                 normalization='full', verbose=False)
            freq_res = freqs[1] - freqs[0]
            # Find the index corresponding to the delta frequency range
            delta_idx = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
            # Integral approximation of the spectrum using parabola (Simpson's rule)
            delta_power = psd[delta_idx] / ref_power
            if in_dB:
                delta_power = simpson(10 * np.log10(delta_power), dx=freq_res)
            else:
                delta_power = np.mean(delta_power)
            # Sum the power within the delta frequency range
            return delta_power

        rolling_band_power = self._apply_rolling(
            window_sec=window_sec,
            step_size=step_size,
            process=get_band_power_multitaper
        )
        return self._return(rolling_band_power, step_size=step_size)

    def get_rolling_zero_crossings(self, window_sec:int=1, step_size:int=1) -> Self:
        """
        Get the zero-crossings of an array with a rolling window
        window_sec: window in seconds
        step_size: step size in seconds (step_size of 1 would mean returend data will be 1 Hz)
        """

        def get_crossing(a, start, end):
            return ((a[start:end-1] * a[start+1:end]) < 0).sum()
        
        rolling_zero_crossings = self._apply_rolling(
            window_sec=window_sec,
            step_size=step_size,
            process=get_crossing
        )
        return self._return(rolling_zero_crossings, step_size=step_size)
  
    def get_rolling_band_power_fourier_sum(self, freq_range:tuple[float,float]=(0.5, 4), ref_power:float=0.001, window_sec:int=2, step_size:int=1) -> Self:
        """
        Gets rolling band power for specified frequency range, data frequency and window size
        freq_range: range of frequencies in form of (lower, upper) to calculate power of
        ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
        window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
        step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
        """
        def get_band_power_fourier_sum(a, start, end) -> np.array:
            a = a[start:end]
            """
            Helper function to get delta spectral power for one array
            """
            # Perform Fourier transform
            fft_data = np.fft.fft(a)
            # Compute the power spectrum
            power_spectrum = np.abs(fft_data)**2
            # Frequency resolution
            freq_resolution = self.freq / len(a)
            # Find the indices corresponding to the delta frequency range
            delta_freq_indices = np.where((np.fft.fftfreq(len(a), 1/self.freq) >= freq_range[0]) &
                                          (np.fft.fftfreq(len(a), 1/self.freq) <= freq_range[1]))[0]
            # Compute the delta spectral power
            delta_power = np.sum(power_spectrum[delta_freq_indices] / ref_power) * freq_resolution

            return delta_power

        rolling_band_power = self._apply_rolling(
            window_sec=window_sec,
            step_size=step_size,
            process=get_band_power_fourier_sum
        )
        return self._return(rolling_band_power, step_size=step_size)
    
    def get_rolling_band_power_welch(self, freq_range:tuple[float, float]=(0.5, 4), ref_power:float=0.001, window_sec:int=2, step_size:int=1) -> Self:
        """
        Gets rolling band power for specified frequency range, data frequency and window size
        freq_range: range of frequencies in form of (lower, upper) to calculate power of
        ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
        window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
        step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
        """
        def get_band_power_welch(a, start, end):
            lower_freq = freq_range[0]
            upper_freq = freq_range[1]
            window_length = int(window_sec * self.freq)
            # TODO: maybe edit this later so there is a buffer before and after?
            windowed_data = a[start:end] * hann(window_length)
            freqs, psd = welch(windowed_data, window='hann', fs=self.freq,
                               nperseg=window_length, noverlap=window_length//2)
            freq_res = freqs[1] - freqs[0]
            # Find the index corresponding to the delta frequency range
            delta_idx = (freqs >= lower_freq) & (freqs <= upper_freq)
            # Integral approximation of the spectrum using parabola (Simpson's rule)
            delta_power = simpson(
                10 * np.log10(psd[delta_idx] / ref_power), dx=freq_res)
            # Sum the power within the delta frequency range
            return delta_power

        rolling_band_power = self._apply_rolling(
            window_sec=window_sec,
            step_size=step_size,
            process=get_band_power_welch
        )
        return self._return(rolling_band_power, step_size=step_size)
    