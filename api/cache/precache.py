from datetime import datetime, timedelta

from psycopg2.extras import RealDictCursor

from settings import settings


PRECACHE_SETTINGS = settings['precache']
FORMAT_DATES = settings['format_dates']

async def get_popular_searches(db_conn, min_days_until_today, offset_days,
                               min_searches, max_searches=None,
                               max_results=None):
    """
        Get most popular searches in the past
    """
    max_created_at = datetime.now().date() - timedelta(min_days_until_today)
    min_created_at = max_created_at - timedelta(offset_days)
    max_created_at = max_created_at

    available_max_searches = "AND count(*) <= %(max_searches)s" \
        if max_searches else ""

    available_max_results = "LIMIT %(max_results)s" if max_results else ""

    query = f"""
        SELECT
            place_id, date_arrival, date_leaving, guest_search,
            count(DISTINCT user_id)
        FROM
            searches
        WHERE
            created_at BETWEEN %(min_created_at)s AND %(max_created_at)s
            AND place_id IS NOT NULL AND date_arrival IS NOT NULL
            AND date_leaving IS NOT NULL AND guest_search IS NOT NULL
        GROUP BY
            place_id, date_arrival, date_leaving, guest_search
        HAVING
            count(*) >= %(min_searches)s {available_max_searches}
        ORDER BY
            count(*) DESC
        {available_max_results}
    """

    params = {
        "max_created_at": str(max_created_at),
        "min_created_at": str(min_created_at),
        "min_searches": min_searches,
        "max_searches": max_searches,
        "max_results": max_results,
    }

    async with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
        await cur.execute(query, parameters=params)

        return await cur.fetchall()


async def get_precache_searches(db_conn, max_results):
    """
        Return most popular searches made in the past interval.

        {'precache':
        [
            {
                place_id: "ChIJ1SZCvy0kMgsRQfBOHAlLuCo",
                date_arrival: "15/07/2017",
                date_leaving: "20/07/2017",
                guests_number: 2
            },
            {
                place_id: "ChIJKcEGZna4lxIRwOzSAv-b67c",
                date_arrival: "15/07/2017",
                date_leaving: "20/07/2017",
                guests_number: 2
            },
        ]}
    """

    def apply_format_search(search):
        return dict(
            place_id=search['place_id'],
            date_arrival=str(search['date_arrival'].strftime(FORMAT_DATES)),
            date_leaving=str(search['date_leaving'].strftime(FORMAT_DATES)),
            guests_number=search['guest_search']
        )

    conf_model = PRECACHE_SETTINGS['model']

    searches = await get_popular_searches(
        db_conn, conf_model['min_days_until_today'],
        conf_model['offset_days'], conf_model['min_repeat_searches'],
        max_searches=conf_model['max_repeat_searches'],
        max_results=max_results
    )

    response = [apply_format_search(search) for search in searches]

    return {'precache': response}
