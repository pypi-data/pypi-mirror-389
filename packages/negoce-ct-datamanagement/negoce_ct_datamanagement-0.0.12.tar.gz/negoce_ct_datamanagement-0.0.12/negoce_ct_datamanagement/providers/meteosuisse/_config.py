import requests
import os
from enum import Enum


class HttpMethod(Enum):
    get = "GET"


class MeteoSwissSMNApi:
    """
    Classe responsable de la configuration et de l'envoi des requêtes HTTP
    vers l'API STAC MeteoSwiss.
    """

    def __init__(self, base_stac: str = None, collection: str = None, timeout: int = 30):
        self.base_stac = base_stac or os.getenv("METEOSWISS_BASE_URL", "https://data.geo.admin.ch/api/stac/v1")
        self.collection = collection or os.getenv("METEOSWISS_COLLECTION", "ch.meteoschweiz.ogd-smn")
        self.timeout = timeout
        self.session = requests.Session()

    def send_request(self, endpoint: str, method: HttpMethod = HttpMethod.get, params=None, headers=None) -> dict:
        """
        Envoie une requête HTTP simple vers l'API MeteoSwiss STAC.
        """
        url = f"{self.base_stac.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            if method == HttpMethod.get:
                resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
            else:
                raise ValueError(f"HttpMethod non supporté : {method.value}")
        except requests.HTTPError as ex:
            raise ex
        except requests.Timeout:
            raise Exception("MeteoSwissSMNApi send_request timed out")

        if resp.text == "":
            return {}
        return resp.json()
