from datetime import datetime

from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from sentinelhub import SHConfig, DataCollection, BBox
from sentinelhub.api.catalog import get_available_timestamps


def get_last_two_timestamps(
    data_collection: DataCollection, config: SHConfig, bbox: BBox
) -> list:
    """
    get last two timestamps for given bbox in collection.

    Args:
        data_collection: data type
        config: sentinel hub config
        bbox: bbox of region

    Returns:
        list of two last timestamps
    """
    today_ts = today()
    two_months_ago_ts = today_ts - relativedelta(months=2)
    time_of_interest = (two_months_ago_ts, today_ts)

    timestamps = get_available_timestamps(
        bbox=bbox,
        time_interval=time_of_interest,
        data_collection=data_collection,
        config=config,
    )
    return timestamps[-2:]


def get_last_month_span(timestamp: str) -> list:
    date = datetime.strptime(timestamp, "%d-%m-%Y")

    month_ago = date - relativedelta(months=1)

    return [month_ago, date]
