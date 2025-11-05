from decimal import Decimal


class UpdateCumulativeValues:
    """
    Manages cumulative value tracking and updates.
    
    This class handles:
    - Detecting if an event needs cumulative tracking
    - Calculating new cumulative totals
    - Sending updates to backend
    - Updating local creative_info state
    """
    
    def __init__(self, api_client, user_data, event_type, payload):
        """
        Initialize the cumulative value manager.
        
        Args:
            api_client: The API client instance
            user_data: UserData instance with creative_info
            event_type (str): Type of event ("purchase", "ad", etc.)
            payload (dict): Event payload containing value and current totals
        """
        self.api_client = api_client
        self.user_data = user_data
        self.event_type = event_type
        self.payload = payload
    
    
    
    def calculate_and_send(self):
        """
        Calculate and send cumulative value update.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        
        try:
            # Determine field name based on event type
            if self.event_type == "purchase":
                field_name = "total_purchase_value"
            elif self.event_type == "ad":
                field_name = "total_ad_value"
            else:
                return True  # Not applicable, consider success
            
            # Get current total from creative_info
            current_total = self.user_data.data["creative_info"].get(field_name, 0)
            
            # Convert current total to Decimal for precise arithmetic
            try:
                if isinstance(current_total, Decimal):
                    current_total_decimal = current_total
                elif isinstance(current_total, (int, float)):
                    current_total_decimal = Decimal(str(current_total))
                elif isinstance(current_total, str):
                    current_total_decimal = Decimal(current_total)
                elif current_total is None:
                    current_total_decimal = Decimal('0')
                else:
                    current_total_decimal = Decimal('0')
            except (ValueError, TypeError, Exception):
                current_total_decimal = Decimal('0')
            
            # Get event value and convert to Decimal
            event_value = self.payload.get("value", 0)
            try:
                if isinstance(event_value, Decimal):
                    event_value_decimal = event_value
                elif isinstance(event_value, (int, float)):
                    event_value_decimal = Decimal(str(event_value))
                elif isinstance(event_value, str):
                    event_value_decimal = Decimal(event_value)
                elif event_value is None:
                    event_value_decimal = Decimal('0')
                else:
                    event_value_decimal = Decimal('0')
            except (ValueError, TypeError, Exception):
                event_value_decimal = Decimal('0')
            
            # Calculate new total using Decimal for precision
            new_total_decimal = current_total_decimal + event_value_decimal
            
            # Validate that the sum is positive
            if new_total_decimal < 0:
                raise ValueError(f"Cumulative total cannot be negative: {new_total_decimal}")
            
            # Convert to float for JSON serialization and storage
            new_total = float(new_total_decimal)
            
            # Send update to backend first
            self._send_update(field_name, new_total, user_data=self.user_data)
            
            # Only update local state if backend update succeeded
            self._update_local_state(field_name, new_total)

            return True
            
        except Exception as e:
            # According to requirements, cumulative update must succeed before sending webhook
            raise ValueError(f"Failed to update cumulative values: {str(e)}")
    
    def _send_update(self, field_name, new_total, user_data):
        """
        Send the updated cumulative value to the backend.
        
        Args:
            field_name (str): "total_purchase_value" or "total_ad_value"
            new_total (float): The new cumulative total (converted from Decimal for JSON)
            user_data: UserData instance
            
        Raises:
            ValueError: If user_id is missing or API request fails
        """
        user_id = user_data.user_id
        if not user_id:
            raise ValueError("User ID is required for cumulative value update")
        
        payload = {field_name: new_total, "user_id": user_id}
        response = self.api_client.post("/v2/cumulative", json=payload)
        
        # Raise exception if the request failed
        response.raise_for_status()
        
        return response.json()

    
    def _update_local_state(self, field_name, new_total):
        """
        Update the creative_info locally with the new total.
        
        Args:
            field_name (str): "total_purchase_value" or "total_ad_value"
            new_total (float): The new cumulative total (converted from Decimal for JSON)
        """ 
        self.user_data.data["creative_info"][field_name] = new_total

