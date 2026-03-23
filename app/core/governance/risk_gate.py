def requires_senior_approval(passport):
    for field, data in passport.items():
        if not data:
            continue

        flags = data.get("risk_flags", [])

        if "SOURCE_CONTRADICTION" in flags:
            return True

    return False