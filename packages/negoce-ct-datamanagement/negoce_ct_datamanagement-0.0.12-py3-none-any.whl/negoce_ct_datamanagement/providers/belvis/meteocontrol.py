import os
import pandas as pd

from negoce_ct_datamanagement.providers.belvis.requests_utils import write_timeseries


def save_meteocontrol_production(df: pd.DataFrame):
    """

    :param df:
    :return:
    """
    # convert dataframe to expected belvis timeseries
    data = []
    for index, row in df.iterrows():
        data.append({'ts': row['datetime'].isoformat(), 'v': row['Meteocontrol_production_mesurée.MW.QH.O'], 'pf': 'estimated'})
    # requests PUT to BelVis
    write_timeseries(timeseries_id=int(os.getenv('BELVIS_ID_Meteocontrol_production_mesurée.MW.QH.O')), data=data)

def save_meteocontrol_nominal_power(df: pd.DataFrame):
    """

    :param df:
    :return:
    """
    # convert dataframe to expected belvis timeseries
    data = []
    for index, row in df.iterrows():
        data.append({'ts': row['datetime'].isoformat(), 'v': row['Meteocontrol_capacité_mesurée.MW.QH.O'], 'pf': 'estimated'})
    # requests PUT to BelVis
    write_timeseries(timeseries_id=int(os.getenv('BELVIS_ID_Meteocontrol_capacité_mesurée.MW.QH.O')), data=data)