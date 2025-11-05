"""Functionality for querying project dependency trees for license metadata."""

import subprocess
from pathlib import Path

from cargo2rpm import CARGO
from cargo2rpm.metadata import FeatureFlags
from cargo2rpm.utils import CARGO_COMMON_ENV


def license_breakdown(flags: FeatureFlags, package: str | None = None) -> set[str]:
    """Generate list of crate dependencies and their licenses."""
    cmd = [
        CARGO,
        "tree",
        "-Zavoid-dev-deps",
        "--package={package}" if package else "--workspace",
        "--offline",
        "--edges=no-build,no-dev,no-proc-macro",
        "--no-dedupe",
        "--target=all",
        "--prefix=none",
        "--format",
        "{l}: {p}",
    ]
    if flags.all_features:
        cmd.append("--all-features")
    if flags.no_default_features:
        cmd.append("--no-default-features")
    if flags.features:
        cmd.append("--features={}".format(",".join(flags.features)))

    ret = subprocess.run(cmd, env=CARGO_COMMON_ENV, capture_output=True, check=True, text=True)  # noqa: S603

    cwd = str(Path.cwd())
    lines = ret.stdout.strip().splitlines()

    return {line.replace(f" ({cwd})", "").replace(" / ", "/").replace("/", " OR ") for line in lines}


def license_summary(flags: FeatureFlags, package: str | None = None) -> set[str]:
    """Generate summary of all license expressions that occur in the dependency tree.."""
    cmd = [
        CARGO,
        "tree",
        "-Zavoid-dev-deps",
        "--package={package}" if package else "--workspace",
        "--offline",
        "--edges=no-build,no-dev,no-proc-macro",
        "--no-dedupe",
        "--target=all",
        "--prefix=none",
        "--format",
        "# {l}",
    ]
    if flags.all_features:
        cmd.append("--all-features")
    if flags.no_default_features:
        cmd.append("--no-default-features")
    if flags.features:
        cmd.append("--features={}".format(",".join(flags.features)))

    ret = subprocess.run(cmd, env=CARGO_COMMON_ENV, capture_output=True, check=True, text=True)  # noqa: S603

    lines = ret.stdout.strip().splitlines()
    return {line.replace(" / ", "/").replace("/", " OR ") for line in lines}
