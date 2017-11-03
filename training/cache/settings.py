import csv

from os.path import join as join_path

import tensorflow as tf

from cache.storage import storage_driver, parse_path, is_storage


def create_output_labels(settings, model_type):
    def _read_header_storage(csv_file):
        bucket_name, storage_path = parse_path(csv_file)

        storage = storage_driver(settings['storage_keys_file'])
        bucket = storage.get_container(container_name=bucket_name)

        obj = bucket.get_object(storage_path)
        stream = obj.as_stream()
        raw_data = b''
        while b'\n' not in raw_data:
            raw_data += next(stream)

        header_str = raw_data.split(b'\n')[0].decode('utf-8')
        header = [column.replace('\r', '') for column in header_str.split(',')]
        return header

    def _read_header_local_file(csv_file):
        with open(test_file) as fcsv:
            rows = csv.reader(fcsv, delimiter=',')
            header = next(rows)
        return header

    model_input = settings['input'][model_type]
    input_labels = model_input['input_fields']
    input_path = settings['input']['files_path']

    test_file = join_path(input_path, model_input['test_file'])
    to_skip = len(input_labels)

    from_gs = is_storage(test_file)
    header_fn = _read_header_storage if from_gs else _read_header_local_file
    header = header_fn(test_file)
    output_labels = header[to_skip:]

    model_input['csv_columns'] = header
    settings[model_type]['labels'] = output_labels


def in_out_shape(model_info):
    model_info['n_inputs'] = len(model_info['inputs'])
    model_info['n_labels'] = len(model_info['labels'])


def zero_default(model_input):
    num_fields = len(model_input['csv_columns'])
    model_input['column_defaults'] = [[0.]] * num_fields


def build_responsive_model(settings):
    create_output_labels(settings, 'responsive')
    in_out_shape(settings['responsive'])
    zero_default(settings['input']['responsive'])


settings = {
    'storage_keys_file': '/credentials/auth.json',
    'responsive': {
        'batch_size': 40,
        'inputs': ['nights_in', 'guests', 'booking_window_in', 'volume',
                   'date_arrival_dow', 'created_at_dow', 'date_leaving_dow'],
        'continuous_inputs': ['nights_in', 'guests', 'booking_window_in'],
        'discrete_inputs': ['volume', 'date_arrival_dow', 'created_at_dow',
                            'date_leaving_dow'],
    },
    'input': {
        'files_path': 'gs://hr-tensorflow/cachete/input_files/',
        'params_file': 'normalize_params.pickle',
        'responsive': {
            'train_file': 'responsive_train_v1.csv',
            'test_file': 'responsive_test_v1.csv',
            'unused_columns': [],
            'input_fields': ['nights_in', 'guests', 'booking_window_in',
                             'volume', 'date_arrival_dow', 'created_at_dow',
                             'date_leaving_dow'],
            'target_types': tf.float32,
        },
    },
}


build_responsive_model(settings)
