from decimal import Decimal


class PurchaseData:
    def __init__(self):
        """
        Initialize PurchaseData.
        
        Note: total_purchase_value is retrieved from UserData.creative_info
        (returned by backend via FetchToken/RegisterUser), similar to how
        retention_day is handled.
        """
        self.data = {"type": "purchase", "payload": {}}

    def set_item_id(self, item_id):
        if not isinstance(item_id, str):
            raise ValueError("Invalid input type for item_id")
        self.data["payload"]["item_id"] = item_id
        return self

    def set_item_name(self, item_name):
        if not isinstance(item_name, str):
            raise ValueError("Invalid input type for item_name")
        self.data["payload"]["item_name"] = item_name
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

    def set_status(self, status):
        "Excpected values for completion status: completed or success. Case insensitive."
        self.data["payload"]["status"] = status
        return self
    
    def set_transaction_id(self, transaction_id):
        if transaction_id is not None and not isinstance(transaction_id, str):
            raise ValueError("Invalid input type for transaction_id")
        if transaction_id:
            self.data["payload"]["tr_id"] = transaction_id
        return self

    def can_send(self):
        payload = self.data["payload"]
        required = ["item_id", "item_name", "value"]
        missing = [field for field in required if field not in payload]
        if missing:
            return {"status": False, "message": f"Missing fields: {', '.join(missing)}"}
        return {"status": True, "message": "Ready to send"}

    def to_json(self, user_data=None):

        # Add total_purchase_value from user's creative_info
        if user_data and hasattr(user_data, 'data'):
            creative_info = user_data.data.get("creative_info", {})
            # Use value from creative_info, or default to 0 if not present
            total_value = creative_info.get("total_purchase_value", 0)
            
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
            creative_info["total_purchase_value"] = float(total_value_decimal)
            self.data["payload"]["total_purchase_value"] = float(total_value_decimal)
        
        return self.data 