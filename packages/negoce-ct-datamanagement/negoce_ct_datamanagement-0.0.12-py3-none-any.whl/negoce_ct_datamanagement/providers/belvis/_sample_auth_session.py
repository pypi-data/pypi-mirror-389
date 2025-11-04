import requests
from datetime import datetime
from zoneinfo import ZoneInfo 

# belvis api config
base_url = 'http://v843:25080'
tenant = 'SGB_SIG'

# session config
usr = 'lebouban'
pwd = '123'  # put your password here

with requests.Session() as s:
    # get auth cookie 
    r_session = s.get(f'{base_url}/rest/session?usr={usr}&pwd={pwd}&tenant={tenant}')
    if r_session.status_code == 200:
        print(f'session start: {s.cookies.get_dict()}')

        # example 1: get belvis monitor
        # r = s.get(f'{base_url}/rest/belvis/internal/monitor')
        # print(r.text)

        # example 2: get timeseries values
        id = 71106415  # realized PV
        date_from = datetime(2025, 3, 10).astimezone(ZoneInfo("Europe/Paris")).isoformat(timespec="minutes")
        date_to = datetime(2025, 3, 11).astimezone(ZoneInfo("Europe/Paris")).isoformat(timespec="minutes")
        url = f'{base_url}/rest/energy/belvis/{tenant}/timeseries/{id}/values?timeRange={date_from}--{date_to}&timeRangeType=inclusive-exclusive&blocking=false&precision=3'
        # url = f'{base_url}/rest/energy/belvis/{tenant}/timeseries/{id}/properties'
        url = url.replace("+", "%2B")
        r = s.get(url)
        if r.status_code != 200:
            print(f'request error: {r.__dict__}')
        print(r.text)

        # close session
        r_session_close = s.delete(f'{base_url}/rest/session/{r_session.text}')
        if r_session_close.status_code != 200:
            print(f'session end error: {r_session_close.__dict__}')

    else:
        print(f'session start error: {r_session:__dict__}')
