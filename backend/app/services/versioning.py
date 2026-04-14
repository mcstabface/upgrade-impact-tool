def normalize_version(version: str) -> tuple[int, ...]:
    parts = version.split(".")
    normalized: list[int] = []

    for part in parts:
        try:
            normalized.append(int(part))
        except ValueError:
            normalized.append(0)

    return tuple(normalized)


def version_in_window(
    current_version: str,
    target_version: str,
    version_from: str | None,
    version_to: str | None,
) -> bool:
    current = normalize_version(current_version)
    target = normalize_version(target_version)

    lower_ok = True
    upper_ok = True

    if version_from:
        lower_ok = normalize_version(version_from) <= target

    if version_to:
        upper_ok = normalize_version(version_to) >= current

    return lower_ok and upper_ok