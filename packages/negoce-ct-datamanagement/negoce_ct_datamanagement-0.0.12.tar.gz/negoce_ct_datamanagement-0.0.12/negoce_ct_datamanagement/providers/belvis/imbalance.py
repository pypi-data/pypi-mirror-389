import os
from datetime import datetime, timedelta
import pandas as pd

from negoce_ct_datamanagement.providers.belvis.requests_utils import write_timeseries


def save_daily_swissgrid_imbalance(df: pd.DataFrame):
    """

    :param df:
    :return:
    """
    # shift timeseries +15' (BelVis start day at 00:15 and end at 00:00)
    df['datetime'] = df['datetime'].apply(lambda x: datetime.fromisoformat(x) + timedelta(minutes=15))
    # convert dataframe to expected belvis timeseries
    data_short = []
    data_long = []
    data_single = []
    for index, row in df.iterrows():
        data_short.append({'ts': row['datetime'].isoformat(), 'v': row['prices_short'], 'pf': 'estimated'})
        data_long.append({'ts': row['datetime'].isoformat(), 'v': row['prices_long'], 'pf': 'estimated'})
        data_single.append({'ts': row['datetime'].isoformat(), 'v': row['prices_single'], 'pf': 'estimated'})
    # requests PUT to BelVis
    write_timeseries(timeseries_id=int(os.getenv('BELVIS_ID_Prix.Estimation.Swissgrid.Court')), data=data_short)
    write_timeseries(timeseries_id=int(os.getenv('BELVIS_ID_Prix.Estimation.Swissgrid.Long')), data=data_long)
    write_timeseries(timeseries_id=int(os.getenv('BELVIS_ID_Prix.Estimation.Swissgrid.Single')), data=data_single)
