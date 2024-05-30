import numpy as np
import antropy
import yasa
from scipy.stats import iqr, skew, kurtosis
from scipy.integrate import simpson
from scipy.signal import welch
from .constants import EEG_BANDS


class Epoch:
    @staticmethod
    def get_hjorth_params(epochs: np.array) -> dict:
        mobility, complexity = antropy.hjorth_params(epochs, axis=1)
        return {
            'hjorth_mobility': mobility,
            'hjorth_complexity': complexity
        }
    
    @staticmethod
    def get_permutation_entropy(epochs: np.array) -> np.array:
        return np.apply_along_axis(antropy.perm_entropy, axis=1, arr=epochs, normalize=True)
    
    @staticmethod
    def get_higuchi(epochs: np.array) -> np.array:
        return np.apply_along_axis(antropy.higuchi_fd, axis=1, arr=epochs),

    @staticmethod
    def get_petrosian(epochs: np.array) -> np.array:
        return antropy.petrosian_fd(epochs, axis=1)

    @staticmethod
    def get_std(epochs: np.array) -> np.array: 
        return np.std(epochs, ddof=1, axis=1)
    
    @staticmethod
    def get_interquartile_range(epochs: np.array) -> np.array: 
        return iqr(epochs, rng=(25, 75), axis=1)
    
    @staticmethod
    def get_skew(epochs: np.array) -> np.array: 
        return skew(epochs, axis=1)
    
    @staticmethod
    def get_kurtosis(epochs: np.array) -> np.array: 
        return kurtosis(epochs, axis=1)
    
    @staticmethod
    def get_zero_crossings(epochs: np.array) -> np.array: 
        return antropy.num_zerocross(epochs, axis=1)
    
    @staticmethod
    def get_total_power(powers):
        total = np.zeros(len(powers[0]))
        for power in powers:
            total += power
        return total

    @staticmethod
    def get_power_ratios(welches: dict) -> dict:
        power_ratios = {}
        if 'sdelta' in welches and 'fdelta' in welches:
            delta = welches["sdelta"] + welches["fdelta"]
            for wave in [w for w in welches.keys() if w not in ('sdelta', 'fdelta')]:
                power_ratios[f"delta/{wave}"] = delta / welches[wave]
        if 'alpha' in welches and 'theta' in welches:
            power_ratios["alpha/theta"] = welches["alpha"] / welches["theta"]
        return power_ratios

    @staticmethod
    def get_absolute_power(freqs: np.array, freq_broad: tuple[float, float], power_spectral_density: np.array) -> dict:
        idx_broad = np.logical_and(freqs >= freq_broad[0], freqs <= freq_broad[1])
        dx = freqs[1] - freqs[0]
        return {"absolute_power": simpson(power_spectral_density[:, idx_broad], dx=dx)}
    
    def get_welch(self, epochs, window_sec:int=4, bands:list[tuple[float, float, str]]=EEG_BANDS) -> tuple[dict, np.array, np.array]:
        window_length = self.freq*window_sec
        kwargs_welch = dict(
            window ='hann',
            scaling='density',
            average='median',
            nperseg=window_length,
            noverlap=window_length//2
        )
        freqs, power_spectral_density = welch(epochs, self.freq, **kwargs_welch)
        bandpower = yasa.bandpower_from_psd_ndarray(power_spectral_density, freqs, bands=bands)

        welches = {}
        for i, (_, _, band_name) in enumerate(bands):
            welches[band_name] = bandpower[i]
        return (welches, freqs, power_spectral_density)