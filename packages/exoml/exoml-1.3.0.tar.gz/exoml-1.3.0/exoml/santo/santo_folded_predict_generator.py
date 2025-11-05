import logging

import foldedleastsquares
import numpy as np
import pandas as pd
import scipy
from foldedleastsquares import DefaultTransitTemplateGenerator
from lcbuilder.helper import LcbuilderHelper
from sklearn.utils import shuffle
from tensorflow.keras.utils import Sequence
from scipy.signal import savgol_filter
from matplotlib import pyplot as plt

def clean_to_float(x):
    return float(str(x).strip("\"'"))

class SantoFoldedPredictGenerator(Sequence):
    def __init__(
            self,
            time, flux,
            input_size=500,
            step_size=1,
            batch_size=500,
            shuffle=True,
            zero_epsilon=1e-7,
            indexes_steps=1,
            plot=False,
            smooth=False,
            rstar=1.0,
            mstar=1.0,
            period_min=0.5,
            period_max=15.0,
            oversampling_factor=1,
            n_transits_min=1
    ):
        self.time = time
        self.flux = flux
        self.input_size = input_size
        self.step_size = step_size
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.zero_epsilon = zero_epsilon
        self.plot = plot
        self.periods = np.sort(DefaultTransitTemplateGenerator().period_grid(
            R_star=rstar,
            M_star=mstar,
            time_span=np.max(time) - np.min(time),
            period_min=period_min,
            period_max=period_max,
            oversampling_factor=oversampling_factor,
            n_transits_min=n_transits_min,
        ))
        self.steps_count = self._count_inputs()
        self.smooth = smooth

    def _count_inputs(self):
        return len(self.periods) - 1

    def __len__(self):
        return len(self.periods) - 1 // self.batch_size

    def __getitem__(self, index):
        max_index = (index + 1) * self.batch_size
        max_index = len(self.periods) if max_index >= len(self.periods) else max_index
        period_indexes = np.arange(index * self.batch_size, max_index, 1)
        inputs = np.full((self.batch_size, self.input_size, 1), 0.0)
        for period_index in period_indexes:
            period = self.periods[period_index]
            phases = foldedleastsquares.core.foldfast(self.time, period)
            sort_index = np.argsort(phases, kind="mergesort")  # 8% faster than Quicksort
            flux = self.flux[sort_index]
            time = self.time[sort_index]
            bin_means, bin_centers, _ = scipy.stats.binned_statistic(
                np.arange(len(flux)),  # x positions
                flux,  # values
                statistic='mean',
                bins=self.input_size
            )
            bin_means = bin_means / 2
            bin_means[np.isnan(bin_means)] = self.zero_epsilon
            self.assert_in_range('target', bin_means)
            inputs[period_index] = bin_means.reshape((self.input_size, 1))
        return inputs, None

    def assert_in_range(self, object_id, array, values_range=(0, 1)):
        if np.isnan(array).any():
            raise ValueError("Target " + str(object_id) + " contains NaN values")
        elif np.max(array) >= values_range[1]:
            raise ValueError("Target " + str(object_id) + " contains values > 1")
        elif np.min(array) < values_range[0]:
            raise ValueError("Target " + str(object_id) + " contains values < 0")
        # elif np.all(array == values_range[0]):
        #     raise ValueError("Target " + str(object_id) + " contains all values == 0")

    def on_epoch_end(self):
        pass

    def class_weights(self):
        return {0: 1, 1: 1}

    def steps_per_epoch(self):
        return self.__len__()