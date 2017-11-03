from __future__ import division
from collections import defaultdict

from cache.storage import upload_object_via_stream

import csv
import random
import sys

from cache.utils import full_path
from cache.settings import settings

isettings = settings['input']

VOLUME_TRAIN_DATA = 0.8
SKIPED_SEARCHES = ['4-5']
INPUT_NAMES = isettings['responsive']['input_fields']


if __name__ == "__main__":
    raw_file_name = sys.argv[1]
    train_file_name = sys.argv[2]
    test_file_name = sys.argv[3]
    try:
        NUM_LABELS = int(sys.argv[4])
    except ValueError:
        NUM_LABELS = None
    skip_searches = sys.argv[5] != 'False'

    all_rows = []
    count_labels = defaultdict(int)
    with open(raw_file_name, 'r') as fcsv:
        reader = csv.DictReader(fcsv, delimiter='|')
        idx = 0
        for row in reader:
            try:
                act_row = {name.strip(): value for name, value in row.items()}
                row_labels = {(label[2], str(label[0]) + '-' + str(label[1]))
                              for label in eval(act_row['array_agg'])}
                for label in row_labels:
                    count_labels[label[1]] += 1
                all_rows.append(act_row)
            except TypeError:
                pass

    labels = sorted(count_labels, key=count_labels.get, reverse=True)
    if skip_searches:
        for search in SKIPED_SEARCHES:
            try:
                labels.remove(search)
            except ValueError:
                pass

    NUM_LABELS = NUM_LABELS if NUM_LABELS else len(labels)
    labels = labels[:NUM_LABELS]

    def get_min_max_values(data, column):
        max_value = max(data, key=lambda x: x[column])[column]
        min_value = min(data, key=lambda x: x[column])[column]
        return dict(max=int(max_value), min=int(min_value))

    norm_params = {name: get_min_max_values(all_rows, name)
                   for name in INPUT_NAMES}

    params_file = isettings['params_file']
    write_path = full_path(params_file)
    upload_object_via_stream(norm_params, write_path)

    header_outputs = labels
    header = INPUT_NAMES + labels
    num_outputs = len(header_outputs)

    def write_header(filename):
        with open(filename, 'w') as fcsv:
            writer = csv.writer(fcsv)
            writer.writerow(header)

    write_header(train_file_name)
    write_header(test_file_name)

    with open(train_file_name, 'a') as fcsv_train, \
            open(test_file_name, 'a') as fcsv_test:
        writer_train = csv.writer(fcsv_train)
        writer_test = csv.writer(fcsv_test)

        def generate_output(act_row):
            output_labels = [0] * NUM_LABELS
            new_row = [act_row[name] for name in INPUT_NAMES]
            row_labels = eval(act_row['array_agg'])
            valid_row = False
            for label in row_labels:
                act_label = '{}-{}'.format(label[0], label[1])
                if act_label in labels:
                    pos = labels.index(act_label)
                    output_labels[pos] = 1
                    valid_row = True
            new_row += output_labels
            if valid_row:
                if random.random() <= VOLUME_TRAIN_DATA:
                    writer_train.writerow(new_row)
                else:
                    writer_test.writerow(new_row)

        map(generate_output, all_rows)
