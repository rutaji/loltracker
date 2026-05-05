
def split_name(name):
    if not name:
        return ["", ""]

    parts = name.split('#', 1)
    if len(parts) == 1:
        return [parts[0], ""]

    return parts