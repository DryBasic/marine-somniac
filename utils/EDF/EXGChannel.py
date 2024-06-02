from .Channel import Channel
from .EpochDerived import EpochDerived
import pandas as pd
import numpy as np
import mne
import yasa


class EXGChannel(Channel, EpochDerived):
    def get_epochs(self, freq_broad:tuple[float,float]=(0.4, 30), window_sec:int=32, step_size:int=4) -> tuple:
        """
        freq_broad: broad range frequency of EEG (this is used for "absolute power" calculations, and as a divisor for calculating overall relative power)
        window_sec: size of the epoch rolling window to use in seconds
        step_size: how big of a step size to use, in seconds
        """
        dt_filt = mne.filter.filter_data(
            self.signal, self.freq, 
            l_freq=freq_broad[0], h_freq=freq_broad[1], verbose=False
        )
        times, epochs = yasa.sliding_window(
            dt_filt, sf=self.freq, 
            window=window_sec, step=step_size
        )
        # add window/2 to the times to make the epochs "centered" around the times
        times = times + window_sec // 2 
        return (times, epochs)
    
    def get_antropy_features(self, epochs: np.array) -> dict:
        features = {
            'permutation_entropy': self.get_permutation_entropy(epochs),
            'higuchi_fractal_dimension': self.get_higuchi(epochs),
            'petrosian_fractal_dimension': self.get_petrosian(epochs),
            "number_zero_crossings": self.get_zero_crossings(epochs)
        }
        return features
    
    def get_epoch_stats(self, epochs: np.array) -> dict:
        stats = {
            "std": self.get_std(epochs),
            "iqr": self.get_interquartile_range(epochs),
            "skew": self.get_skew(epochs),
            "kurtosis": self.get_kurtosis(epochs)
        }
        return stats

    def get_epoch_derived_features(self, freq_broad=(0.4, 30), epoch_window_sec=32, step_size=4, welch_window_sec:int=4) -> pd.DataFrame:
        """
        Gets ECG features using similar code & syntax as YASA's feature generation, calculates deterministic features as well as spectral features
        freq_broad: broad range frequency of EEG (this is used for "absolute power" calculations, and as a divisor for calculating overall relative power)
        sfreq: sampling frequeuency, by default 500 Hz
        epoch_window_sec: size of the epoch rolling window to use
        welch_window_sec: size of the welch window for power spectral density calculations (this affects the low frequeuncy power and very low frequency power calculations, etc.)
        step_size: how big of a step size to use, in seconds
        bands: optional parameter to override the default bands used, for exmaple if you'd like more specific bands than just sdelta, fdelta, theta, alpha, etc
        """
        times, epochs = self.get_epochs(freq_broad, epoch_window_sec, step_size)

        hjorth_parameters = self.get_hjorth_params(epochs)
        antropy_features = self.get_antropy_features(epochs)
        stats = self.get_epoch_stats(epochs)
        welches, freqs, power_spectral_density = self.get_welch_of_bands(epochs, welch_window_sec)
        power_ratios = self.get_power_ratios(welches)
        absolute_power = self.get_absolute_power(freqs, freq_broad, power_spectral_density)

        welch_stds = {f"{k}_std": [np.std(array)] * len(array) for k, array in welches}
        relative_powers = {f"{k}_relative": array/absolute_power['absolute_power'] for k, array in welches}

        features = {
            'epoch': times
            **stats,
            **hjorth_parameters, 
            **antropy_features,
            **welches,
            **welch_stds,
            **relative_powers,
            **power_ratios,
            **absolute_power,
        }
        return pd.DataFrame(features)



