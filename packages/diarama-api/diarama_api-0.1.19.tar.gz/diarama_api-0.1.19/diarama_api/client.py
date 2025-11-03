import json
import requests

class DiaramaAPIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.diaramastudio.ru"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json; charset=utf-8"
        }

    def _get(self, endpoint, params=None):
        r = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint, data=None, files=None):
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()

        if files:
            headers.pop("Content-Type", None)
            r = requests.post(url, headers=headers, files=files)
        else:
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8') if data else None
            r = requests.post(url, headers=headers, data=json_data)

        r.raise_for_status()
        return r.json()

    def _put(self, endpoint, data=None):
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        r = requests.put(f"{self.base_url}{endpoint}", headers=self.headers, data=json_data)
        r.raise_for_status()
        return r.json()

    def _delete(self, endpoint):
        r = requests.delete(f"{self.base_url}{endpoint}", headers=self.headers)
        r.raise_for_status()
        return r.json()
