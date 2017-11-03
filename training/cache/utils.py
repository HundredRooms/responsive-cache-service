from os.path import join as join_path, exists as path_exists
from pickle import load as pickle_load

from cache.storage import (storage_driver, pickle_load as load_storage_pickle,
                           is_storage)
from cache.settings import settings


class FileNotFoundError(IOError):
    """
        This is jusdt a dummy error definition for Python 2.7 which
        should be removed if any migration to Python3.x is possible
        since such error is already defined there
    """


def check_storage(fnx):
    def wraper(input_file, *args, **kwargs):
        kwargs['is_storage'] = is_storage(input_file)
        return fnx(input_file, *args, **kwargs)
    return wraper


def get_output_labels(output_labels):
    def _parse_output(str_ouput):
        booking_window, nights = map(int, str_ouput.split('-'))
        return {'booking_window': booking_window, 'nights': nights}

    return [_parse_output(str_out) for str_out in output_labels]


@check_storage
def unpickle(pickle_path, is_storage):
    if is_storage:
        storage = storage_driver(settings['storage_keys_file'])
        pickle = load_storage_pickle(storage, pickle_path)
    else:
        with open(pickle_path, 'rb') as fp:
            pickle = pickle_load(fp)
    return pickle


@check_storage
def check_path(path, is_storage=False):
    if (path is None or not path_exists(path)) and not is_storage:
        msg = 'File "{}" does not exist'.format(path)
        raise FileNotFoundError(msg)

    return path


@check_storage
def full_path(file_name, is_storage=False):
    if is_storage:
        return file_name

    if file_name is None:
        raise FileNotFoundError('No file')

    files_path = settings['input']['files_path']
    full_path = join_path(files_path, file_name)

    return check_path(full_path)
