import tensorflow as tf
from tensorflow.contrib.learn import utils as learn_utils

from cache.models.responsive_dnn import dnn_responsive_estimator
from cache.input_tools import input_fn_csv

from cache.settings import settings
isettings = settings['input']['responsive']
rsettings = settings['responsive']

DEFAULT_ESTIMATOR = dnn_responsive_estimator

# Rearange settings for compliance with input_fn_csv interface
BASE_PARAMS = {
        'target_cols': rsettings['labels'],
        'batch_size': rsettings['batch_size'],
        'column_names': isettings['csv_columns'],
        'skip_columns': isettings['unused_columns'],
        'defaults': isettings['column_defaults'],
}


def train_input(train_file):
    """
        Returns a training input_fn for a tf.learn.Experiment
    """

    input_fn = input_fn_csv([train_file], shuffle=True,
                            **BASE_PARAMS)
    return input_fn


def eval_input(test_file):
    """
        Returns an eval input_fn for a tf.learn.Experiment
    """

    input_fn = input_fn_csv([test_file], **BASE_PARAMS)
    return input_fn


def serving_input():
    """
        Returns a serving_fn for a tf.learn.Experiment
    """

    def _serving_fn():
        feature_placeholders = {
                name: tf.placeholder(isettings['target_types'], [None])
                for name in rsettings['inputs']
        }
        features = dict(feature_placeholders)
        return learn_utils.input_fn_utils.InputFnOps(features,
                                                     None,
                                                     feature_placeholders)

    return _serving_fn
