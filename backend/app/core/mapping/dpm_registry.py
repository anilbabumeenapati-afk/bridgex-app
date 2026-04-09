FIELD_MAPPING = {
    "operational_availability": "DORA_AVAILABILITY_METRIC",
    "incident_notification_time": "DORA_INCIDENT_RESPONSE_TIME"
}

DPM_REGISTRY = {
    "DORA_AVAILABILITY_METRIC": {
        "dpm_id": "C_01.01.a",
        "unit": "percent",
        "validation": {
            "min": 99,
            "max": 100
        }
    },
    "DORA_INCIDENT_RESPONSE_TIME": {
        "dpm_id": "C_02.01.b",
        "unit": "minutes",
        "validation": {
            "min": 0,
            "max": 60
        }
    }
}