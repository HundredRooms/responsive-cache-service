from re import search as regex_search
from libcloud.storage.drivers.google_storage import GoogleStorageDriver
from pickle import loads as ploads, dumps as pdumps
from json import load as json_load


class NonValidStoragePath(ValueError):
    pass


START_TOKEN = 'gs://'


def storage_driver(keys_file):
    with open(keys_file, 'r') as fi:
        credentials = json_load(fi)

    driver = GoogleStorageDriver(key=credentials['client_email'],
                                 secret=credentials['private_key'])
    return driver


def is_storage(path):
    return path is not None and path.startswith(START_TOKEN)


def parse_path(path):
    pattern = START_TOKEN + '[^/]*'
    search_res = regex_search(pattern, path)
    if search_res is None:
        raise NonValidStoragePath

    end_pos = search_res.end()
    bucket_name = path[len(START_TOKEN):end_pos]
    storage_path = path[end_pos+1:]

    return bucket_name, storage_path


def upload_object_via_stream(
        obj, path, max_retries=2
):
    """
        Upload Object to google storage
    """

    def run_upload(bucket, storage_path, retries=1):
        """
          Sometime's google fails so we retry it two times.
        """

        if retries <= max_retries:
            try:
                object_bytes = iter_object()
                bucket.upload_object_via_stream(
                    object_bytes, object_name=storage_path
                )
                return True
            except:
                retries += 1
                return run_upload(retries)
            return False

    def iter_object(num_iters=5):
        obj_bytes = pdumps(obj)
        object_length = len(obj_bytes)
        batch_size = object_length // num_iters + 1
        for idx in range(num_iters):
            start = batch_size * idx
            end = start + batch_size
            yield obj_bytes[start:end]

    driver = storage_driver('auth.json')
    bucket_name, storage_path = parse_path(path)
    bucket = driver.get_container(container_name=bucket_name)

    return run_upload(bucket, storage_path)


def pickle_load(driver, path):
    bucket_name, storage_path = parse_path(path)
    bucket = driver.get_container(container_name=bucket_name)
    obj = bucket.get_object(object_name=storage_path)

    pickle_bytes = b''
    stream = obj.as_stream()
    for batch in stream:
        pickle_bytes += batch
    stream.close()
    return ploads(pickle_bytes)
