import os
import requests
from enum import Enum


# define schema for allowed method here
class VolueMethod(Enum):
    post = 'POST'
    get = 'GET'


class VolueApi:

    def __init__(self):
        self.api_urlbase = 'https://api.volueinsight.com/api'
        self.auth_urlbase = 'https://auth.volueinsight.com/oauth2/token'
        self.client_id = os.getenv('VOLUE_CLIENT_ID')
        self.client_secret = os.getenv('VOLUE_CLIENT_SECRET')
        # with this setup a new token is fetched for each request; could be improved
        self.access_token = self.get_access_token()


    def get_access_token(self):
        resp_auth = requests.post(self.auth_urlbase,
                                 data={'grant_type': 'client_credentials'},
                                 auth=(self.client_id, self.client_secret))
        return resp_auth.json()['access_token']

    def send_request(self,  endpoint: str, method: VolueMethod = VolueMethod.get, data: dict = None):
        """

        :param endpoint: (str)
        :param method: (enum) GET or POST
        :param data: (dict) data to send with POST
        :return: request response as dict
        """
        url = f'{self.api_urlbase}/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        try:
            if method == VolueMethod.get:
                resp = requests.get(url, headers=headers)
            elif method == VolueMethod.post:
                resp = requests.post(url, data=data, headers=headers)
            resp.raise_for_status()
        except requests.HTTPError as ex:
            # possibly check response for a message
            raise ex  # let the caller handle it
        except requests.Timeout:
            raise Exception("VolueApi send_request timed out")
        #return data
        return resp.json()


if __name__ == "__main__":
    # define env here
    os.environ["ENV"] = "development"
    # load env variables from .env.* file
    from pathlib import Path
    from dotenv import load_dotenv
    ENV = os.getenv("ENV")
    env_file = str(Path(__file__).parents[3] / f'.env.{ENV}')
    load_dotenv(env_file)

    # test code
    api = VolueApi()
    resp = api.send_request(endpoint="frequencies")
    a = 1

