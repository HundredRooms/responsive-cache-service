from collections import Mapping
from importlib import import_module
from os import environ, path


eget = environ.get


def update(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def merge_settings(settings):
    environ = eget('HR_ENV', 'dev').lower()
    settings_file = 'settings_{}'.format(environ)
    if path.exists(settings_file + '.py'):
        settings_override = import_module(settings_file).settings
        settings = update(settings, settings_override)
    return settings
