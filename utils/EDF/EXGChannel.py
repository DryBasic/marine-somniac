from .Channel import Channel
import numpy as np
from typing import Self, Literal
import mne
import yasa
import antropy
from scipy.integrate import simpson
from scipy.signal import welch
from scipy.stats import iqr, skew, kurtosis
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
    
    
    def get_yasa_welch(self, freq_broad:tuple=(0.4, 30), freq_range:tuple[float, float]=(0.5, 4), ref_power:float=0.001, window_sec:int=4, epoch_window_sec:int=32, step_size:int=1,
                        preset_band_range:Literal['alpha','beta','sigma','theta','sdelta','fdelta']=None) -> Self:
        """
        freq_broad: broad range frequency; used for "absolute power" calculations, data is pre-filtered to this
        freq_range:
        window_sec: 
        epoch_window_sec: 
        ref_power:
        step_size:
        preset_band_range: overrides freq_range if specified with defaults for 'alpha'|'beta'|'sigma'|'theta'|'sdelta'|'fdelta'
        """
        if preset_band_range is not None:
            freq_range = {
                "alpha": (8, 12),
                "beta": (16, 30),
                "sigma": (12, 16),
                "theta": (4, 8),
                "sdelta": (0.4, 1),
                "fdelta": (1, 4)
            }[preset_band_range]

        dt_filt = mne.filter.filter_data(
            self.signal, self.freq, 
            l_freq=freq_broad[0], h_freq=freq_broad[1], verbose=False
        )
        times, epochs = yasa.sliding_window(dt_filt, sf=self.freq, window=epoch_window_sec, step=step_size)
        times = times + epoch_window_sec // 2 
        window_length = self.freq*window_sec
        kwargs_welch = dict(
            window='hann',
            nperseg=window_length, # a little more than  4 minutes
            noverlap=window_length//2,
            scaling='density',
            average='median'
        )
        freqs, psd = welch(epochs, self.freq, **kwargs_welch)
        bp = yasa.bandpower_from_psd_ndarray(psd, freqs, bands=bands)

    def get_hjorth_mobility(self):
        _, epochs = self._get_epochs()
        hmob, _ = antropy.hjorth_params(epochs, axis=1)
        return hmob

    def get_hjorth_complexity(self):
        _, epochs = self._get_epochs()
        _, hcomp = antropy.hjorth_params(epochs, axis=1)
        return hcomp
    

    def get_():
        feat = {
            "std": np.std(epochs, ddof=1, axis=1),
            "iqr": iqr(epochs, rng=(25, 75), axis=1),
            "skew": skew(epochs, axis=1),
            "kurt": kurtosis(epochs, axis=1),
            "nzc": antropy.num_zerocross(epochs, axis=1),
        }

    def _get_epochs(self, freq_broad, window_sec, step_size, epoch_window_sec) -> tuple:
        dt_filt = mne.filter.filter_data(
            self.signal, self.freq, 
            l_freq=freq_broad[0], h_freq=freq_broad[1], verbose=False
        )
        times, epochs = yasa.sliding_window(
            dt_filt, sf=self.freq, 
            window=window_sec, step=step_size
        )
        times = times + epoch_window_sec // 2 # add window/2 to the times to make the epochs "centered" around the times
        return (times, epochs)

    def get_features_yasa_eeg(self, freq_broad=(0.4, 30), sfreq=500, welch_window_sec=4, epoch_window_sec=32, step_size=4, bands=None):
        """
        Gets ECG features using similar code & syntax as YASA's feature generation, calculates deterministic features as well as spectral features
        freq_broad: broad range frequency of EEG (this is used for "absolute power" calculations, and as a divisor for calculating overall relative power)
        sfreq: sampling frequeuency, by default 500 Hz
        epoch_window_sec: size of the epoch rolling window to use
        welch_window_sec: size of the welch window for power spectral density calculations (this affects the low frequeuncy power and very low frequency power calculations, etc.)
        step_size: how big of a step size to use, in seconds
        bands: optional parameter to override the default bands used, for exmaple if you'd like more specific bands than just sdelta, fdelta, theta, alpha, etc
        """
        if bands is None:
            bands = [
                (0.4, 1, "sdelta"),
                (1, 4, "fdelta"),
                (4, 8, "theta"),
                (8, 12, "alpha"),
                (12, 16, "sigma"),
                (16, 30, "beta"),
            ]
        
        #  Preprocessing
        # - Filter the data
        dt_filt = mne.filter.filter_data(
            self.signal, sfreq, l_freq=freq_broad[0], h_freq=freq_broad[1], verbose=False
        )
        # - Extract epochs. Data is now of shape (n_epochs, n_samples).
        times, epochs = yasa.sliding_window(dt_filt, sf=sfreq, window=epoch_window_sec, step=step_size)
        times = times + epoch_window_sec // 2 # add window/2 to the times to make the epochs "centered" around the times

        window_length = sfreq*welch_window_sec
        kwargs_welch = dict(
            window='hann',
            nperseg=window_length, # a little more than  4 minutes
            noverlap=window_length//2,
            scaling='density',
            average='median'
        )

        # Calculate standard descriptive statistics
        hmob, hcomp = antropy.hjorth_params(epochs, axis=1)

        feat = {
            "std": np.std(epochs, ddof=1, axis=1),
            "iqr": iqr(epochs, rng=(25, 75), axis=1),
            "skew": skew(epochs, axis=1),
            "kurt": kurtosis(epochs, axis=1),
            "nzc": antropy.num_zerocross(epochs, axis=1),
            "hmob": hmob,
            "hcomp": hcomp,
        }

        # Calculate spectral power features (for EEG + EOG)
        freqs, psd = sp_sig.welch(epochs, sfreq, **kwargs_welch)
        bp = bandpower_from_psd_ndarray(psd, freqs, bands=bands)

        for j, (_, _, b) in enumerate(bands):
            feat[b] = bp[j]

        # Add power ratios for EEG
        if 'sdelta' in feat:
            delta = feat["sdelta"] + feat["fdelta"]
            feat["dt"] = delta / feat["theta"]
            feat["ds"] = delta / feat["sigma"]
            feat["db"] = delta / feat["beta"]
            feat["at"] = feat["alpha"] / feat["theta"]
        
        # Add total power
        idx_broad = np.logical_and(freqs >= freq_broad[0], freqs <= freq_broad[1])
        dx = freqs[1] - freqs[0]
        feat["abspow"] = simpson(psd[:, idx_broad], dx=dx)

        # Add relative power standard deviation
        for j, (_, _, b) in enumerate(bands):
            feat[b + '_std'] = [np.std(bp[j])] * len(bp[j])

        # Add relative power bands
        for j, (_, _, b) in enumerate(bands):
            feat[b + '_relative'] = bp[j] / feat["abspow"]

        # Calculate entropy and fractal dimension features
        feat["perm"] = np.apply_along_axis(ant.perm_entropy, axis=1, arr=epochs, normalize=True)
        feat["higuchi"] = np.apply_along_axis(ant.higuchi_fd, axis=1, arr=epochs)
        feat["petrosian"] = ant.petrosian_fd(epochs, axis=1)
        feat["epoch_index"] = times

        # Convert to dataframe
        feat = pd.DataFrame(feat)
        for col in feat.columns:
            if col != 'yasa_time':
                feat[col] = pd.to_numeric(feat[col])
        return feat
