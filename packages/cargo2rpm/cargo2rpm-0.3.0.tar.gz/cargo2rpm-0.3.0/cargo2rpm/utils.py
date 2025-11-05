"""Common definitions and utility functions for the cargo2rpm test suite."""

import importlib.resources

from cargo2rpm.metadata import Metadata

CARGO_COMMON_ENV = {
    "CARGO_HOME": ".cargo",
    "RUSTC_BOOTSTRAP": "1",
}

SHORT_LIMIT = 22


def load_metadata_from_resource(filename: str) -> Metadata:
    """Load metadata from importlib resource.

    This function loads crate metadata (i.e. the JSON dump from
    `cargo metadata`) as identified by its file name, and parse it into a
    `Metadata` object.
    """
    data = importlib.resources.files("cargo2rpm.testdata").joinpath(filename).read_text()
    return Metadata.from_json(data)


def short_repr(obj: object) -> str:
    """Return truncated / ellipsized object repr.

    Utility function for returning a truncated `repr` of the object that was
    passed as an argument. Used for identifying test cases in parametrized
    `pytest` tests.
    """
    s = repr(obj)
    if len(s) >= SHORT_LIMIT:
        return s[0:SHORT_LIMIT] + ".."
    return s
