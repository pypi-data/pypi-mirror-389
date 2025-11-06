import logging

from exoml.ml.encoding.time_position import value_encode_times
from sklearn.utils import shuffle
import tensorflow as tf
import numpy as np
import pandas as pd


class HaunterModelGenerator(tf.keras.utils.Sequence):
    """
    Sequence generator for DETREND model batches
    """
    def __init__(self, dataset, batch_size, input_size, zero_epsilon=1e-7, shuffle=True):
        self.zero_epsilon = zero_epsilon
        self.dataset = dataset
        self.batch_size = batch_size
        self.input_size = input_size
        self.shuffle = shuffle
        if self.shuffle:
            self.dataset = self.dataset.sample(frac=1).reset_index(drop=True)

    def __len__(self):
        leng = (np.ceil(len(self.dataset) / float(self.batch_size))).astype(int)
        return leng

    def __getitem__(self, idx):
        batch_rows = self.dataset[idx * self.batch_size: (idx + 1) * self.batch_size]
        batch_data_array = batch_rows.loc[:, ['mass_Mearth_input_norm', 'CMF_input_norm', 'Zenv_input_norm',
                                              'Zwater_core_input_norm', 'Tsurf_K_input_norm', 'Psurf_bar_input_norm']]
        batch_data_values = batch_rows.loc[:, ['radius_Rearth_output_norm', 'entropy_SI_output_norm',
                                               'log10_mass_integral_output_norm']]
        #assert np.all((batch_data_array > 0) & (batch_data_array < 1))
        #assert np.all((batch_data_values > 0) & (batch_data_values < 1))
        return batch_data_array.to_numpy(dtype=np.float32), batch_data_values.to_numpy(dtype=np.float32)

    def class_weights(self):
        return None

    def get_dataset(self):
        x_spec = (
            tf.TensorSpec(shape=(None, 6, 1), dtype=tf.float32)
        )

        y_spec = tf.TensorSpec(shape=(None, 3,), dtype=tf.float32)  # Adjust if label shape is different

        return tf.data.Dataset.from_generator(
            lambda: iter(self),
            output_signature=(x_spec, y_spec)
        ).take(len(self)).repeat()
