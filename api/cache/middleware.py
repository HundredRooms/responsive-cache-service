import aiopg
from asyncio import get_event_loop
import redis

from settings import redis_conf, settings


REDIS_POOL_SIZE = 1000
MAX_CONNECTIONS = 10
db_pool = None
redis_conn_pool = redis.ConnectionPool(host=redis_conf['host'],
                                       port=int(redis_conf['port']),
                                       db=int(redis_conf['db']),
                                       max_connections=REDIS_POOL_SIZE)


async def create_db_pool(max_connenctions=MAX_CONNECTIONS, pool_loop=None):
    dsn = settings['databases']['postgres_dsn']
    pool_loop = pool_loop or get_event_loop()

    return await aiopg.create_pool(dsn, loop=pool_loop,
                                   minsize=1, maxsize=max_connenctions)


async def create_error_middleware(app, handler):
    async def error_handler(request):
        try:
            return await handler(request)
        except:
            data = {
                'url': request.path_qs,
                'method': request.method,
                'headers': dict(request.headers),
                'data': await request.read()
            }
            app.sentry_client.http_context(data)
            app.sentry_client.captureException()
            raise
        finally:
            app.sentry_client.context.clear()

    return error_handler


async def middleware_cache(app, handler):
    async def _inner(request):
        request.cache = redis.StrictRedis(connection_pool=redis_conn_pool)
        return await handler(request)

    return _inner


async def middleware_postgres(app, handler):
    async def _inner(request):
        global db_pool
        if db_pool is None:
            db_pool_postgress = await create_db_pool()
        async with db_pool_postgress.acquire() as conn:
            request.postgres_conn = conn
            return await handler(request)

    return _inner
