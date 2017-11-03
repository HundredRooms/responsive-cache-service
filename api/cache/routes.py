from cache.views import (get_robots,
                         predict_searches,
                         precache_searches,
                         )


routes = [
    ['GET', '/robots.txt', get_robots],
    ['GET', '/v1/search', predict_searches],
    ['GET', '/v1/precache', precache_searches]
]
