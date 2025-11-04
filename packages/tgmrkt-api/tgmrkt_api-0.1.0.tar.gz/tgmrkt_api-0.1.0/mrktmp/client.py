import requests


class MrktClient:
    """Client for TG MRKT API requests"""

    def __init__(self, auth_data: str, base_url: str = "https://api.tgmrkt.io/api/v1"):
        self.base_url = base_url
        self.auth_data = auth_data
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": auth_data,
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://cdn.tgmrkt.io",
            "Priority": "u=1, i",
            "Referer": "https://cdn.tgmrkt.io/",
            "Sec-Ch-Ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
        })

    def _request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                resp = self.session.get(url, params=kwargs.get("params", {}), timeout=10)
            else:
                resp = self.session.request(method, url, json=kwargs.get("json", {}), timeout=10)

            resp.raise_for_status()

            user_id = resp.headers.get("X-User-Id")
            if user_id:
                print(f"✅ Logged as User ID: {user_id}")

            return resp.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {e.response.text}"

            if e.response.status_code == 401:
                raise ValueError("Auth expired - update token from Network tab")
            elif e.response.status_code == 404:
                raise ValueError(f"Endpoint not found: {endpoint}")
            else:
                raise ValueError(error_msg)

        except requests.exceptions.Timeout:
            raise ValueError(f"Request timeout for {endpoint}")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request error: {e}")