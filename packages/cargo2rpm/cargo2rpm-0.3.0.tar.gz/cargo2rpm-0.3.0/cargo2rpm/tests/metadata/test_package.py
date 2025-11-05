import pytest

from cargo2rpm.metadata import FeatureFlags
from cargo2rpm.utils import load_metadata_from_resource, short_repr


@pytest.mark.parametrize(
    "filename",
    [
        "ahash-0.8.3.json",
        "aho-corasick-1.0.2.json",
        "assert_cmd-2.0.8.json",
        "assert_fs-1.0.10.json",
        "autocfg-1.1.0.json",
        "bstr-1.2.0.json",
        "cfg-if-1.0.0.json",
        "clap-4.1.4.json",
        "espanso-2.1.8.json",
        "fapolicy-analyzer-0.6.8.json",
        "gstreamer-0.19.7.json",
        "human-panic-1.1.0.json",
        "hyperfine-1.15.0.json",
        "iri-string-0.7.0.json",
        "libblkio-1.2.2.json",
        "libc-0.2.139.json",
        "predicates-2.1.5.json",
        "proc-macro2-1.0.50.json",
        "quote-1.0.23.json",
        "rand-0.8.5.json",
        "rand_core-0.6.4.json",
        "regex-1.8.4.json",
        "regex-syntax-0.7.2.json",
        "rpm-sequoia-1.2.0.json",
        "rust_decimal-1.28.0.json",
        "rustix-0.36.8.json",
        "serde-1.0.152.json",
        "serde_derive-1.0.152.json",
        "sha1collisiondetection-0.3.1.json",
        "syn-1.0.107.json",
        "time-0.3.17.json",
        "tokio-1.25.0.json",
        "unicode-xid-0.2.4.json",
        "zbus-3.8.0.json",
        "zola-0.16.1.json",
        "zoxide-0.9.0.json",
    ],
    ids=short_repr,
)
def test_metadata_smoke(filename: str):
    metadata = load_metadata_from_resource(filename)
    packages = metadata.packages
    assert len(packages) >= 1


