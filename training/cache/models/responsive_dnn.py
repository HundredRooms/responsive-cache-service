import tensorflow as tf
import tensorflow.contrib.layers as layers
from tensorflow.python.ops import variable_scope

from cache.utils import full_path, unpickle
from cache.settings import settings

rsettings = settings['responsive']
isettings = settings['input']


class InvalidLabels(ValueError):
    pass


def get_output_labels(output_labels):
    def _parse_output(str_ouput):
        try:
            booking_window, nights = map(int, str_ouput.split('-'))
        except ValueError:
            raise InvalidLabels('Label {} is not valid'.format(str_ouput))

        return {'booking_window': booking_window, 'nights': nights}

    return [_parse_output(str_out) for str_out in output_labels]


def dnn_responsive_modfn(features_dict, labels, mode, params):
    """
        DNN with three hidden layers. tf.contrib.learn.Estimator model_fn.

        This function contract can be checked in:
        https://www.tensorflow.org/extend/estimators
    """

    # Get hyperparameters
    hidden1 = params['hidden1']
    hidden2 = params['hidden2']
    ones_bias = params['ones_bias']
    bool_th = params['bool_th']

    # Processed Deep data
    def minmax_normalize(tensor, name):
        arange = tf.constant(float(params[name]['max'] - params[name]['min']))
        subtract = tf.subtract(tensor, tf.constant(float(params[name]['min'])))
        return tf.truediv(subtract, arange)

    output_labels = get_output_labels(rsettings['labels'])

    input_list_deep = [minmax_normalize(tensor_in, name=name)
                       for name, tensor_in in features_dict.items()
                       if name in rsettings['continuous_inputs']]

    features_dnn = tf.stack(input_list_deep, -1)

    n_deep_inputs = len(rsettings['continuous_inputs'])
    n_labels = rsettings['n_labels']

    # Processed Wide data.
    # Read discrete inputs as continuous inputs and then convert to discrete.
    date_arrival_dow = tf.contrib.layers.real_valued_column("date_arrival_dow")
    date_leaving_dow = tf.contrib.layers.real_valued_column("date_leaving_dow")
    created_at_dow = tf.contrib.layers.real_valued_column("created_at_dow")
    volume = tf.contrib.layers.real_valued_column("volume", )

    bucket_volume = tf.contrib.layers.bucketized_column(
        volume,
        boundaries=[1000, 2000, 3000, 5000, 8000, 13000, 21000])
    bucket_arrival = tf.contrib.layers.bucketized_column(
        date_arrival_dow, boundaries=list(range(8)))

    bucket_leaving = tf.contrib.layers.bucketized_column(
        date_leaving_dow, boundaries=list(range(8)))

    bucket_created = tf.contrib.layers.bucketized_column(
        created_at_dow, boundaries=list(range(8)))

    # Model structure

    # Deep Model Part
    layers_size = [n_deep_inputs, hidden1, hidden2, 1000, n_labels]
    net = layers.stack(features_dnn, layers.fully_connected, layers_size[:-1])
    deep_logits = layers.stack(net, layers.fully_connected, layers_size[-1:],
                               activation_fn=None)
    # Wide Model Part

    wide_cols = [bucket_volume, bucket_created, bucket_leaving,
                 bucket_arrival,
                 tf.contrib.layers.crossed_column([bucket_leaving,
                                                   bucket_volume],
                                                  hash_bucket_size=int(1e4)),
                 tf.contrib.layers.crossed_column([bucket_leaving,
                                                   bucket_arrival],
                                                  hash_bucket_size=int(1e4)),
                 tf.contrib.layers.crossed_column([bucket_leaving,
                                                   bucket_created],
                                                  hash_bucket_size=int(1e4)),
                 tf.contrib.layers.crossed_column([bucket_volume,
                                                   bucket_created],
                                                  hash_bucket_size=int(1e4)),
                 tf.contrib.layers.crossed_column([bucket_volume,
                                                   bucket_arrival],
                                                  hash_bucket_size=int(1e4)),
                 tf.contrib.layers.crossed_column([bucket_created,
                                                   bucket_arrival],
                                                  hash_bucket_size=int(1e4)),
                 tf.contrib.layers.crossed_column([bucket_created,
                                                   bucket_arrival,
                                                   bucket_leaving],
                                                  hash_bucket_size=int(1e4)),
                 ]

    with variable_scope.variable_op_scope(
            features_dict.values(), "linear") as scope:
        wide_logits, _, _ = (
            layers.weighted_sum_from_feature_columns(
                columns_to_tensors=features_dict,
                feature_columns=wide_cols,
                num_outputs=n_labels,
                weight_collections=['linear'],
                scope=scope))

    # Combined two parts
    logits = wide_logits + deep_logits

    # Model output and loss
    prediction = tf.nn.sigmoid(logits)

    predictions = {str(search): prediction[0][idx]
                   for idx, search in enumerate(output_labels)}

    if mode == tf.contrib.learn.ModeKeys.INFER:
        return tf.contrib.learn.ModelFnOps(mode, predictions)

    loss_outputs = tf.nn.sigmoid_cross_entropy_with_logits(logits=logits,
                                                           labels=labels)
    loss_outputs = loss_outputs * (ones_bias * labels + 1)
    loss = tf.reduce_mean(loss_outputs)

    labels_b, prediction_b = map(lambda x: x > bool_th, [labels, prediction])
    precision = tf.metrics.precision(labels_b, prediction_b)
    accuracy = tf.metrics.accuracy(labels_b, prediction_b)
    recall = tf.metrics.recall(labels_b, prediction_b)
    auc = tf.metrics.auc(labels_b, prediction_b, curve='PR')
    eval_metrics = {
            'recall': recall,
            'precision': precision,
            'accuracy': accuracy,
            'auc': auc,
    }

    # Model training
    train_op = tf.contrib.layers.optimize_loss(
        loss, tf.contrib.framework.get_global_step(), optimizer='Adagrad',
        learning_rate=0.12
    )

    if mode == tf.contrib.learn.ModeKeys.EVAL:
        return tf.contrib.learn.ModelFnOps(mode, prediction, loss, train_op,
                                           eval_metrics)

    return tf.contrib.learn.ModelFnOps(mode, prediction, loss, train_op)


def dnn_responsive_estimator(model_dir, **hyperparameters):
    """
        Builds a DNN linear combined multilabel classifier estimator

        Current accepted arguments are:

        :model_dir: estimator model function
        :hyperparameters: model hyperparameters
    """

    params = hyperparameters.copy()

    params_file = isettings['params_file']
    read_path = full_path(params_file)
    params.update(unpickle(read_path))

    return tf.contrib.learn.Estimator(model_fn=dnn_responsive_modfn,
                                      model_dir=model_dir,
                                      params=params)
