# Worker revision under review.
def normalize_payload(payload):
    allowed = {"id", "name"}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(f"unknown fields: {sorted(unknown)}")
    return {key: payload[key] for key in allowed if key in payload}
