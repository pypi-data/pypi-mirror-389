"""Translation layer between cargo / crate metadata and RPM metadata."""

import os

__version__ = "0.3.0"

# if the "CARGO" environment variable is not defined, fall back to "cargo"
CARGO = _cargo if (_cargo := os.environ.get("CARGO")) else "cargo"
