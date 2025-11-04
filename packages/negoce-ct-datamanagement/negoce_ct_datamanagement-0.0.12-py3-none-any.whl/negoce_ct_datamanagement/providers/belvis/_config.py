import os

import requests
from enum import Enum


# define schema for allowed method here
class BelvisMethod(Enum):
    get = 'GET'
    put = 'PUT'


class BelvisApi:

    def __init__(self, tenant: str = 'SGB_SIG'):
        self.technical_base_url = f"{os.getenv('BELVIS_BASE_URL')}/rest/belvis/internal"
        self.timeseries_base_url = f"{os.getenv('BELVIS_BASE_URL')}/rest/energy/belvis/{tenant}"
        self.token = os.getenv(f'BELVIS_{tenant}_TOKEN')

    def send_request(self, endpoint: str, method: BelvisMethod = BelvisMethod.get, data: str = None, auth: bool = True):
        """

        :param endpoint: (str)
        :param method: (enum) GET or PUT
        :param data: (dict) data to send with PUT
        :param auth: (bool) include or not auth token in headers
        :return: request response as dict
        """
        if endpoint in ["/heartbeat/ping", "/sysinfo", "/monitor"]:
            url = f'{self.technical_base_url}{endpoint}'
        else:
            url = f'{self.timeseries_base_url}{endpoint}'
        # fix URL for BelVis API
        url = url.replace("+", "%2B")
        headers = None
        if auth:
            headers = {
                'Authorization': f'Bearer {self.token}'
            }
        try:
            if method == BelvisMethod.get:
                resp = requests.get(url, headers=headers)
                resp.raise_for_status()
            elif method == BelvisMethod.put:
                resp = requests.put(url, data=data, headers=headers)
                resp.raise_for_status()
            else:
                raise ValueError(f"Belvis method shoud be either get or put not {method.value}")
        except requests.HTTPError as ex:
            # possibly check response for a message
            raise ex  # let the caller handle it
        except requests.Timeout:
            raise Exception("BelvisApi send_request timed out")
        #return data
        if resp.text == "":
            return {}
        else:
            return resp.json()

    def ping(self):
        return self.send_request(endpoint="/heartbeat/ping")

    def sysinfo(self):
        return self.send_request(endpoint="/sysinfo")

    def monitor(self):
        return self.send_request(endpoint="/monitor")

