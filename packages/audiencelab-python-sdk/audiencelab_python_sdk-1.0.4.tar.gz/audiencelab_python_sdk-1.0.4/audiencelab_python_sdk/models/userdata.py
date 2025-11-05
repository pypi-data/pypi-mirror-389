from datetime import datetime, timezone, timedelta
from ..sdk_version import SDKVersion


class UserData:
    def __init__(self):
        self.data = {
            "creative_info": {},
            "device_info": {}
        }
        self.user_id = None
        self.client_ip_address = None
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.app_version = "unknown"

    def set_user_id(self, user_id):
        self.user_id = user_id
        return self

    def set_user_ip(self, ip_address):
        self.client_ip_address = ip_address
        return self
    
    def set_app_version(self, app_version):
        self.app_version = app_version
        return self

    def set_last_login(self, last_login):
        try:
            datetime.fromisoformat(last_login)
        except ValueError:
            raise ValueError("Invalid date format for last login")
        self.data["creative_info"]["last_login_date"] = last_login
        return self

    def set_event_timestamp(self, timestamp):
        try:
            # First, try the standard fromisoformat
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            # If that fails, try common datetime formats
            formats = [
                "%a %b %d %Y %H:%M:%S %Z%z",  # e.g., "Mon Jan 01 2020 12:00:00 GMT+0000"
                "%Y-%m-%dT%H:%M:%S.%f%z",      # e.g., "2020-01-01T12:00:00.000000+0000"
                "%Y-%m-%d %H:%M:%S",           # e.g., "2020-01-01 12:00:00"
                "%Y-%m-%dT%H:%M:%S"            # e.g., "2020-01-01T12:00:00"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            else:  # No format matched
                raise ValueError(f"Could not parse timestamp: {timestamp}. Expected ISO format or common datetime format.")
    
        # If dt is naive (i.e. has no timezone info), assume it's in the system's local timezone.
        if dt.tzinfo is None:
            local_tz = datetime.now().astimezone().tzinfo
            dt = dt.replace(tzinfo=local_tz)
        
        # Convert the datetime to UTC
        dt = dt.astimezone(timezone.utc)

        # Store the UTC ISO 8601 formatted timestamp
        self.timestamp = dt.isoformat()
        return self

    def set_device_info(self, device_info):
        """
        Sets the device information with type checking and validation.
        
        Args:
            device_info (dict): The device information object with the following fields:
                - device_name (str): The device name (required)
                - height (int): The window height (required)
                - width (int): The window width (required)
                - os (str): The operating system (required)
                - os_version (str): The operating system version (required)
                - device_model (str): The device model (required)
                - timezone (str): The timezone (required)
                - device_vendor (str, optional): The device vendor
                - madid (str, optional): The Mobile advertising ID
                - advertiser_tracking_enabled (bool, optional): Advertiser tracking enabled
                - application_tracking_enabled (bool, optional): Application tracking enabled
                - dpi (int, optional): The device DPI
                - screen_density (float, optional): The screen density
                - cores (int, optional): The number of cores
                - ext_stor_size (int, optional): The external storage size
                - free_stor (int, optional): The free storage
                - low_battery_level (bool, optional): Low battery level
                - locale (str, optional): The locale
                - carrier (str, optional): The carrier
        
        Returns:
            UserData: The UserData instance for method chaining
            
        Raises:
            ValueError: If any required field is missing
            TypeError: If a field has an incorrect type
        """
        # Validate that device_info is a dictionary
        if not isinstance(device_info, dict):
            raise TypeError("device info must be a dictionary")
            
        
        # Validate required fields
        required_fields = {
            "device_name": str,
            "device_model": str,
            "timezone": str
        }
        
        for field, field_type in required_fields.items():
            if field not in device_info:
                raise ValueError(f"Missing required device info field: {field}")
            if not isinstance(device_info[field], field_type):
                raise TypeError(f"Field {field} must be of type {field_type.__name__}")
        
        # Check for height/width (either direct or as window_height/width)
        if not any(field in device_info for field in ["height", "window_height"]):
            raise ValueError("Missing required device info field: height or window_height")
        if not any(field in device_info for field in ["width", "window_width"]):
            raise ValueError("Missing required device info field: width or window_width")
            
        # Check for OS information
        if "os" not in device_info:
            raise ValueError("Missing required device info field: os")
        if "os_version" not in device_info:
            raise ValueError("Missing required device info field: os_version")
            
        # Create a copy of the device info to avoid modifying the original
        self.data["device_info"] = device_info.copy()
        
        # Map height/width to window_height/window_width if needed
        if "height" in self.data["device_info"] and "window_height" not in self.data["device_info"]:
            self.data["device_info"]["window_height"] = self.data["device_info"]["height"]
            del self.data["device_info"]["height"]
        if "width" in self.data["device_info"] and "window_width" not in self.data["device_info"]:
            self.data["device_info"]["window_width"] = self.data["device_info"]["width"]
            del self.data["device_info"]["width"]
            
        # Create os_system from os and os_version if not already present
        if "os_system" not in self.data["device_info"]:
            os_value = self.data["device_info"]["os"]
            os_version = self.data["device_info"]["os_version"]
            self.data["device_info"]["os_system"] = f"{os_value} {os_version}"
        

        return self

    def set_user_creative_token_info(self, creative_token_or_info, madid=None, os_system=None, device_name=None, device_model=None, utc_offset=None, install_date=None, last_login_date=None):
        """
        Sets the user's creative token information.

        This method accepts either:
        - A single dictionary containing all creative info fields.
        - Individual parameters for each field.

        If a dictionary is provided as the first argument, it will be used directly.
        Otherwise, the provided individual parameters will be used to construct the creative info.
        """
        if isinstance(creative_token_or_info, dict):
            # Check if creative_token is in the dict but under a different name
            if "creativeToken" in creative_token_or_info and "creative_token" not in creative_token_or_info:
                creative_token_or_info["creative_token"] = creative_token_or_info.pop("creativeToken")
            # Handle potential null/None values in the response
            filtered_info = {k: v for k, v in creative_token_or_info.items() if v is not None}
            self.data["creative_info"].update(filtered_info)
        else:
            # Filter out None values
            update_dict = {
                "creative_token": creative_token_or_info,
                "madid": madid,
                "os_system": os_system,
                "device_name": device_name,
                "device_model": device_model,
                "utc_offset": utc_offset,
                "install_date": install_date,
                "last_login_date": last_login_date
            }
            filtered_dict = {k: v for k, v in update_dict.items() if v is not None}
            self.data["creative_info"].update(filtered_dict)
        
        # Copy device info fields to creative info if they're not already there
        device_info = self.data.get("device_info", {})
        if device_info and not self.data["creative_info"].get("device_name") and device_info.get("device_name"):
            self.data["creative_info"]["device_name"] = device_info["device_name"]
        if device_info and not self.data["creative_info"].get("device_model") and device_info.get("device_model"):
            self.data["creative_info"]["device_model"] = device_info["device_model"]
        if device_info and not self.data["creative_info"].get("os_system"):
            # Try different field names for OS
            os_value = device_info.get("os_system") or device_info.get("os")
            if os_value:
                self.data["creative_info"]["os_system"] = os_value
        
        # If not already set, default to "organic" creative token
        if not self.data["creative_info"].get("creative_token"):
            self.data["creative_info"]["creative_token"] = "organic"
            
        # Set defaults for fields that might be missing but required
        if not self.data["creative_info"].get("install_date"):
            self.data["creative_info"]["install_date"] = self.timestamp
        if not self.data["creative_info"].get("last_login_date"):
            self.data["creative_info"]["last_login_date"] = self.timestamp
        if not self.data["creative_info"].get("utc_offset"):
            self.data["creative_info"]["utc_offset"] = "+00:00"
        
        return self

    def get_retention(self):
        # Get user retention data.
        ret_check = self.can_set_retention()
        if not ret_check["status"]:
            raise ValueError(ret_check["message"])

        install_str = self.data["creative_info"]["install_date"]
        last_login_str = self.data["creative_info"]["last_login_date"]
        install = datetime.fromisoformat(install_str)
        last_login = datetime.fromisoformat(last_login_str)
        local = datetime.fromisoformat(self.timestamp)

        retention_day = (local - install).days
        backfill_day = max(0, (last_login - install).days)

        return {"backfill_day": backfill_day, "retention_day": retention_day}

    def get_app_event_data(self):
        # Check that we have all the required fields for retention
        ret_check = self.can_set_retention()
        if not ret_check["status"]:
            raise ValueError(ret_check["message"])

        # Check that we have all the required creative info fields
        event_check = self.can_send_app_event()
        if not event_check["status"]:
            raise ValueError(event_check["message"])

        retention = self.get_retention()
        creative_info = self.data.get("creative_info", {})

        return {
            "utc_offset": creative_info.get("utc_offset"),
            "creativeToken": creative_info.get("creative_token"),
            "device_name": creative_info.get("device_name"),
            "device_model": creative_info.get("device_model"),
            "os_system": creative_info.get("os_system"),
            "retention_day": retention.get("retention_day", 0),
            "sdk_version": SDKVersion.get_version(),
            "sdk_type": SDKVersion.get_sdk_type(),
            "app_version": self.app_version,
            "client_ip": self.client_ip_address,
            "timestamp": self.timestamp
        }

    def can_identify(self):
        if not self.user_id:
            return {"status": False, "message": "User ID is required."}
        if not self.client_ip_address:
            return {"status": False, "message": "User IP address is required."}
        device_info = self.data.get("device_info")
        if not device_info:
            return {"status": False, "message": "No device info set."}
        if "device_name" not in device_info:
            return {"status": False, "message": "Missing required device info field: device_name"}
        if "window_height" not in device_info: 
            return {"status": False, "message": "Missing required device info field: height"}
        if "window_width" not in device_info: 
            return {"status": False, "message": "Missing required device info field: width"}
        if "os_system" not in device_info:
            return {"status": False, "message": "Missing required device info field: os, os_version"}
        if "device_model" not in device_info:
            return {"status": False, "message": "Missing required device info field: device_model"}
        if "timezone" not in device_info:
            return {"status": False, "message": "Missing required device info field: timezone"}
        return {"status": True, "message": ""}

    def can_fetch_token(self):
        if not self.user_id:
            return {"status": False, "message": "User ID is required."}
        return {"status": True, "message": ""}

    def can_set_retention(self):
        if not self.user_id:
            return {"status": False, "message": "User ID is required."}
        if not self.timestamp:
            return {"status": False, "message": "Timestamp is required"}
        creative_info = self.data.get("creative_info", {})
        if "install_date" not in creative_info:
            return {"status": False, "message": "Installation date is required. Fetch creative token info"}
        if "last_login_date" not in creative_info:
            return {"status": False, "message": "Last login date is required. Fetch creative token info"}
        return {"status": True, "message": ""}

    def can_send_app_event(self):
        retention_valid = self.can_set_retention()
        if not retention_valid["status"]:
            return retention_valid
        if not self.client_ip_address:
            return {"status": False, "message": "User IP address is required."}
        creative_info = self.data.get("creative_info", {})
        required_fields = ["utc_offset", "creative_token", "device_model", "device_name", "os_system"]
        for field in required_fields:
            if field not in creative_info:
                return {"status": False, "message": "Missing required creative info fields. Fetch creative token info"}
        return {"status": True, "message": ""}

    def get_device_info_json(self):
        import json
        payload = self.data.get("device_info", {}).copy()
        payload["user_id"] = self.user_id
        payload["ip_address"] = self.client_ip_address
        payload["timestamp"] = self.timestamp
        return json.dumps(payload)
    
    def get_sdk_version(self):
        return SDKVersion.get_version()
    
    def get_app_version(self):
        return self.app_version