@pytest.mark.parametrize(
    ("filename", "flags", "expected"),
    [
        # simple cases
        ("ahash-0.8.3.json", None, False),
        ("aho-corasick-1.0.2.json", None, False),
        ("assert_cmd-2.0.8.json", None, True),
        ("assert_fs-1.0.10.json", None, False),
        ("autocfg-1.1.0.json", None, False),
        ("bstr-1.2.0.json", None, False),
        ("cfg-if-1.0.0.json", None, False),
        ("clap-4.1.4.json", None, True),
        ("gstreamer-0.19.7.json", None, False),
        ("human-panic-1.1.0.json", None, False),
        ("hyperfine-1.15.0.json", None, True),
        ("iri-string-0.7.0.json", None, False),
        ("libc-0.2.139.json", None, False),
        ("predicates-2.1.5.json", None, False),
        ("proc-macro2-1.0.50.json", None, False),
        ("quote-1.0.23.json", None, False),
        ("rand-0.8.5.json", None, False),
        ("rand_core-0.6.4.json", None, False),
        ("regex-1.8.4.json", None, False),
        ("regex-syntax-0.7.2.json", None, False),
        ("rpm-sequoia-1.2.0.json", None, False),
        ("rust_decimal-1.28.0.json", None, False),
        ("rustix-0.36.8.json", None, False),
        ("serde-1.0.152.json", None, False),
        ("serde_derive-1.0.152.json", None, False),
        ("syn-1.0.107.json", None, False),
        ("time-0.3.17.json", None, False),
        ("tokio-1.25.0.json", None, False),
        ("unicode-xid-0.2.4.json", None, False),
        ("zbus-3.8.0.json", None, False),
        ("zoxide-0.9.0.json", None, True),
        # more complicated cases
        ("sha1collisiondetection-0.3.1.json", None, False),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(no_default_features=True), False),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(no_default_features=True, features=["std"]), False),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(no_default_features=True, features=["clap"]), False),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(no_default_features=True, features=["clap", "std"]), True),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(features=["clap"]), True),
    ],
    ids=short_repr,
)
def test_metadata_is_bin(filename: str, flags: FeatureFlags, expected: bool):  # noqa: FBT001
    metadata = load_metadata_from_resource(filename)
    assert not metadata.is_workspace(), "Not supported for workspaces!"
    assert metadata.is_bin(flags) == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("ahash-0.8.3.json", True),
        ("aho-corasick-1.0.2.json", True),
        ("assert_cmd-2.0.8.json", True),
        ("assert_fs-1.0.10.json", True),
        ("autocfg-1.1.0.json", True),
        ("bstr-1.2.0.json", True),
        ("cfg-if-1.0.0.json", True),
        ("clap-4.1.4.json", True),
        ("espanso-2.1.8.json", False),
        ("fapolicy-analyzer-0.6.8.json", False),
        ("gstreamer-0.19.7.json", True),
        ("human-panic-1.1.0.json", True),
        ("hyperfine-1.15.0.json", False),
        ("iri-string-0.7.0.json", True),
        ("libblkio-1.2.2.json", False),
        ("libc-0.2.139.json", True),
        ("predicates-2.1.5.json", True),
        ("proc-macro2-1.0.50.json", True),
        ("quote-1.0.23.json", True),
        ("rand-0.8.5.json", True),
        ("rand_core-0.6.4.json", True),
        ("regex-1.8.4.json", True),
        ("regex-syntax-0.7.2.json", True),
        ("rpm-sequoia-1.2.0.json", False),
        ("rust_decimal-1.28.0.json", True),
        ("rustix-0.36.8.json", True),
        ("serde-1.0.152.json", True),
        ("serde_derive-1.0.152.json", True),
        ("sha1collisiondetection-0.3.1.json", True),
        ("syn-1.0.107.json", True),
        ("time-0.3.17.json", True),
        ("tokio-1.25.0.json", True),
        ("unicode-xid-0.2.4.json", True),
        ("zbus-3.8.0.json", True),
        ("zola-0.16.1.json", False),
        ("zoxide-0.9.0.json", False),
    ],
    ids=short_repr,
)
def test_metadata_is_lib(filename: str, expected: bool):  # noqa: FBT001
    metadata = load_metadata_from_resource(filename)
    assert metadata.is_lib() == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("ahash-0.8.3.json", False),
        ("aho-corasick-1.0.2.json", False),
        ("assert_cmd-2.0.8.json", False),
        ("assert_fs-1.0.10.json", False),
        ("autocfg-1.1.0.json", False),
        ("bstr-1.2.0.json", False),
        ("cfg-if-1.0.0.json", False),
        ("clap-4.1.4.json", False),
        ("espanso-2.1.8.json", True),
        ("fapolicy-analyzer-0.6.8.json", True),
        ("gstreamer-0.19.7.json", False),
        ("human-panic-1.1.0.json", False),
        ("hyperfine-1.15.0.json", False),
        ("iri-string-0.7.0.json", False),
        ("libblkio-1.2.2.json", True),
        ("libc-0.2.139.json", False),
        ("predicates-2.1.5.json", False),
        ("proc-macro2-1.0.50.json", False),
        ("quote-1.0.23.json", False),
        ("rand-0.8.5.json", False),
        ("rand_core-0.6.4.json", False),
        ("regex-1.8.4.json", False),
        ("regex-syntax-0.7.2.json", False),
        ("rpm-sequoia-1.2.0.json", False),
        ("rust_decimal-1.28.0.json", False),
        ("rustix-0.36.8.json", False),
        ("serde-1.0.152.json", False),
        ("serde_derive-1.0.152.json", False),
        ("sha1collisiondetection-0.3.1.json", False),
        ("syn-1.0.107.json", False),
        ("time-0.3.17.json", False),
        ("tokio-1.25.0.json", False),
        ("unicode-xid-0.2.4.json", False),
        ("zbus-3.8.0.json", False),
        ("zola-0.16.1.json", True),
        ("zoxide-0.9.0.json", False),
    ],
    ids=short_repr,
)
def test_metadata_is_workspace(filename: str, expected: bool):  # noqa: FBT001
    metadata = load_metadata_from_resource(filename)
    assert metadata.is_workspace() == expected


