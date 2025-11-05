import json


class RegisterUser:
    def __init__(self, api_client, user_data):
        self.api_client = api_client
        self.user_data = user_data

    def send(self):
        # Verify that required fields are set to identify the user
        if not self.user_data.can_identify():
            raise ValueError("User identification fields missing. Add user_id and user_ip to user_data.")
        payload = json.loads(self.user_data.get_device_info_json())
        response = self.api_client.post(f"/v2/fetch-token", json=payload)
        return response.json() 