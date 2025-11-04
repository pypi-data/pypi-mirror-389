import os
import requests
from enum import Enum
from datetime import datetime, timedelta
import httpx
import asyncio
import logging
logger = logging.getLogger("meteocontrol.api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
# Singleton instance
_api_instance = None

# Singleton async instance
_api_async_instance = None

def get_api():
    """Returns a singleton instance of MeteoControlApi"""
    global _api_instance
    if _api_instance is None:
        _api_instance = MeteoControlApi()
    return _api_instance

def get_api_async():
    """Returns a singleton instance of AsyncMeteoControlApi"""
    global _api_async_instance
    if _api_async_instance is None:
        _api_async_instance = AsyncMeteoControlApi()
    return _api_async_instance


# define schema for allowed method here
class MeteoControlMethod(Enum):
    post = 'POST'
    get = 'GET'


class MeteoControlMethod(Enum):
    get = "GET"
    post = "POST"


class MeteoControlApi:
    """
    Documentation: https://meteocontrol.github.io/vcom-api/
    Rate limits:
        - 90 call/minutes
        - 10000 call/day
        notes: login endpoint has stricter limits: 10 call/minute, 7200 call/day
    Technical contact: technique@bolay.co
    """

    def __init__(self):
        self.api_urlbase = 'https://api.meteocontrol.de/v2'
        self.api_key = os.getenv('METEOCONTROL_API_KEY')
        self.username = os.getenv('METEOCONTROL_USERNAME')
        self.password = os.getenv('METEOCONTROL_PASSWORD')
        
        self.access_token = None
        self.token_expiry = None
        # Set default token expiry to 30 minutes before the actual expiry
        # This provides a safety margin
        self.token_validity_period = 60 * 60  # 1 hour in seconds
        self.token_safety_margin = 30 * 60    # 30 minutes in seconds
        self.last_limits = {}

    def _update_and_log_limits(self, resp):
        try:
            # snapshot de tous les X-RateLimit-*
            limits = {k: v for k, v in resp.headers.items() if k.lower().startswith("x-ratelimit-")}
            if limits:
                self.last_limits = limits
                logger.info("🔖 API limits: %s", limits)
                # log compact (minute & day si présents)
                m_rem = limits.get("X-RateLimit-Remaining-Minute")
                d_rem = limits.get("X-RateLimit-Remaining-Day")
                m_lim = limits.get("X-RateLimit-Limit-Minute")
                d_lim = limits.get("X-RateLimit-Limit-Day")
                m_rst = limits.get("X-RateLimit-Reset-Minute") or limits.get("X-RateLimit-Reset")
                d_rst = limits.get("X-RateLimit-Reset-Day")
                logger.info(
                    f"RateLimit minute {m_rem}/{m_lim} (reset={m_rst}), "
                    f"day {d_rem}/{d_lim} (reset={d_rst})"
                )
        except Exception:
            pass

    def ensure_token(self):
        """Refresh the token only if expired or not available."""
        current_time = datetime.utcnow()
        
        # Get a new token if:
        # 1. No token exists
        # 2. Token expiry time exists and has passed
        if (self.access_token is None or 
            self.token_expiry is None or 
            current_time >= self.token_expiry):
            self.get_access_token()

    def get_access_token(self):
        """Get a new access token and set its expiration time."""
        resp_auth = requests.post(
            url=self.api_urlbase + '/login',
            headers={
                'content-type': 'application/x-www-form-urlencoded',
                'x-api-key': self.api_key
            },
            data={
                'grant_type': 'password',
                'client_id': 'vcom-api',
                'client_secret': 'AYB=~9_f-BvNoLt8+x=3maCq)>/?@Nom',
                'username': self.username,
                'password': self.password,
            },
        )

        print(f"[Auth] Status code: {resp_auth.status_code}")
        print(f"[Auth] Remaining requests this minute: {resp_auth.headers.get('X-RateLimit-Remaining-Minute')}")
        
        if resp_auth.status_code != 200:
            print(f"[Auth] Response text: {repr(resp_auth.text)}")
            raise Exception(f"Authentication failed with status code {resp_auth.status_code}.")

        try:
            auth_data = resp_auth.json()
            new_token = auth_data['access_token']
            
            # Set the token expiry time with safety margin
            # If expires_in is provided in the response, use it; otherwise use default
            expires_in = auth_data.get('expires_in', self.token_validity_period)
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - self.token_safety_margin)
            
            if self.access_token != new_token:
                print(f"[Auth] 🔁 New token acquired at {datetime.utcnow().isoformat()}Z")
                print(f"[Auth] Token will be considered expired at {self.token_expiry.isoformat()}Z")
            else:
                print(f"[Auth] ✅ Reusing existing token.")
            
            self.access_token = new_token
            return new_token
        except Exception as e:
            print("Error processing authentication response:", e)
            raise

    def send_request(self, endpoint: str, method: MeteoControlMethod = MeteoControlMethod.get, data: dict = None):
        """
        Send a request to the MeteoControl API.

        :param endpoint: (str) API endpoint to call
        :param method: (enum) GET or POST
        :param data: (dict) data to send with POST
        :return: request response as dict
        """
        # Ensure we have a valid token before making the request
        self.ensure_token()
        
        url = f'{self.api_urlbase}/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'x-api-key': self.api_key
        }
        
        try:
            if method == MeteoControlMethod.get:
                resp = requests.get(url, headers=headers)
                self._update_and_log_limits(resp)
                resp.raise_for_status()
            elif method == MeteoControlMethod.post:
                resp = requests.post(url, json=data, headers=headers)
            
            remaining_minute = resp.headers.get('X-RateLimit-Remaining-Minute')
            remaining_day = resp.headers.get('X-RateLimit-Remaining-Day')

            if remaining_minute is not None or remaining_day is not None:
                logger.info(
                    f"Rate limits → minute: {remaining_minute}, day: {remaining_day}"
                )

            if remaining_minute and int(remaining_minute) < 20:
                logger.warning(f"⚠️ Approche de la limite/minute: {remaining_minute} restantes")
            
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as ex:
            self._update_and_log_limits(ex.response)
            if ex.response.status_code == 401:
                # Token might be expired or invalid, try to refresh once
                print("[Auth] Received 401 error, refreshing token and retrying...")
                self.access_token = None  # Force token refresh
                self.ensure_token()
                
                # Retry the request with the new token
                headers['Authorization'] = f'Bearer {self.access_token}'
                if method == MeteoControlMethod.get:
                    retry_resp = requests.get(url, headers=headers)
                elif method == MeteoControlMethod.post:
                    retry_resp = requests.post(url, json=data, headers=headers)
                
                retry_resp.raise_for_status()
                return retry_resp.json()
            if ex.response.status_code == 429:
                logger.error("429 Too Many Requests – limites au moment de l’erreur: %s", self.last_limits)
            else:
                print(f"HTTP Error: {ex.response.status_code} - {ex.response.text}")
                raise
        except requests.Timeout:
            raise Exception("MeteoControlApi send_request timed out")
        except Exception as e:
            print(f"Unexpected error in send_request: {e}")
            raise


