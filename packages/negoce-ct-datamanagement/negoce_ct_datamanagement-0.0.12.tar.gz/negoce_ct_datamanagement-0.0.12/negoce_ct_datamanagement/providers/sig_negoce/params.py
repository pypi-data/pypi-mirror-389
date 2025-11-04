from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List


def get_params(curves_id: List[int], date_from: datetime, date_to: datetime) -> list:
    """

    :param curves_id:
    :param date_from:
    :param date_to:
    :return:
    """
    dt_delta_min = int((date_to - date_from).total_seconds() / 60)
    points = []
    for t in range(0, dt_delta_min, 15):
        point_ts = (date_from + timedelta(minutes=t)).astimezone(ZoneInfo('Europe/Zurich')).timestamp() * 1000
        if curves_id[0] == 3900:  # icon00
            points.append([point_ts, 0.8])
        elif curves_id[0] == 3901:  # ec00
            points.append([point_ts, 0.2])
        else:
            raise ValueError(f'No timeseries params found for id {curves_id[0]}')
    # format volue-like to leverage convert_to_ts function
    return [{
        'modified': datetime.now().isoformat(),
        'frequency': 'MIN15',
        'points': points
    }]
