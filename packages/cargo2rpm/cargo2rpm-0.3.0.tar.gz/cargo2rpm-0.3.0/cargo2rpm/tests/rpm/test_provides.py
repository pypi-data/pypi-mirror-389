import pytest

from cargo2rpm.rpm import _provides_crate, _provides_feature, provides
from cargo2rpm.utils import load_metadata_from_resource, short_repr


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("ahash-0.8.3.json", "crate(ahash) = 0.8.3"),
        ("assert_cmd-2.0.8.json", "crate(assert_cmd) = 2.0.8"),
        ("assert_fs-1.0.10.json", "crate(assert_fs) = 1.0.10"),
        ("autocfg-1.1.0.json", "crate(autocfg) = 1.1.0"),
        ("bstr-1.2.0.json", "crate(bstr) = 1.2.0"),
        ("cfg-if-1.0.0.json", "crate(cfg-if) = 1.0.0"),
        ("clap-4.1.4.json", "crate(clap) = 4.1.4"),
        ("gstreamer-0.19.7.json", "crate(gstreamer) = 0.19.7"),
        ("human-panic-1.1.0.json", "crate(human-panic) = 1.1.0"),
        ("libc-0.2.139.json", "crate(libc) = 0.2.139"),
        ("predicates-2.1.5.json", "crate(predicates) = 2.1.5"),
        ("proc-macro2-1.0.50.json", "crate(proc-macro2) = 1.0.50"),
        ("quote-1.0.23.json", "crate(quote) = 1.0.23"),
        ("rand-0.8.5.json", "crate(rand) = 0.8.5"),
        ("rand_core-0.6.4.json", "crate(rand_core) = 0.6.4"),
        ("rust_decimal-1.28.0.json", "crate(rust_decimal) = 1.28.0"),
        ("rustix-0.36.8.json", "crate(rustix) = 0.36.8"),
        ("serde-1.0.152.json", "crate(serde) = 1.0.152"),
        ("serde_derive-1.0.152.json", "crate(serde_derive) = 1.0.152"),
        ("sha1collisiondetection-0.3.1.json", "crate(sha1collisiondetection) = 0.3.1"),
        ("syn-1.0.107.json", "crate(syn) = 1.0.107"),
        ("time-0.3.17.json", "crate(time) = 0.3.17"),
        ("tokio-1.25.0.json", "crate(tokio) = 1.25.0"),
        ("unicode-xid-0.2.4.json", "crate(unicode-xid) = 0.2.4"),
        ("zbus-3.8.0.json", "crate(zbus) = 3.8.0"),
    ],
    ids=short_repr,
)
def test_provides_crate(filename: str, expected: str):
    metadata = load_metadata_from_resource(filename)
    assert _provides_crate(metadata.packages[0]) == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("ahash-0.8.3.json", "crate(ahash/default) = 0.8.3"),
        ("assert_cmd-2.0.8.json", "crate(assert_cmd/default) = 2.0.8"),
        ("assert_fs-1.0.10.json", "crate(assert_fs/default) = 1.0.10"),
        ("autocfg-1.1.0.json", "crate(autocfg/default) = 1.1.0"),
        ("bstr-1.2.0.json", "crate(bstr/default) = 1.2.0"),
        ("cfg-if-1.0.0.json", "crate(cfg-if/default) = 1.0.0"),
        ("clap-4.1.4.json", "crate(clap/default) = 4.1.4"),
        ("gstreamer-0.19.7.json", "crate(gstreamer/default) = 0.19.7"),
        ("human-panic-1.1.0.json", "crate(human-panic/default) = 1.1.0"),
        ("libc-0.2.139.json", "crate(libc/default) = 0.2.139"),
        ("predicates-2.1.5.json", "crate(predicates/default) = 2.1.5"),
        ("proc-macro2-1.0.50.json", "crate(proc-macro2/default) = 1.0.50"),
        ("quote-1.0.23.json", "crate(quote/default) = 1.0.23"),
        ("rand-0.8.5.json", "crate(rand/default) = 0.8.5"),
        ("rand_core-0.6.4.json", "crate(rand_core/default) = 0.6.4"),
        ("rust_decimal-1.28.0.json", "crate(rust_decimal/default) = 1.28.0"),
        ("rustix-0.36.8.json", "crate(rustix/default) = 0.36.8"),
        ("serde-1.0.152.json", "crate(serde/default) = 1.0.152"),
        ("serde_derive-1.0.152.json", "crate(serde_derive/default) = 1.0.152"),
        ("sha1collisiondetection-0.3.1.json", "crate(sha1collisiondetection/default) = 0.3.1"),
        ("syn-1.0.107.json", "crate(syn/default) = 1.0.107"),
        ("time-0.3.17.json", "crate(time/default) = 0.3.17"),
        ("tokio-1.25.0.json", "crate(tokio/default) = 1.25.0"),
        ("unicode-xid-0.2.4.json", "crate(unicode-xid/default) = 0.2.4"),
        ("zbus-3.8.0.json", "crate(zbus/default) = 3.8.0"),
    ],
    ids=short_repr,
)
def test_provides_feature(filename: str, expected: str):
    metadata = load_metadata_from_resource(filename)
    assert _provides_feature(metadata.packages[0], "default") == expected


