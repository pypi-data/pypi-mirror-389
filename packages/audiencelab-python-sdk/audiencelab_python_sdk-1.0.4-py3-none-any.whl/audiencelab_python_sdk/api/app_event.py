from .update_cumulative_values import UpdateCumulativeValues


class AppEvent:
    def __init__(self, api_client, event_data, user_data):
        self.api_client = api_client
        self.event_data = event_data
        self.user_data = user_data

    def send(self):
        """
        Send an app event to the backend.
        
        For purchase and ad events with value, cumulative values are updated first.
        The webhook is only sent if cumulative update succeeds.
        
        Returns:
            dict: The JSON response from the webhook endpoint
            
        Raises:
            ValueError: If validation fails or cumulative update fails
        """
        # Check required fields in user_data
        user_check = self.user_data.can_send_app_event() if hasattr(self.user_data, 'can_send_app_event') else True

        if isinstance(user_check, dict):
            if not user_check.get("status", True):
                raise ValueError(user_check.get("message", "User cannot send app event"))
        elif not user_check:
            raise ValueError("User cannot send app event")

        # Check that event_data is ready
        event_check = self.event_data.can_send()
        if not event_check.get("status", True):
            raise ValueError(event_check.get("message", "Event data is not ready"))
        
        event_type = self.event_data.data.get("type")
        initial_payload = self.event_data.data.get("payload", {})
        
        # For purchase/ad events with value, update cumulative totals first
        # This must succeed before sending the webhook
        if event_type in ["purchase", "ad"] and "value" in initial_payload:
            cumulative_manager = UpdateCumulativeValues(
                self.api_client, 
                self.user_data, 
                event_type, 
                initial_payload
            )
            # This will raise an exception if cumulative update fails
            # ensuring the webhook is not sent
            success = cumulative_manager.calculate_and_send()
            if not success:
                raise ValueError(f"Failed to update cumulative {event_type} value")
        
        # Build event payload with updated cumulative values
        event_json = self.event_data.to_json(user_data=self.user_data)
        payload = event_json.get("payload", {})

        # Build webhook body
        body = {"type": event_type}
        if hasattr(self.user_data, 'get_app_event_data'):
            body.update(self.user_data.get_app_event_data())
        body["payload"] = payload

        # Send webhook - only reaches here if cumulative update succeeded
        response = self.api_client.post(f"/webhook", json=body)
        
        # Raise exception if webhook request failed
        response.raise_for_status()

        return response.json()
