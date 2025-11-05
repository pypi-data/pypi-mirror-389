import importlib.resources

import pytest

from cargo2rpm.utils import short_repr
from cargo2rpm.vendor import _parse_vendor_manifest_line, parse_vendor_manifest


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("winnow v0.7.13", ("winnow", "0.7.13")),
        ("blazesym v0.2.0-rc.0", ("blazesym", "0.2.0~rc.0")),
        ("smithay v0.7.0 (https://github.com/Smithay/smithay.git#20d2dacd)", ("smithay", "0.7.0+git20d2dacd")),
        ("hell owo rld", None),
    ],
    ids=short_repr,
)
def test_parse_line(line: str, expected: str | None):
    assert _parse_vendor_manifest_line(line) == expected


@pytest.mark.parametrize(
    ("manifest_path", "expected_path"),
    [
        ("niri-25.08-cargo-vendor.txt", "niri-25.08-cargo-vendor.rpm.txt"),
    ],
    ids=short_repr,
)
def test_parse_manifest(manifest_path: str, expected_path: str):
    manifest = importlib.resources.files("cargo2rpm.testdata").joinpath(manifest_path).read_text()
    expected = importlib.resources.files("cargo2rpm.testdata").joinpath(expected_path).read_text()
    assert parse_vendor_manifest(manifest) == expected
