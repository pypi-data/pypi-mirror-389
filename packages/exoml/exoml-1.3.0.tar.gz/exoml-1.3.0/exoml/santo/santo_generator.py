import logging
import threading

import numpy as np
import pandas as pd
from sklearn.utils import shuffle
from tensorflow.keras.utils import Sequence
from matplotlib import pyplot as plt
from functools import lru_cache


@lru_cache(maxsize=5)  # keep up to 5 files cached
def load_flux(path, delimiter=','):
    return np.loadtxt(path, delimiter=delimiter)


class SantoGenerator(Sequence):
    def __init__(
            self,
            lcs_dir,
            target_files,
            input_size=500,
            step_size=1,
            batch_size=500,
            shuffle=True,
            zero_epsilon=1e-7,
            indexes_steps=1,
            plot=False,
            from_arrays=False,
            store_arrays=False
    ):
        self.lcs_dir = lcs_dir
        self.target_files = target_files
        self.input_size = input_size
        self.step_size = step_size
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.zero_epsilon = zero_epsilon
        self.plot = plot
        self.indexes_steps = indexes_steps
        self.from_arrays = from_arrays
        self.store_arrays = store_arrays
        self.steps_count, self.generator_info_df = self._count_inputs()

    def _count_inputs(self):
        return self.__len__(), len(self.target_files)

    def __len__(self):
        return len(self.target_files) // self.batch_size

    def __getitem__(self, index):
        train_fluxes = np.full((self.batch_size, self.input_size), 0.0)
        train_tags = np.full((self.batch_size, self.input_size), float(0))
        cadences = np.full((self.batch_size), 0.0)
        initial_index = index * self.batch_size
        for iteration_index in np.arange(initial_index, initial_index + self.batch_size):
            item_index = iteration_index - initial_index
            filename = self.target_files[iteration_index]
            try:
                flux = load_flux(f"{filename}", delimiter=",")
                flux_data = flux[np.r_[1, 0]]
                tags_data = flux[3]
                flux_data[0] = flux_data[0] / 2
                train_fluxes[item_index] = flux_data[0]
                train_tags[item_index] = tags_data
                cadences[item_index] = np.median(flux_data[1][np.argwhere(flux_data[1] > 0).flatten()]) * 24
                cadences[item_index] = np.where(cadences[item_index] >= 1, 1 - self.zero_epsilon, cadences[item_index])
                self.assert_in_range("", flux_data[0])
            except Exception as e:
                logging.exception(
                    f"Error with file {filename}. file_index {item_index}, "
                    f"iteration_index {iteration_index}, batch_size {self.batch_size}, "
                    f"input_size {self.input_size}"
                )
                raise e
            # if self.plot:
            #     fig, ax = plt.subplots(2, 1, figsize=(16, 8), constrained_layout=True)
            #     ax[0].scatter(np.arange(0, len(train_fluxes[item_index])), train_fluxes[item_index])
            #     ax[1].plot(np.arange(0, train_tags[item_index]), train_tags[item_index])
            #     plt.show()
        np.all(
            train_tags != train_tags.astype(int)
        ), "train_tags contains integer values!"
        return [train_fluxes, cadences], train_tags

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
        if self.shuffle:
            self.target_files = shuffle(self.target_files)

    def class_weights(self):
        return {0: 1, 1: 1}

    def steps_per_epoch(self):
        return self.steps_count
