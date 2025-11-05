class FetchToken:
    def __init__(self, api_client, user_data):
        self.api_client = api_client
        self.user_data = user_data

    def send(self):
        # Verify that the required fields are set to fetch the creative token
        token_check = self.user_data.can_fetch_token() if hasattr(self.user_data, 'can_fetch_token') else True
        if isinstance(token_check, dict):
            if not token_check.get("status", True):
                raise ValueError(token_check.get("message", "User cannot fetch token"))
        elif not token_check:
            raise ValueError("User cannot fetch token")

        response = self.api_client.get(f"/v2/creativetoken?user_id={self.user_data.user_id}")
        return response.json() 