# LEGACY
    # def get_rolling_band_power_multitaper(self, freq_range:tuple[float, float]=(0.5, 4), ref_power:float=1e-13,
    #                                       window_sec:int=2, step_size:int=1, in_dB:bool=True) -> Self:
    #     """
    #     Gets rolling band power for specified frequency range, data frequency and window size
    #     freq_range: range of frequencies in form of (lower, upper) to calculate power of
    #     ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
    #     window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
    #     step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
    #     in_dB: boolean for whether to convert the output into decibals
    #     """
    #     def get_band_power_multitaper(a, start, end) -> np.array:
    #         a = a[start:end]
    #         # TODO: maybe edit this later so there is a buffer before and after?
    #         psd, freqs = mne.time_frequency.psd_array_multitaper(a, sfreq=self.freq,
    #                                                              fmin=freq_range[0], fmax=freq_range[1], adaptive=True, 
    #                                                              normalization='full', verbose=False)
    #         freq_res = freqs[1] - freqs[0]
    #         # Find the index corresponding to the delta frequency range
    #         delta_idx = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
    #         # Integral approximation of the spectrum using parabola (Simpson's rule)
    #         delta_power = psd[delta_idx] / ref_power
    #         if in_dB:
    #             delta_power = simpson(10 * np.log10(delta_power), dx=freq_res)
    #         else:
    #             delta_power = np.mean(delta_power)
    #         # Sum the power within the delta frequency range
    #         return delta_power

    #     rolling_band_power = self._apply_rolling(
    #         window_sec=window_sec,
    #         step_size=step_size,
    #         process=get_band_power_multitaper
    #     )
    #     return self._return(rolling_band_power, step_size=step_size)

    # def get_rolling_zero_crossings(self, window_sec:int=1, step_size:int=1) -> Self:
    #     """
    #     Get the zero-crossings of an array with a rolling window
    #     window_sec: window in seconds
    #     step_size: step size in seconds (step_size of 1 would mean returend data will be 1 Hz)
    #     """

    #     def get_crossing(a, start, end):
    #         return ((a[start:end-1] * a[start+1:end]) < 0).sum()
        
    #     rolling_zero_crossings = self._apply_rolling(
    #         window_sec=window_sec,
    #         step_size=step_size,
    #         process=get_crossing
    #     )
    #     return self._return(rolling_zero_crossings, step_size=step_size)
  
    # def get_rolling_band_power_fourier_sum(self, freq_range:tuple[float,float]=(0.5, 4), ref_power:float=0.001, window_sec:int=2, step_size:int=1) -> Self:
    #     """
    #     Gets rolling band power for specified frequency range, data frequency and window size
    #     freq_range: range of frequencies in form of (lower, upper) to calculate power of
    #     ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
    #     window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
    #     step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
    #     """
    #     def get_band_power_fourier_sum(a, start, end) -> np.array:
    #         a = a[start:end]
    #         """
    #         Helper function to get delta spectral power for one array
    #         """
    #         # Perform Fourier transform
    #         fft_data = np.fft.fft(a)
    #         # Compute the power spectrum
    #         power_spectrum = np.abs(fft_data)**2
    #         # Frequency resolution
    #         freq_resolution = self.freq / len(a)
    #         # Find the indices corresponding to the delta frequency range
    #         delta_freq_indices = np.where((np.fft.fftfreq(len(a), 1/self.freq) >= freq_range[0]) &
    #                                       (np.fft.fftfreq(len(a), 1/self.freq) <= freq_range[1]))[0]
    #         # Compute the delta spectral power
    #         delta_power = np.sum(power_spectrum[delta_freq_indices] / ref_power) * freq_resolution

    #         return delta_power

    #     rolling_band_power = self._apply_rolling(
    #         window_sec=window_sec,
    #         step_size=step_size,
    #         process=get_band_power_fourier_sum
    #     )
    #     return self._return(rolling_band_power, step_size=step_size)
    
    # def get_rolling_band_power_welch(self, freq_range:tuple[float, float]=(0.5, 4), ref_power:float=0.001, window_sec:int=2, step_size:int=1) -> Self:
    #     """
    #     Gets rolling band power for specified frequency range, data frequency and window size
    #     freq_range: range of frequencies in form of (lower, upper) to calculate power of
    #     ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
    #     window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
    #     step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
    #     """
    #     def get_band_power_welch(a, start, end):
    #         lower_freq = freq_range[0]
    #         upper_freq = freq_range[1]
    #         window_length = int(window_sec * self.freq)
    #         # TODO: maybe edit this later so there is a buffer before and after?
    #         windowed_data = a[start:end] * hann(window_length)
    #         freqs, psd = welch(windowed_data, window='hann', fs=self.freq,
    #                            nperseg=window_length, noverlap=window_length//2)
    #         freq_res = freqs[1] - freqs[0]
    #         # Find the index corresponding to the delta frequency range
    #         delta_idx = (freqs >= lower_freq) & (freqs <= upper_freq)
    #         # Integral approximation of the spectrum using parabola (Simpson's rule)
    #         delta_power = simpson(
    #             10 * np.log10(psd[delta_idx] / ref_power), dx=freq_res)
    #         # Sum the power within the delta frequency range
    #         return delta_power

    #     rolling_band_power = self._apply_rolling(
    #         window_sec=window_sec,
    #         step_size=step_size,
    #         process=get_band_power_welch
    #     )
    #     return self._return(rolling_band_power, step_size=step_size)