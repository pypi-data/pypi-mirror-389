"""Partial Python port of the "semver" crate (<https://docs.rs/semver>)."""

import itertools
import re
from dataclasses import dataclass
from enum import Enum

MAX_COMPARATORS = 2

VERSION_REGEX = re.compile(
    r"""
    ^
    (?P<major>0|[1-9]\d*)
    \.(?P<minor>0|[1-9]\d*)
    \.(?P<patch>0|[1-9]\d*)
    (?:-(?P<pre>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?
    (?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$
    """,
    re.VERBOSE,
)


VERSION_REQ_REGEX = re.compile(
    r"""
    ^
    (?P<op>=|>|>=|<|<=|~|\^)?
    (?P<major>0|[1-9]\d*)
    (\.(?P<minor>\*|0|[1-9]\d*))?
    (\.(?P<patch>\*|0|[1-9]\d*))?
    (-(?P<pre>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?
    $
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class PreRelease:
    """Pre-release part of a Version."""

    parts: list[str | int]

    @staticmethod
    def parse(prerelease: str) -> "PreRelease":
        """Parse PreRelease from string."""
        parts: list[str | int] = [int(part) if part.isdecimal() else part for part in prerelease.split(".")]

        return PreRelease(parts)

    def __str__(self) -> str:
        return ".".join([str(part) for part in self.parts])

    def __repr__(self) -> str:
        return repr(str(self))

    def __hash__(self) -> int:
        return hash(self.parts)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PreRelease):
            return False  # pragma nocover

        return self.parts == other.parts

    def __lt__(self, other: object) -> bool:  # noqa: C901,PLR0911,PLR0912
        """Determine precedence between pre-releases.

        The algorithm for determining order is based on the semver.org spec.
        """
        if not isinstance(other, PreRelease):
            return NotImplemented  # pragma nocover

        for lpart, rpart in itertools.zip_longest(self.parts, other.parts):
            match lpart, rpart:
                # all previous parts were equal and the left pre-release has more parts
                case l, None:
                    return False

                # all previous parts were equal and the right pre-release has more parts
                case None, r:
                    return True

                # compare nonempty parts depending on value type
                case l, r:
                    match isinstance(l, int), isinstance(r, int):
                        # both parts are numbers: compare numerically
                        case True, True:
                            if l < r:  # type: ignore[operator]
                                return True
                            if l == r:
                                continue
                            return False

                        # both parts are strings: compare lexicographically
                        case False, False:
                            if l < r:  # type: ignore[operator]
                                return True
                            if l == r:
                                continue
                            return False

                        # number and string: string takes precedence
                        case True, False:
                            return True

                        # string and number: string takes precedence
                        case False, True:
                            return False

                        case _:  # pragma nocover
                            msg = "Unreachable: This should never happen."
                            raise RuntimeError(msg)

                case _:  # pragma nocover
                    msg = "Unreachable: This should never happen."
                    raise RuntimeError(msg)

        # both pre-releases have equal numbers of parts and all pairs of parts are equal
        return False

    def __le__(self, other: object) -> bool:
        if not isinstance(other, PreRelease):
            return NotImplemented  # pragma nocover

        return (self == other) or (self < other)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, PreRelease):
            return NotImplemented  # pragma nocover

        return other < self

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, PreRelease):
            return NotImplemented  # pragma nocover

        return (self == other) or (self > other)


@dataclass(frozen=True)
class Version:
    """Version that adheres to the "semantic versioning" format."""

    major: int
    minor: int
    patch: int
    pre: str | None = None
    build: str | None = None

    @staticmethod
    def parse(version: str) -> "Version":
        """Parse a version string and return a `Version` object.

        Raises a `ValueError` if the string does not match the expected format.
        """
        match = VERSION_REGEX.match(version)
        if not match:
            msg = f"Invalid version: {version!r}"
            raise ValueError(msg)

        matches = match.groupdict()

        major_str = matches["major"]
        minor_str = matches["minor"]
        patch_str = matches["patch"]
        pre = matches["pre"]
        build = matches["build"]

        major = int(major_str)
        minor = int(minor_str)
        patch = int(patch_str)

        return Version(major, minor, patch, pre, build)

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            s += f"-{self.pre}"
        if self.build:
            s += f"+{self.build}"
        return s

    def __repr__(self) -> str:
        return repr(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False  # pragma nocover

        return (self.major == other.major) and (self.minor == other.minor) and (self.patch == other.patch) and (self.pre == other.pre)

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.pre, self.build))

    def __lt__(self, other: object) -> bool:  # noqa: C901,PLR0911
        """Determine precedence between versions.

        The algorithm for determining order between versions is based on the semver.org spec.
        """
        if not isinstance(other, Version):
            return NotImplemented  # pragma nocover

        if self.major < other.major:
            return True
        if self.major > other.major:
            return False

        # major versions match
        if self.minor < other.minor:
            return True
        if self.minor > other.minor:
            return False

        # minor versions match
        if self.patch < other.patch:
            return True
        if self.patch > other.patch:
            return False

        # patch versions match
        match self.pre, other.pre:
            case None, None:
                return False
            case spre, None:
                return True
            case None, opre:
                return False
            case spre, opre:
                return PreRelease.parse(spre) < PreRelease.parse(opre)
            case _:  # pragma nocover
                msg = "Unreachable: This should never happen."
                raise RuntimeError(msg)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented  # pragma nocover

        return (self == other) or (self < other)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented  # pragma nocover

        return other < self

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented  # pragma nocover

        return (self == other) or (self > other)

    def to_rpm(self) -> str:
        """Format the `Version` object as an equivalent RPM version string.

        Characters that are invalid in RPM versions are replaced ("-" -> "_")

        Build metadata (the optional `Version.build` attribute) is dropped, so
        the conversion is not lossless for versions where this attribute is not
        `None`. However, build metadata is not intended to be part of the
        version (and is not even considered when doing version comparison), so
        dropping it when converting to the RPM version format is correct.
        """
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            s += f"~{self.pre.replace('-', '_')}"
        return s

    @staticmethod
    def from_rpm(version: str) -> "Version":
        """Parse an RPM version string and return the equivalent `Version`.

        Characters that are invalid in SemVer format are replaced ("_" -> "-").

        This method performs the inverse of `Version.to_rpm`.
        """
        return Version.parse(version.replace("~", "-").replace("_", "-"))


class Op(Enum):
    """Version requirement operator.

    This class enumerates all operators that are considered valid for specifying
    the required version of a dependency in cargo.
    """

    EXACT = "="
    GREATER = ">"
    GREATER_EQ = ">="
    LESS = "<"
    LESS_EQ = "<="
    TILDE = "~"
    CARET = "^"
    WILDCARD = "*"

    def __repr__(self) -> str:
        return self.value  # pragma nocover


@dataclass(frozen=True)
class Comparator:
    """Partial version requirement.

    A `Comparator` consists of an operator (`Op`) and a (partial) semantic
    version and is used to define a requirement that a version can be matched
    against.
    """

    op: Op
    major: int
    minor: int | None
    patch: int | None
    pre: str | None

    def __str__(self) -> str:
        if self.op == Op.WILDCARD:
            if self.minor is not None:
                return f"{self.major}.{self.minor}.*"
            return f"{self.major}.*"

        op = self.op.value
        if self.pre is not None:
            return f"{op}{self.major}.{self.minor}.{self.patch}-{self.pre}"
        if self.patch is not None:
            return f"{op}{self.major}.{self.minor}.{self.patch}"
        if self.minor is not None:
            return f"{op}{self.major}.{self.minor}"
        return f"{op}{self.major}"

    def __repr__(self) -> str:
        return repr(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Comparator):
            return NotImplemented  # pragma nocover

        # naive equality check: does not take equivalence into account
        return (
            self.op == other.op
            and self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.pre == other.pre
        )

    def __hash__(self) -> int:
        return hash((self.op, self.major, self.minor, self.patch, self.pre))

    def __contains__(self, item: object) -> bool:  # noqa: PLR0911
        if not isinstance(item, Version):
            return False  # pragma nocover

        match self.op:
            case Op.EXACT:
                return item == self._as_version()
            case Op.GREATER:
                return item > self._as_version()
            case Op.GREATER_EQ:
                return item >= self._as_version()
            case Op.LESS:
                return item < self._as_version()
            case Op.LESS_EQ:
                return item <= self._as_version()
            case Op.TILDE:
                return item in VersionReq(self.normalize())
            case Op.CARET:
                return item in VersionReq(self.normalize())
            case Op.WILDCARD:
                return item in VersionReq(self.normalize())
            case _:  # pragma nocover
                msg = f"Unknown operator: {self.op} (this should never happen)"
                raise ValueError(msg)

    def _as_version(self) -> Version:
        return Version(self.major, self.minor or 0, self.patch or 0, self.pre)

    @staticmethod
    def parse(comparator: str) -> "Comparator":
        """Parse a single version requirement string.

        This function returns a a `Comparator` and raises a `ValueError` if the
        string does not match the expected format.
        """
        match = VERSION_REQ_REGEX.match(comparator)
        if not match:
            msg = f"Invalid version requirement: {comparator!r}"
            raise ValueError(msg)

        matches = match.groupdict()

        op_str = matches["op"]
        major_str = matches["major"]
        minor_str = matches["minor"]
        patch_str = matches["patch"]
        pre = matches["pre"]

        # if patch is present, minor needs to be present as well
        if minor_str is None and patch_str is not None:
            msg = f"Invalid version requirement: {comparator!r}"
            raise ValueError(msg)  # pragma nocover

        # if patch is not wildcard, then minor cannot be wildcard
        if minor_str is not None and patch_str is not None and minor_str == "*" and patch_str != "*":
            msg = f"Invalid wildcard requirement: {comparator!r}."
            raise ValueError(msg)

        # if pre-release is specified, then minor and patch must be present
        if pre and (minor_str is None or patch_str is None):
            msg = f"Invalid pre-release requirement (minor / patch version missing): {comparator!r}"
            raise ValueError(msg)

        # normalize wildcard specifiers
        if minor_str is not None and minor_str == "*":
            op_str = "*"
            minor_str = None
        if patch_str is not None and patch_str == "*":
            op_str = "*"
            patch_str = None

        # fall back to default CARET ("^") operator if not specified
        op = Op(op_str) if op_str is not None else Op.CARET
        major = int(major_str)
        minor = int(minor_str) if minor_str is not None else None
        patch = int(patch_str) if patch_str is not None else None

        return Comparator(op, major, minor, patch, pre)

    def normalize(self) -> list["Comparator"]:  # noqa: C901,PLR0912,PLR0915
        """Normalize / simplify this comparator.

        This returns a list of equivalent comparators which only use the ">=",
        ">", "<", "<=", and "=" operators.

        This is based on the documentation of the semver crate, which is used
        by cargo: <https://docs.rs/semver/1.0.16/semver/enum.Op.html>

        This normalized version requirement can be formatted as a valid RPM
        dependency string. Other operators (i.e. "^", "~", and "*") are not
        supported by RPM.
        """
        comparators = []

        match self.op:
            case Op.EXACT:
                match (self.minor, self.patch):
                    case (None, None):
                        comparators.append(Comparator(Op.GREATER_EQ, self.major, 0, 0, None))
                        comparators.append(Comparator(Op.LESS, self.major + 1, 0, 0, None))
                    case (minor, None):
                        comparators.append(Comparator(Op.GREATER_EQ, self.major, minor, 0, None))
                        comparators.append(Comparator(Op.LESS, self.major, minor + 1, 0, None))  # type: ignore[operator]
                    case (minor, patch):
                        comparators.append(Comparator(Op.EXACT, self.major, minor, patch, self.pre))
                    case _:  # pragma nocover
                        msg = "Unreachable: This should never happen."
                        raise RuntimeError(msg)

            case Op.GREATER:
                match (self.minor, self.patch):
                    case (None, None):
                        comparators.append(Comparator(Op.GREATER_EQ, self.major + 1, 0, 0, None))
                    case (minor, None):
                        comparators.append(Comparator(Op.GREATER_EQ, self.major, minor + 1, 0, None))  # type: ignore[operator]
                    case (minor, patch):
                        comparators.append(Comparator(Op.GREATER, self.major, minor, patch, self.pre))
                    case _:  # pragma nocover
                        msg = "Unreachable: This should never happen."
                        raise RuntimeError(msg)

            case Op.GREATER_EQ:
                match (self.minor, self.patch):
                    case (None, None):
                        comparators.append(Comparator(Op.GREATER_EQ, self.major, 0, 0, None))
                    case (minor, None):
                        comparators.append(Comparator(Op.GREATER_EQ, self.major, minor, 0, None))
                    case (minor, patch):
                        comparators.append(Comparator(Op.GREATER_EQ, self.major, minor, patch, self.pre))
                    case _:  # pragma nocover
                        msg = "Unreachable: This should never happen."
                        raise RuntimeError(msg)

            case Op.LESS:
                match (self.minor, self.patch):
                    case (None, None):
                        comparators.append(Comparator(Op.LESS, self.major, 0, 0, None))
                    case (minor, None):
                        comparators.append(Comparator(Op.LESS, self.major, minor, 0, None))
                    case (minor, patch):
                        comparators.append(Comparator(Op.LESS, self.major, minor, patch, self.pre))
                    case _:  # pragma nocover
                        msg = "Unreachable: This should never happen."
                        raise RuntimeError(msg)

            case Op.LESS_EQ:
                match (self.minor, self.patch):
                    case (None, None):
                        comparators.append(Comparator(Op.LESS, self.major + 1, 0, 0, None))
                    case (minor, None):
                        comparators.append(Comparator(Op.LESS, self.major, minor + 1, 0, None))  # type: ignore[operator]
                    case (minor, patch):
                        comparators.append(Comparator(Op.LESS_EQ, self.major, minor, patch, self.pre))
                    case _:  # pragma nocover
                        msg = "Unreachable: This should never happen."
                        raise RuntimeError(msg)

            case Op.TILDE:
                match (self.minor, self.patch):
                    case (None, None):
                        comparators.extend(Comparator(Op.EXACT, self.major, None, None, None).normalize())
                    case (minor, None):
                        comparators.extend(Comparator(Op.EXACT, self.major, minor, None, None).normalize())
                    case (minor, patch):
                        comparators.append(Comparator(Op.GREATER_EQ, self.major, minor, patch, self.pre))
                        comparators.append(Comparator(Op.LESS, self.major, minor + 1, 0, None))  # type: ignore[operator]
                    case _:  # pragma nocover
                        msg = "Unreachable: This should never happen."
                        raise RuntimeError(msg)

            case Op.CARET:
                match (self.major, self.minor, self.patch):
                    case (major, None, None):
                        comparators.extend(Comparator(Op.EXACT, major, None, None, None).normalize())
                    case (0, 0, None):
                        comparators.extend(Comparator(Op.EXACT, 0, 0, None, None).normalize())
                    case (major, minor, None):
                        comparators.extend(Comparator(Op.CARET, major, minor, 0, None).normalize())
                    case (0, 0, patch):
                        comparators.extend(Comparator(Op.EXACT, 0, 0, patch, self.pre).normalize())
                    case (0, minor, patch):
                        comparators.append(Comparator(Op.GREATER_EQ, 0, minor, patch, self.pre))
                        comparators.append(Comparator(Op.LESS, 0, minor + 1, 0, None))  # type: ignore[operator]
                    case (major, minor, patch):
                        comparators.append(Comparator(Op.GREATER_EQ, major, minor, patch, self.pre))
                        comparators.append(Comparator(Op.LESS, major + 1, 0, 0, None))
                    case _:  # pragma nocover
                        msg = "Unreachable: This should never happen."
                        raise RuntimeError(msg)

            case Op.WILDCARD:
                match (self.minor, self.patch):
                    case (None, None):
                        comparators.extend(Comparator(Op.EXACT, self.major, None, None, None).normalize())
                    case (minor, None):
                        comparators.extend(Comparator(Op.EXACT, self.major, minor, None, None).normalize())
                    case _:  # pragma nocover
                        msg = "Unreachable: This should never happen."
                        raise RuntimeError(msg)

            case _:  # pragma nocover
                msg = f"Unknown operator: {self.op} (this should never happen)"
                raise ValueError(msg)

        return comparators

    def to_rpm(self, crate: str, feature: str | None) -> str:
        """Format the `Comparator` object as an equivalent RPM dependency.

        Raises a `ValueError` if the comparator cannot be converted into a valid
        RPM dependency (for example, if it was not normalized or uses an
        unsupported operator).
        """
        if self.normalize() != [self]:  # pragma nocover
            msg = "Cannot format non-normalized comparators in RPM syntax."
            raise ValueError(msg)

        feature_str = "" if feature is None else f"/{feature}"
        version_str = f"{self.major}.{self.minor}.{self.patch}"

        if self.pre is None:
            pre_str = ""
            pre_str_less = "~"
        else:
            pre = self.pre.replace("-", "_")
            pre_str = f"~{pre}"
            pre_str_less = f"~{pre}"

        match self.op:
            case Op.EXACT:
                return f"crate({crate}{feature_str}) = {version_str}{pre_str}"
            case Op.GREATER:
                return f"crate({crate}{feature_str}) > {version_str}{pre_str}"
            case Op.GREATER_EQ:
                return f"crate({crate}{feature_str}) >= {version_str}{pre_str}"
            case Op.LESS:
                return f"crate({crate}{feature_str}) < {version_str}{pre_str_less}"
            case Op.LESS_EQ:
                return f"crate({crate}{feature_str}) <= {version_str}{pre_str}"
            case _:  # pragma nocover
                msg = f"Unsupported operator for RPM syntax formatting: {self.op}"
                raise ValueError(msg)


@dataclass(frozen=True)
class VersionReq:
    """Version requirement.

    A `VersionReq` consists of a - possibly empty -list of a `Comparators`.

    An empty list represents the "no requirements" case (i.e. any version
    matches this requirement).

    For a version to match a version requirement with a non-empty list of
    comparators, it must match with all comparators in the list.
    """

    comparators: list[Comparator]

    def __str__(self) -> str:
        if not self.comparators:
            return "*"

        return ",".join(str(comparator) for comparator in self.comparators)

    def __repr__(self) -> str:
        return repr(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionReq):
            return NotImplemented  # pragma nocover

        return self.comparators == other.comparators

    def __hash__(self) -> int:
        return hash(self.comparators)

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, Version):
            return False  # pragma nocover

        normalized = self.normalize().comparators
        return all(item in comparator for comparator in normalized)

    @staticmethod
    def parse(req: str) -> "VersionReq":
        """Parse a version requirement string and return a `VersionReq`.

        Raises a `ValueError` if the string does not match the expected format.
        """
        if not req:
            msg = "Invalid version requirement (empty string)."
            raise ValueError(msg)

        if req == "*":
            return VersionReq([])

        reqs = req.replace(" ", "").split(",")
        comparators = [Comparator.parse(req) for req in reqs]

        return VersionReq(comparators)

    def normalize(self) -> "VersionReq":
        """Normalize / simplify this version requirement.

        This returns an equivalent requirement with comparators that only
        use ">=", ">", "<", "<=", and "=" operators. Other operators (i.e.
        "^", "~", and "*") are not supported by RPM.
        """
        comparators = []
        for comparator in self.comparators:
            comparators.extend(comparator.normalize())

        return VersionReq(comparators)

    def to_rpm(self, crate: str, feature: str | None) -> str:
        """Format the `VersionReq` object as an equivalent RPM dependency string.

        Raises a `ValueError` if the requirement cannot be converted into a
        valid RPM dependency - for example, if normalizing the comparators in
        this requirement results in a list of comparators with three or more
        items, which cannot easily be represented as RPM dependencies.
        """
        comparators = self.normalize().comparators

        if len(comparators) == 0:
            feature_str = "" if feature is None else f"/{feature}"
            return f"crate({crate}{feature_str})"

        if len(comparators) == 1:
            return comparators[0].to_rpm(crate, feature)

        if len(comparators) == MAX_COMPARATORS:
            return f"({comparators[0].to_rpm(crate, feature)} with {comparators[1].to_rpm(crate, feature)})"

        # len(comparators) > 2:
        msg = "Using more than 2 comparators is not supported by RPM."
        raise ValueError(msg)
