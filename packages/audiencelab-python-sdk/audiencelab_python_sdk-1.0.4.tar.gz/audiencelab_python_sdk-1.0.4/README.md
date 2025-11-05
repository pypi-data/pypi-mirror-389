# AudienceLab Python SDK

With the introduction of Apple's App Tracking Transparency (ATT) framework, mobile advertisers have faced significant challenges in measuring ad performance on iOS. This challenge is set to expand further with Google's upcoming Privacy Sandbox, reducing visibility into user-level attribution.

Geeklab is dedicated to developing a privacy-first marketing performance analytics platform that enables advertisers to gain actionable insights while adhering to evolving data privacy regulations. Our solution aggregates performance data at the device/developer server level and provides creative-level analytics, ensuring that advertisers can optimize campaigns without relying on user-level tracking.

## Overview

The Audiencelab Python SDK is a lightweight client library for integrating with the AudienceLab API. It simplifies:

- User registration and creative token fetching
- Sending in-app events (purchases, ad views, retention events)
- Collecting and managing device and user information
- Automatic cumulative value tracking for purchase and ad revenue

## Installation

`pip install audiencelab-python-sdk`

## Basic Usage

### 1. Initialize the Client and Construct User Data

First, import the necessary classes from the SDK. Create a client instance using your API key and base URL, and then build the user data object.

> Note: Detailed device information is only required during the initial user registration. For all subsequent events, simply provide the user ID and IP address. If the event did not occur in real time, be sure to include the event timestamp (ISO 8601).

```python
from audiencelab_python_sdk import Client, UserData, RegisterUser, FetchToken, RetentionData, PurchaseData, AdData, AppEvent

api_key = "your_api_key"
base_url = "https://example.com"
client = Client(api_key, base_url)

# Initialize UserData
user_data = UserData() \
    .set_user_id("user_12345") \
    .set_user_ip("123.123.1.1") \
    .set_app_version("1.2.3") \
    .set_event_timestamp("2024-10-05T16:48:00+02:00") \
    .set_device_info({
        "device_name": "My Device",
        "height": 2436,
        "width": 1125,
        "os": "iOS",
        "os_version": "14.4",
        "device_model": "iPhone15,4",
        "timezone": "America/New_York"
    })
```

### 2.1 Register a User

Register a new user; Call this only once when a new user first downloads and opens the app.

This event will also return creative token information which updates your user data with the creative token information. In this case, step 2.2 is not required.

```python
register_event = RegisterUser(client, user_data)
try:
    response = register_event.send()
    user_data.set_user_creative_token_info(response)
    print("User registered & creative token information set.")
except Exception as e:
    print("Error during user registration:", e)
```

### 2.2 Fetch the Creative Token

Creative token information fetching; Call this once before sending any user related in app events.

```python
fetch_event = FetchToken(client, user_data)
try:
    response = fetch_event.send()
    user_data.set_user_creative_token_info(response)
    print("Creative token information set.")
except Exception as e:
    print("Error fetching creative token:", e)
```

### 3. Send In-App Events

> **⚠️ Note:**  
> Make sure to set both the **user ID** and the **user IP address** on your `user_data` (e.g., using `.set_user_id()` and `.set_user_ip()`) before fetching the creative token and sending an in-App event! Both are required.

#### Retention Event

The retention event should be sent each time the user opens the app, **including after the initial user registration event**.

```python
retention_data = RetentionData().set_retention_data(user_data)
retention_event = AppEvent(client, retention_data, user_data)
try:
    response = retention_event.send()
    print("Retention event sent")
except Exception as e:
    print("Error sending retention event:", e)
```

#### Purchase Event

The SDK automatically tracks cumulative purchase values. Each purchase event updates the running total on both the backend and in local state.

```python
purchase_data = PurchaseData() \
    .set_item_id("item_123") \
    .set_item_name("No Ads") \
    .set_value(3.99) \
    .set_currency("usd") \
    .set_status("completed") \
    .set_transaction_id("txn_abc123")  # Optional: unique transaction identifier
purchase_event = AppEvent(client, purchase_data, user_data)
try:
    response = purchase_event.send()
    print("Purchase event sent")
except Exception as e:
    print("Error sending purchase event:", e)
```

#### Ad View Event

The SDK automatically tracks cumulative ad revenue values. Each ad event updates the running total on both the backend and in local state.

```python
ad_data = AdData() \
    .set_ad_id("ad_123") \
    .set_name("New Game Ad") \
    .set_source("rewarded_video") \
    .set_media_source("admob") \
    .set_channel("paid") \
    .set_watch_time(4321) \
    .set_reward(True) \
    .set_value(0.00035) \
    .set_currency("usd") \
    .set_transaction_id("ad_txn_xyz789")  # Optional: unique transaction identifier
ad_event = AppEvent(client, ad_data, user_data)
try:
    response = ad_event.send()
    print("Ad view event sent")
except Exception as e:
    print("Error sending ad view event:", e)
```

## License

This project is licensed under the terms of the [GEEKLAB SDK EULA](https://github.com/Geeklab-Ltd/audiencelab_python_sdk/blob/main/LICENSE.md).
