import aiohttp_cors

from aiohttp import web

from cache.routes import routes
from cache.middleware import (create_error_middleware,
                              middleware_cache,
                              middleware_postgres,
                              )
from settings import settings

import raven

middlewares = [middleware_cache, middleware_postgres]

sentry_client = raven.Client(settings['sentry']['dsn']) \
    if settings.get('sentry', {}).get('enabled') else None

if sentry_client:
    middlewares.insert(0, create_error_middleware)

app = web.Application(middlewares=middlewares)
app.auth = {}
app.sentry_client = sentry_client
app.settings = settings

for route in routes:
    app.router.add_route(*route)


# Configure default CORS settings.
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

# Configure CORS on all routes.
for route in list(app.router.routes()):
    cors.add(route)

if __name__ == '__main__':
    import logging

    access_log = logging.getLogger('aiohttp.access')
    access_log.setLevel(logging.INFO)
    stdout_handler = logging.StreamHandler()
    access_log.addHandler(stdout_handler)

    web.run_app(app)
