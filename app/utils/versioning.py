def version_sort_key(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return (0,)


def normalize_version(version: str) -> str:
    if not version:
        return version

    parts = version.split(".")
    if len(parts) < 2:
        return version

    return f"{parts[0]}.{parts[1]}"