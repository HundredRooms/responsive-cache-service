import multiprocessing
import tensorflow as tf


def file_reader(filenames, num_epochs, shuffle=False, skip_header_lines=1):
    """
        Get input producers for file input pipeline

        :param filenames: [str]. Names of file(s) to read from
        :param num_epochs: int. Number of epochs to generate file queue
        :param shuffle: Wehter or not to shuffle records
        :param skip_header_lines: Number of header lines to skip

        :return: (tf.TextLineReader, QueueRunner)
    """

    files = tf.concat([
      tf.train.match_filenames_once(filename)
      for filename in filenames
    ], axis=0)

    filename_queue = tf.train.string_input_producer(
        files, num_epochs=num_epochs, shuffle=shuffle)
    reader = tf.TextLineReader(skip_header_lines=skip_header_lines)
    return reader, filename_queue


def read_csv_rows(rows, column_names, defaults, target_cols, output_shape=None,
                  batch_size=1, skip_columns=None, shuffle=False,
                  **shuffle_args):
    """
        Gets targets and tensors from CSV file records

        :param rows: String tensor. Each string correspons to a CSV row
        :param column_names: [str]. List of CSV column names
        :param defaults: [Tensor]. Specifies column defaults.
                         One tensor per column
        :param target_cols: [str]. List of target CSV columns. Remaining
                            `column_names` are considered as inputs
        :param output_shape: If set, target output shape for label tensor
        :param batch_size: Size of batches to read
        :param shuffle: Wehter or not to shuffle records
        :param shuffle_args: arguments to tf.train.shuffle_batch

        :return: (dict(str, Tensor), [Tensor]) as expected from a
                 tf.learn.Experiment input_fn
    """
    columns = tf.decode_csv(rows, record_defaults=defaults)
    inputs = dict(zip(column_names, columns))
    if skip_columns:
        for colname in skip_columns:
            inputs.pop(colname)
    if shuffle:
        capacity = shuffle_args.pop('capacity', batch_size * 10)
        min_after_dequeue = shuffle_args.pop('min_after_dequeue',
                                             batch_size * 2 + 1)
        allow_smaller_final_batch = shuffle_args.pop(
                'allow_smaller_final_batch',
                True)
        num_threads = shuffle_args.pop(
                'num_threads',
                multiprocessing.cpu_count())
        inputs = tf.train.shuffle_batch(
                inputs,
                batch_size,
                capacity=capacity,
                min_after_dequeue=min_after_dequeue,
                num_threads=num_threads,
                enqueue_many=shuffle_args.pop('enqueue_many', True),
                allow_smaller_final_batch=allow_smaller_final_batch
        )

    label_cols = [inputs.pop(target_name) for target_name in target_cols]
    label_tensor = tf.stack(label_cols, axis=1)

    if output_shape:
        label_tensor = tf.reshape(label_tensor, output_shape)

    return inputs, label_tensor


def input_fn_csv(filenames, column_names, defaults, target_cols,
                 batch_size, num_epochs=None, skip_header_lines=1,
                 output_shape=None, skip_columns=None, shuffle=False,
                 **shuffle_args):
    """
        Return an input_fn from a CSV file reading pipeline ready to use as
        a tf.learn.Experiment input_fn
    """

    def _input_fn():
        reader, filename_queue = file_reader(
                filenames,
                num_epochs,
                shuffle=shuffle,
                skip_header_lines=skip_header_lines
        )

        _, rows = reader.read_up_to(filename_queue, num_records=batch_size)
        return read_csv_rows(rows, column_names, defaults, target_cols,
                             batch_size=batch_size, output_shape=output_shape,
                             shuffle=shuffle, skip_columns=skip_columns,
                             **shuffle_args)

    return _input_fn
