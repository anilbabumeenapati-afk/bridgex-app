# app/core/mapping/synonym_mapper.py

SYNONYMS = {
    "operational_availability": [
        "uptime",
        "availability",
        "service availability",
        "system uptime"
    ],
    "incident_notification_time": [
        "incident response",
        "response time",
        "incident response time",
        "critical response"
    ]
}


def map_synonym(text: str):
    if not text:
        return None

    text = text.lower()

    for canonical, variants in SYNONYMS.items():
        for v in variants:
            if v in text:
                return canonical

    return None