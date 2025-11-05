from decimal import Decimal


class AdData:
    def __init__(self):
        """
        Initialize AdData.
        
        Note: total_ad_value is retrieved from UserData.creative_info
        (returned by backend via FetchToken/RegisterUser), similar to how
        retention_day is handled.
        """
        self.data = {"type": "ad", "payload": {}}

    def set_ad_id(self, ad_id):
        if not isinstance(ad_id, str):
            raise ValueError("Invalid input type for ad_id")
        self.data["payload"]["ad_id"] = ad_id
        return self

    def set_name(self, name):
        if not isinstance(name, str):
            raise ValueError("Invalid input type for name")
        self.data["payload"]["name"] = name
        return self

    def set_source(self, source):
        if not isinstance(source, str):
            raise ValueError("Invalid input type for source")
        self.data["payload"]["source"] = source
        return self

    def set_watch_time(self, watch_time):
        if not isinstance(watch_time, (int, float)):
            raise ValueError("Invalid input type for watch time")
        self.data["payload"]["watch_time"] = watch_time
        return self

    def set_reward(self, reward):
        self.data["payload"]["reward"] = reward
        return self

    def set_media_source(self, media_source):
        self.data["payload"]["media_source"] = media_source
        return self

    def set_channel(self, channel):
        self.data["payload"]["channel"] = channel
        return self

    def set_value(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValueError("Invalid input type for value")
        # Convert to Decimal for precision, but store as float for JSON compatibility
        decimal_value = Decimal(str(value))
        self.data["payload"]["value"] = float(decimal_value)
        # Store Decimal for internal calculations
        self._value_decimal = decimal_value
        return self

    def set_currency(self, currency):
        if not isinstance(currency, str):
            raise ValueError("Invalid input type for currency")
        self.data["payload"]["currency"] = currency
        return self
    
    def set_transaction_id(self, transaction_id):
        if transaction_id is not None and not isinstance(transaction_id, str):
            raise ValueError("Invalid input type for transaction_id")
        if transaction_id:
            self.data["payload"]["tr_id"] = transaction_id
        return self

    def can_send(self):
        # require at least ad_id, name, and source
        payload = self.data["payload"]
        required = ["ad_id", "name", "source"]
        missing = [field for field in required if field not in payload]
        if missing:
            return {"status": False, "message": f"Missing fields: {', '.join(missing)}"}
        return {"status": True, "message": "Ready to send"}

    def to_json(self, user_data=None):

        # Add total_ad_value from user's creative_info
        if user_data and hasattr(user_data, 'data'):
            creative_info = user_data.data.get("creative_info", {})
            # Use value from creative_info, or default to 0 if not present
            total_value = creative_info.get("total_ad_value", 0)
            
            # Convert to Decimal for precision, handle various input types
            try:
                if isinstance(total_value, Decimal):
                    total_value_decimal = total_value
                elif isinstance(total_value, (int, float, str)):
                    total_value_decimal = Decimal(str(total_value))
                else:
                    total_value_decimal = Decimal('0')
            except (ValueError, TypeError):
                total_value_decimal = Decimal('0')
            
            # Store as Decimal internally, convert to float for JSON
            creative_info["total_ad_value"] = float(total_value_decimal)
            self.data["payload"]["total_ad_value"] = float(total_value_decimal)
        
        return self.data 