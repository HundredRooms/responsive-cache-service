from aiohttp import ClientSession
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from json import loads as jloads, dumps as jdumps

from settings import settings, RESPONSIVE

TOKEN_MARGIN = settings.get('token_margin', 0)
OK_STATUS = 200


def get_predictions_key(search_data):
    keys = ['booking_window_in', 'nights_in', 'volume', 'guests']
    return '-'.join([str(int(search_data[k])) for k in keys])


def get_credentials():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        settings['auth_file'],
        scopes=settings['scopes']
    )
    return creds


def get_access_token(redis):
    access_token = redis.get('access_token')
    token_expire = redis.get('token_expire')
    if access_token and token_expire:
        if float(token_expire) > datetime.now().timestamp():
            return access_token.decode("utf-8")
    creds = get_credentials()
    creds.get_access_token()
    access_token = creds.access_token
    redis.set('access_token', access_token)
    token_expire = (creds.token_expiry - TOKEN_MARGIN).timestamp()
    redis.set('token_expire', token_expire)

    return access_token


def get_headers(access_token):
    headers = {'authorization': 'Bearer ' + access_token}
    headers.update(settings['headers'])
    return headers


async def mlengine_predict(redis, data, model_type):
    access_token = get_access_token(redis)
    headers = get_headers(access_token)
    async with ClientSession() as session:
        async with session.post(
                settings[model_type]['url'],
                data=jdumps({'instances': [data]}),
                headers=headers,
                timeout=10) as resp:
            text = await resp.text()
    return jloads(text), resp.status == OK_STATUS


def generetate_predict_data(date_arrival, date_leaving, guests, volume):
    arrival = datetime.strptime(date_arrival, '%d/%m/%Y')
    leaving = datetime.strptime(date_leaving, '%d/%m/%Y')
    today = datetime.now()
    search_data = dict(
        booking_window_in=float((arrival - today).days),
        nights_in=float((leaving - arrival).days),
        volume=float(volume),
        guests=float(guests),
        date_arrival_dow=arrival.weekday(),
        date_leaving_dow=leaving.weekday(),
        created_at_dow=today.weekday(),
    )
    return search_data


async def request_responsive(redis,
                             date_arrival,
                             date_leaving,
                             guests_number,
                             volume):
    search_data = generetate_predict_data(date_arrival,
                                          date_leaving,
                                          guests_number,
                                          volume
                                          )

    predictions_key = get_predictions_key(search_data)

    predictions = redis.get(predictions_key)
    if predictions:
        predictions = jloads(predictions)
    else:
        predictions, is_ok = await mlengine_predict(
            redis, search_data, RESPONSIVE
        )
        if is_ok:
            redis.set(predictions_key, jdumps(predictions))
    searches = predictions['predictions'][0]
    guests = int(guests_number)
    min_value = settings['responsive']['min_value']
    searches = [process_output(jloads(search.replace("'", '"')), guests, value)
                for search, value in searches.items()
                if value >= min_value]
    return searches


def process_output(search, guests_number, value):
    today = datetime.now()
    booking = timedelta(days=search['booking_window'])
    nights = timedelta(days=search['nights'])
    date_arrival = (today + booking)
    date_leaving = (date_arrival + nights)
    search_processed = dict(
        date_arrival=date_arrival.strftime('%d/%m/%Y'),
        date_leaving=date_leaving.strftime('%d/%m/%Y'),
        guests_number=guests_number,
        value=value
    )
    return search_processed


def request_two_guests(date_arrival, date_leaving):
    return dict(date_arrival=date_arrival,
                date_leaving=date_leaving,
                guests_number=2,
                value=0.5)