@pytest.mark.parametrize(
    ("filename", "feature", "expected"),
    [
        ("ahash-0.8.3.json", None, "crate(ahash) = 0.8.3"),
        ("assert_cmd-2.0.8.json", None, "crate(assert_cmd) = 2.0.8"),
        ("assert_fs-1.0.10.json", None, "crate(assert_fs) = 1.0.10"),
        ("autocfg-1.1.0.json", None, "crate(autocfg) = 1.1.0"),
        ("bstr-1.2.0.json", None, "crate(bstr) = 1.2.0"),
        ("cfg-if-1.0.0.json", None, "crate(cfg-if) = 1.0.0"),
        ("clap-4.1.4.json", None, "crate(clap) = 4.1.4"),
        ("gstreamer-0.19.7.json", None, "crate(gstreamer) = 0.19.7"),
        ("human-panic-1.1.0.json", None, "crate(human-panic) = 1.1.0"),
        ("libc-0.2.139.json", None, "crate(libc) = 0.2.139"),
        ("predicates-2.1.5.json", None, "crate(predicates) = 2.1.5"),
        ("proc-macro2-1.0.50.json", None, "crate(proc-macro2) = 1.0.50"),
        ("quote-1.0.23.json", None, "crate(quote) = 1.0.23"),
        ("rand-0.8.5.json", None, "crate(rand) = 0.8.5"),
        ("rand_core-0.6.4.json", None, "crate(rand_core) = 0.6.4"),
        ("rust_decimal-1.28.0.json", None, "crate(rust_decimal) = 1.28.0"),
        ("rustix-0.36.8.json", None, "crate(rustix) = 0.36.8"),
        ("serde-1.0.152.json", None, "crate(serde) = 1.0.152"),
        ("serde_derive-1.0.152.json", None, "crate(serde_derive) = 1.0.152"),
        ("sha1collisiondetection-0.3.1.json", None, "crate(sha1collisiondetection) = 0.3.1"),
        ("syn-1.0.107.json", None, "crate(syn) = 1.0.107"),
        ("time-0.3.17.json", None, "crate(time) = 0.3.17"),
        ("tokio-1.25.0.json", None, "crate(tokio) = 1.25.0"),
        ("unicode-xid-0.2.4.json", None, "crate(unicode-xid) = 0.2.4"),
        ("zbus-3.8.0.json", None, "crate(zbus) = 3.8.0"),
        ("ahash-0.8.3.json", "default", "crate(ahash/default) = 0.8.3"),
        ("assert_cmd-2.0.8.json", "default", "crate(assert_cmd/default) = 2.0.8"),
        ("assert_fs-1.0.10.json", "default", "crate(assert_fs/default) = 1.0.10"),
        ("autocfg-1.1.0.json", "default", "crate(autocfg/default) = 1.1.0"),
        ("bstr-1.2.0.json", "default", "crate(bstr/default) = 1.2.0"),
        ("cfg-if-1.0.0.json", "default", "crate(cfg-if/default) = 1.0.0"),
        ("clap-4.1.4.json", "default", "crate(clap/default) = 4.1.4"),
        ("gstreamer-0.19.7.json", "default", "crate(gstreamer/default) = 0.19.7"),
        ("human-panic-1.1.0.json", "default", "crate(human-panic/default) = 1.1.0"),
        ("libc-0.2.139.json", "default", "crate(libc/default) = 0.2.139"),
        ("predicates-2.1.5.json", "default", "crate(predicates/default) = 2.1.5"),
        ("proc-macro2-1.0.50.json", "default", "crate(proc-macro2/default) = 1.0.50"),
        ("quote-1.0.23.json", "default", "crate(quote/default) = 1.0.23"),
        ("rand-0.8.5.json", "default", "crate(rand/default) = 0.8.5"),
        ("rand_core-0.6.4.json", "default", "crate(rand_core/default) = 0.6.4"),
        ("rust_decimal-1.28.0.json", "default", "crate(rust_decimal/default) = 1.28.0"),
        ("rustix-0.36.8.json", "default", "crate(rustix/default) = 0.36.8"),
        ("serde-1.0.152.json", "default", "crate(serde/default) = 1.0.152"),
        ("serde_derive-1.0.152.json", "default", "crate(serde_derive/default) = 1.0.152"),
        ("sha1collisiondetection-0.3.1.json", "default", "crate(sha1collisiondetection/default) = 0.3.1"),
        ("syn-1.0.107.json", "default", "crate(syn/default) = 1.0.107"),
        ("time-0.3.17.json", "default", "crate(time/default) = 0.3.17"),
        ("tokio-1.25.0.json", "default", "crate(tokio/default) = 1.25.0"),
        ("unicode-xid-0.2.4.json", "default", "crate(unicode-xid/default) = 0.2.4"),
        ("zbus-3.8.0.json", "default", "crate(zbus/default) = 3.8.0"),
    ],
    ids=short_repr,
)
def test_provides(filename: str, feature: str | None, expected: str):
    metadata = load_metadata_from_resource(filename)
    assert provides(metadata.packages[0], feature) == expected
