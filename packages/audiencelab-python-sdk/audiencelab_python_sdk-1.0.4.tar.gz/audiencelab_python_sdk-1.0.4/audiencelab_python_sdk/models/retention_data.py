class RetentionData:
    def __init__(self):
        self.data = {"type": "retention", "payload": {}}

    def set_retention_data(self, user):
        # Expecting user to have methods: can_set_retention() returning a dict and get_retention() returning retention info
        if not hasattr(user, "can_set_retention"):
            raise ValueError("Invalid input type for user data")
        result = user.can_set_retention()
        if not result.get("status", True):
            raise ValueError(result.get("message", "User cannot set retention"))
        retention_info = user.get_retention()
        self.data["payload"]["backfill_day"] = retention_info.get("backfill_day")
        self.data["payload"]["retention_day"] = retention_info.get("retention_day")
        return self

    def can_send(self):
        required_fields = ["backfill_day", "retention_day"]
        for field in required_fields:
            if field not in self.data["payload"] or self.data["payload"][field] is None:
                return {"status": False, "message": f"{field} is missing"}
        return {"status": True, "message": ""}

    def to_json(self, user_data=None):
        return self.data 