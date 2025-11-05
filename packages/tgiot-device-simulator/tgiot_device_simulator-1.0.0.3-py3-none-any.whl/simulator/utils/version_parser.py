"""Version parsing utilities."""

import re
from typing import Optional


def parse_version_string(version_str: str) -> Optional[str]:
    """Parse and normalize version string to semantic version format."""

    # Remove 'v' prefix if present
    clean_version = version_str.strip().lower()
    if clean_version.startswith("v"):
        clean_version = clean_version[1:]

    # Match semantic version pattern (x.x.x)
    pattern = r"(\d+)\.(\d+)\.(\d+)"
    match = re.search(pattern, clean_version)

    if match:
        major, minor, patch = match.groups()
        return f"{major}.{minor}.{patch}"

    # Try to match just major.minor and add .0
    pattern = r"(\d+)\.(\d+)"
    match = re.search(pattern, clean_version)

    if match:
        major, minor = match.groups()
        return f"{major}.{minor}.0"

    return None
