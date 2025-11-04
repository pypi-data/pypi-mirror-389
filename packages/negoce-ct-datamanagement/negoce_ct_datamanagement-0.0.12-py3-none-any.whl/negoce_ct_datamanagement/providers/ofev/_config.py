import requests
from enum import Enum


# define schema for allowed method here
class OfevMethod(Enum):
    get = 'GET'


class OfevApi:

    def __init__(self):
        self.api_urlbase = 'https://www.hydrodaten.admin.ch'

    def send_request(self,  endpoint: str, method: OfevMethod = OfevMethod.get):
        """

        :param endpoint: (str)
        :param method: (enum) GET or POST
        :return: request response as dict
        """
        url = f'{self.api_urlbase}/{endpoint}'
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except requests.HTTPError as ex:
            # possibly check response for a message
            raise ex  # let the caller handle it
        except requests.Timeout:
            raise Exception("VolueApi send_request timed out")
        # clean data
        data_raw = resp.json()
        data = []
        for serie in data_raw['plot']['data']:
            data.append({
                'name': serie['name'],
                'values': list(zip(serie['x'], serie['y']))
            })
        return data
