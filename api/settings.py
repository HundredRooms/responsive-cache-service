from datetime import timedelta
from json import load as json_load
from os import environ as os_environ


def build_url(current_settings, model_type):
    msettings = current_settings[model_type]
    url = current_settings['mlengine_url'].format(
        project=current_settings['project_name'],
        model=msettings['model'],
        version=msettings['version'])
    current_settings[model_type]['url'] = url


def credentials(filename):
    with open(filename, 'r') as fin:
        content = json_load(fin)
    return content


eget = os_environ.get


settings = {
    'auth_file': '/credentials/auth.json',
    'scopes': 'https://www.googleapis.com/auth/cloud-platform',
    'headers': {
        'host': "ml.googleapis.com",
        'content-type': "application/json",
    },
    'format_dates': '%d/%m/%Y',
    'sentry': {
        'enabled': False,
        'dsn': eget('SENTRY_DSN'),
    },
    'responsive': {
        'model': 'responsive',
        'version': 'v0',
        'min_value': 0.5
    },
    'precache': {
        'max_results': 200,
        'model': {
            'min_days_until_today': 1,
            'offset_days': 1,
            'max_repeat_searches': 6,
            'min_repeat_searches': 3,
        },
    },
    'mlengine_url': 'https://ml.googleapis.com/v1/projects/{project}/models/{model}/versions/{version}:predict?alt=json',
    'databases': {
        'redis': eget('REDIS_DSN', 'redis 6379 5'),
        'postgres': {
            'db': eget('POSTGRES_NAME', 'datarooms'),
            'user': eget('POSTGRES_USER', 'hundredrooms'),
            'pwd': eget('POSTGRES_PASS', 'hundredrooms'),
            'host': eget('POSTGRES_HOST', 'postgres'),
            'port': eget('POSTGRES_PORT', 5432),
        }
    },
    'token_margin': timedelta(seconds=300),
}

settings['project_name'] = credentials(settings['auth_file'])['project_id']
postgres_conf = settings['databases']['postgres']
settings['databases']['postgres_dsn'] = f"dbname={postgres_conf['db']} user={postgres_conf['user']} password={postgres_conf['pwd']} host={postgres_conf['host']}"
build_url(settings, 'responsive')
redis_conf = dict(zip(('host', 'port', 'db'), settings['databases']["redis"].split()))
RESPONSIVE = 'responsive'
