import requests


class Client:
    """A Python SDK client for AudienceLab services."""
    def __init__(self, api_key, base_url, timeout=20):
        if not api_key:
            raise ValueError("API Key is required.")
        if not base_url:
            raise ValueError("Base URL is required.")
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'geeklab-api-key': api_key,
        })

    def get(self, url, **kwargs):
        """Executes a GET request."""
        full_url = self.base_url + url
        response = self.session.get(full_url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response

    def post(self, url, data=None, json=None, **kwargs):
        """Executes a POST request."""
        full_url = self.base_url + url
        response = self.session.post(full_url, data=data, json=json, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response 