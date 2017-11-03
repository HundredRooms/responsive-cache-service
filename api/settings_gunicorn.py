import os

production = os.environ.get('HR_ENV') == 'prod'
accesslog = '-'
access_log_format = '%a %l %u %t "%r" %s ' \
                    '%b "%{Referrer}i" "%{User-Agent}i" %Tf'
bind = ['0.0.0.0:8080']
workers = 4 if production else 1
worker_class = 'aiohttp.worker.GunicornWebWorker'
reload = not production

del production
