from json import dumps as jdumps

from aiohttp import web

from cache.mlengine import (request_responsive,
                            request_two_guests,
                            )
from cache.precache import get_precache_searches
from settings import settings


def make_response(func):
    """
        Return Json web response
    """
    async def json_api_func(request):
        try:
            response = await func(request)
            if isinstance(response, web.Response):
                return response
            return web.Response(
                body=jdumps(response).encode('utf-8'),
                content_type='application/vnd.api+json')
        except Exception as e:
            response = {
                'error': None,
                'meta': None,
                'jsonapi': {"version": "1.0"},
            }
            if isinstance(e, web.HTTPException):
                status = e.status_code
                title = str(e)
                details = e.text
            else:
                raise e
                status = 500
                title = 'Internal Server Error'
                details = str(e)
            response['error'] = {
                'status': status,
                'title': title,
                'details': details
            }
            return web.Response(
                status=status,
                body=jdumps(response).encode('utf-8'),
                content_type='application/vnd.api+json')
    return json_api_func


async def get_robots(request):
    content = b"User-agent: *\r\nDisallow: / "
    return web.Response(body=content,
                        content_type="text/plain",
                        status=200)


async def predict_responsive(request):
    """
        GET method.
        Wrapper of cache.mlengine.request_responsive
    """

    required_fields = ['date_arrival', 'date_leaving', 'guests_number']
    search_in = {}
    for field in required_fields:
        search_field = request.GET.get(field)
        if not search_field:
            err_msg = 'Field {} not specified'.format(field)
            raise web.HTTPBadRequest(text=err_msg)
        search_in[field] = search_field

    search_in['volume'] = 1000

    searches = await request_responsive(**search_in, redis=request.cache)

    return searches


async def predict_two_guests(request):
    required_fields = ['date_arrival', 'date_leaving']
    search_in = {}
    for field in required_fields:
        search_field = request.GET.get(field)
        if not search_field:
            err_msg = 'Field {} not specified'.format(field)
            raise web.HTTPBadRequest(text=err_msg)
        search_in[field] = search_field

    searches = request_two_guests(**search_in)

    return [searches]


@make_response
async def predict_searches(request):
    responsive = await predict_responsive(request)
    two_guest = await predict_two_guests(request)

    predictions = dict(responsive=responsive,
                       two_guest=two_guest)

    return {'predictions': predictions}


@make_response
async def precache_searches(request):
    """
        Return most popular searches doing
    """
    max_results = settings['precache']['max_results']
    max_results = request.GET.get('max_results', max_results)
    response = await get_precache_searches(request.postgres_conn, max_results)
    return {'predictions': response}
