"""Implementation of functionality related to vendored dependencies."""

import re
import subprocess
from pathlib import Path

from cargo2rpm import CARGO
from cargo2rpm.semver import Version
from cargo2rpm.utils import CARGO_COMMON_ENV

# this is a regex for lines of the format
# <name> v<version> OR
# <name> v<version> (<url>#<ref>)
MANIFEST_LINE_REGEX_STR = r"""
^
(?P<name>[a-zA-Z][a-zA-Z0-9-_]*)
[ ]
v(?P<version>
    (?P<major>0|[1-9]\d*)
    \.(?P<minor>0|[1-9]\d*)
    \.(?P<patch>0|[1-9]\d*)
    (?:-(?P<pre>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?
    (?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?
)
(?P<path>
    [ ]
    \(
    .+
    \#
    (?P<ref>[0-9a-f]+)
    \)
)?
$
"""

MANIFEST_LINE_REGEX = re.compile(MANIFEST_LINE_REGEX_STR, re.VERBOSE)


def _parse_vendor_manifest_line(line: str) -> tuple[str, str] | None:
    matches = MANIFEST_LINE_REGEX.match(line)
    if matches is None:
        return None

    groups = matches.groupdict()
    name: str = groups["name"]
    version: str = groups["version"]
    gitref: str | None = groups.get("ref", None)

    rpmversion = Version.parse(version).to_rpm()

    if gitref is not None:
        return name, f"{rpmversion}+git{gitref}"

    return name, rpmversion


def parse_vendor_manifest(contents: str) -> str:
    """Parse contents of the vendor manifest."""
    out = []

    for line in contents.strip().splitlines():
        nv = _parse_vendor_manifest_line(line)
        if nv is None:
            msg = f"Cannot parse line in vendor manifest: {line!r}"
            raise ValueError(msg)
        crate, version = nv
        out.append(f"bundled(crate({crate})) = {version}")

    return "\n".join(out)


def vendor_manifest() -> set[str]:
    """Generate and write contents of the vendor manifest."""
    pwd = str(Path.cwd())

    cmd = [
        CARGO,
        "tree",
        "--workspace",
        "--offline",
        "--edges=normal,build,dev",
        "--no-dedupe",
        "--target=all",
        "--all-features",
        "--prefix=none",
        "--format",
        "{p}",
    ]

    ret = subprocess.run(cmd, env=CARGO_COMMON_ENV, capture_output=True, check=False)  # noqa: S603
    ret.check_returncode()

    lines = ret.stdout.decode().strip().splitlines()

    return {line.replace(" (proc-macro)", "") for line in lines if pwd not in line}
