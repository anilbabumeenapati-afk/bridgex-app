def approve_field(field):
    field["status"] = "APPROVED"
    return field

def reject_field(field):
    field["status"] = "REJECTED"
    return field

def edit_field(field, new_value):
    field["value"] = new_value
    field["status"] = "MODIFIED"
    return field