@pytest.mark.parametrize(
    ("filename", "flags", "expected"),
    [
        # simple cases
        ("ahash-0.8.3.json", None, set()),
        ("aho-corasick-1.0.2.json", None, set()),
        ("assert_cmd-2.0.8.json", None, {"bin_fixture"}),
        ("assert_fs-1.0.10.json", None, set()),
        ("autocfg-1.1.0.json", None, set()),
        ("bstr-1.2.0.json", None, set()),
        ("cfg-if-1.0.0.json", None, set()),
        ("clap-4.1.4.json", None, {"stdio-fixture"}),
        ("gstreamer-0.19.7.json", None, set()),
        ("human-panic-1.1.0.json", None, set()),
        ("hyperfine-1.15.0.json", None, {"hyperfine"}),
        ("iri-string-0.7.0.json", None, set()),
        ("libc-0.2.139.json", None, set()),
        ("predicates-2.1.5.json", None, set()),
        ("proc-macro2-1.0.50.json", None, set()),
        ("quote-1.0.23.json", None, set()),
        ("rand-0.8.5.json", None, set()),
        ("rand_core-0.6.4.json", None, set()),
        ("regex-1.8.4.json", None, set()),
        ("regex-syntax-0.7.2.json", None, set()),
        ("rpm-sequoia-1.2.0.json", None, set()),
        ("rust_decimal-1.28.0.json", None, set()),
        ("rustix-0.36.8.json", None, set()),
        ("serde-1.0.152.json", None, set()),
        ("serde_derive-1.0.152.json", None, set()),
        ("syn-1.0.107.json", None, set()),
        ("time-0.3.17.json", None, set()),
        ("tokio-1.25.0.json", None, set()),
        ("unicode-xid-0.2.4.json", None, set()),
        ("zbus-3.8.0.json", None, set()),
        ("zoxide-0.9.0.json", None, {"zoxide"}),
        # more complicated cases
        ("sha1collisiondetection-0.3.1.json", None, set()),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(no_default_features=True), set()),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(no_default_features=True, features=["std"]), set()),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(no_default_features=True, features=["clap"]), set()),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(no_default_features=True, features=["clap", "std"]), {"sha1cdsum"}),
        ("sha1collisiondetection-0.3.1.json", FeatureFlags(features=["clap"]), {"sha1cdsum"}),
    ],
    ids=short_repr,
)
def test_metadata_get_binaries(filename: str, flags: FeatureFlags, expected: set[str]):
    metadata = load_metadata_from_resource(filename)
    assert not metadata.is_workspace(), "Not supported for workspaces!"
    assert metadata.get_binaries(flags) == expected


@pytest.mark.parametrize(
    ("filename", "feature", "expected"),
    [
        ("ahash-0.8.3.json", None, "crate(ahash) = 0.8.3"),
        ("ahash-0.8.3.json", "default", "crate(ahash/default) = 0.8.3"),
        ("assert_cmd-2.0.8.json", None, "crate(assert_cmd) = 2.0.8"),
        ("assert_cmd-2.0.8.json", "default", "crate(assert_cmd/default) = 2.0.8"),
    ],
    ids=short_repr,
)
def test_package_to_rpm_dependency(filename: str, feature: str | None, expected: str):
    data = load_metadata_from_resource(filename)
    assert data.packages[0].to_rpm_dependency(feature) == expected
