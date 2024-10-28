from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from sentinelhub import SHConfig
from sentinelhub.api.catalog import get_available_timestamps


def get_last_two_timestamps(data_collection, config: SHConfig, bbox):
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
