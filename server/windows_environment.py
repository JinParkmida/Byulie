"""Windows 11 64-bit runtime validation for Byulie entry points."""

import os
import platform
import sys

SKIP_WINDOWS_CHECK_ENV = "BYULIE_SKIP_WINDOWS_CHECK"
WINDOWS_11_MIN_BUILD = 22000


def _windows_build_number():
    """Return the Windows build number when it can be parsed."""
    version_parts = platform.version().split(".")
    if len(version_parts) >= 3 and version_parts[2].isdigit():
        return int(version_parts[2])
    return 0


def ensure_windows_11_64bit():
    """Raise a clear error unless Byulie is running on Windows 11 with 64-bit Python."""
    if os.environ.get(SKIP_WINDOWS_CHECK_ENV) == "1":
        return

    if platform.system() != "Windows":
        raise RuntimeError(
            "Byulie is configured for Windows 11 64-bit. "
            f"Detected {platform.system() or 'an unknown operating system'}."
        )

    if sys.maxsize <= 2**32:
        raise RuntimeError(
            "Byulie requires 64-bit Python on Windows 11. "
            "Install 64-bit Python 3.10 or 3.11 and recreate .venv."
        )

    build_number = _windows_build_number()
    if build_number and build_number < WINDOWS_11_MIN_BUILD:
        raise RuntimeError(
            "Byulie requires Windows 11 64-bit. "
            f"Detected Windows build {build_number}; Windows 11 starts at build {WINDOWS_11_MIN_BUILD}."
        )