class AsyncMeteoControlApi:
    """
    Async version of MeteoControlApi using httpx
    """
    def __init__(self):
        self.api_urlbase = 'https://api.meteocontrol.de/v2'
        self.api_key = os.getenv('METEOCONTROL_API_KEY')
        self.username = os.getenv('METEOCONTROL_USERNAME')
        self.password = os.getenv('METEOCONTROL_PASSWORD')
        self.access_token = None
        self.token_expiry = None
        self.token_validity_period = 60 * 60
        self.token_safety_margin = 30 * 60
        self._token_lock = asyncio.Lock()

    async def ensure_token(self):
        async with self._token_lock:
            now = datetime.utcnow()
            if (
                self.access_token is None or
                self.token_expiry is None or
                now >= self.token_expiry
            ):
                await self.get_access_token()

    async def get_access_token(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url=self.api_urlbase + '/login',
                headers={
                    'content-type': 'application/x-www-form-urlencoded',
                    'x-api-key': self.api_key
                },
                data={
                    'grant_type': 'password',
                    'client_id': 'vcom-api',
                    'client_secret': 'AYB=~9_f-BvNoLt8+x=3maCq)>/?@Nom',
                    'username': self.username,
                    'password': self.password,
                },
                timeout=15
            )

            if resp.status_code != 200:
                raise Exception(f"[Auth] Failed with {resp.status_code}: {resp.text}")

            auth_data = resp.json()
            self.access_token = auth_data['access_token']
            expires_in = auth_data.get('expires_in', self.token_validity_period)
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - self.token_safety_margin)

    async def send_request(self, endpoint: str, method: MeteoControlMethod = MeteoControlMethod.get, data: dict = None):
        await self.ensure_token()
        url = f'{self.api_urlbase}/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'x-api-key': self.api_key
        }

        async with httpx.AsyncClient(timeout=15) as client:
            while True:  # Boucle pour relancer après pause si nécessaire
                try:
                    if method == MeteoControlMethod.get:
                        resp = await client.get(url, headers=headers)
                    elif method == MeteoControlMethod.post:
                        resp = await client.post(url, json=data, headers=headers)

                    # Check rate limits
                    remaining_minute = resp.headers.get("X-RateLimit-Remaining-Minute")
                    remaining_day = resp.headers.get("X-RateLimit-Remaining-Day")
                    # print(f"[Endpoint] {url} - Status code: {resp.status_code}")
                    if remaining_minute is not None:
                        # print(f"[RateLimit] Remaining requests this minute: {remaining_minute}")
                        if int(remaining_minute) <= 30:
                            # print("[RateLimit] 🕒 Waiting 50 seconds due to rate limit")
                            await asyncio.sleep(50)
                            continue  

                    # if remaining_day is not None:
                    #     print(f"[RateLimit] Remaining requests today: {remaining_day}")

                    resp.raise_for_status()
                    return resp.json()

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        self.access_token = None
                        return await self.send_request(endpoint, method, data)
                    raise
                except Exception as e:
                    print(f"[Async] Error during send_request: {e}")
                    raise



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
    api = MeteoControlApi()
    resp = api.send_request(endpoint="session")
    a = 1

