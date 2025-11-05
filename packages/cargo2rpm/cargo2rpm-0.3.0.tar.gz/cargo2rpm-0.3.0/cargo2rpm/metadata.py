"""Functionality for reading cargo / crate metadata."""

import json
import re
import subprocess
import sys
import textwrap
from collections import defaultdict
from dataclasses import dataclass

from cargo2rpm import CARGO
from cargo2rpm.semver import Comparator, Op, Version, VersionReq

DESCRIPTION_MAX_WIDTH = 72


class FeatureFlags:
    """Collection of flags that affect feature and dependency resolution.

    This includes "--all-features", "--no-default-features", and
    "--features foo,bar".
    """

    def __init__(self, *, all_features: bool = False, no_default_features: bool = False, features: list[str] | None = None):
        """Initialize new FeatureFlags from flags.

        Raises a "ValueError" for arguments that are incompatible with each other.

        Passing no arguments is equivalent to passing no command-line flags to
        cargo, i.e. the "default" feature is enabled.
        """
        if features is None:
            features = []

        if all_features and features:
            msg = "Cannot specify both '--all-features' and '--features'."
            raise ValueError(msg)

        if all_features and no_default_features:
            msg = "Cannot specify both '--all-features' and '--no-default-features'."
            raise ValueError(msg)

        self.all_features = all_features
        self.no_default_features = no_default_features
        self.features = features

    def __repr__(self) -> str:
        parts = []

        if self.all_features:
            parts.append("all_features")
        if self.no_default_features:
            parts.append("no_default_features")
        if self.features:
            parts.append(f"features=[{', '.join(self.features)}]")

        if parts:
            string = ", ".join(parts)
            return f"[{string}]"
        return "[]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FeatureFlags):
            return False  # pragma nocover

        return (
            self.all_features == other.all_features
            and self.no_default_features == other.no_default_features
            and set(self.features) == set(other.features)
        )

    def __hash__(self) -> int:
        return hash((self.all_features, self.no_default_features, self.features))


@dataclass(frozen=True)
class Dependency:
    """Metadata for a single compilation target."""

    _data: dict

    def __repr__(self) -> str:
        return repr(self._data)

    @property
    def name(self) -> str:  # noqa: D102
        return self._data["name"]

    @property
    def req(self) -> str:  # noqa: D102
        return self._data["req"]

    @property
    def kind(self) -> str | None:  # noqa: D102
        return self._data["kind"]

    @property
    def rename(self) -> str | None:  # noqa: D102
        return self._data["rename"]

    @property
    def optional(self) -> bool:  # noqa: D102
        return self._data["optional"]

    @property
    def uses_default_features(self) -> bool:  # noqa: D102
        return self._data["uses_default_features"]

    @property
    def features(self) -> list[str]:  # noqa: D102
        return self._data["features"]

    @property
    def target(self) -> str | None:  # noqa: D102
        return self._data["target"]

    @property
    def path(self) -> str | None:  # noqa: D102
        return self._data.get("path")

    @property
    def source(self) -> str | None:  # noqa: D102
        return self._data.get("source")

    def is_path_or_git(self) -> bool:
        """Check whether this is a normal, path-based, or git-based dependency."""
        if self.path:
            return True
        return self.source is not None and self.source.startswith("git+")

    def to_rpm(self, feature: str | None) -> str:
        """Format this crate dependency as an RPM dependency string."""
        if self.path is not None:
            msg = "Cannot generate an RPM dependency for a path dependency."
            raise ValueError(msg)

        req = VersionReq.parse(self.req)
        return req.to_rpm(self.name, feature)


@dataclass(frozen=True)
class Target:
    """Metadata for a single compilation target."""

    _data: dict

    def __repr__(self) -> str:
        return repr(self._data)

    @property
    def name(self) -> str:  # noqa: D102
        return self._data["name"]

    @property
    def kind(self) -> list[str]:  # noqa: D102
        return self._data["kind"]

    @property
    def crate_types(self) -> list[str]:  # noqa: D102
        return self._data["crate_types"]

    @property
    def required_features(self) -> list[str]:  # noqa: D102
        return self._data.get("required-features", None) or []


@dataclass(frozen=True)
class Package:
    """Metadata for a crate or single workspace member."""

    _data: dict

    def __repr__(self) -> str:
        return repr(self._data)

    @property
    def name(self) -> str:  # noqa: D102
        return self._data["name"]

    @property
    def version(self) -> str:  # noqa: D102
        return self._data["version"]

    @property
    def license(self) -> str | None:  # noqa: D102
        return self._data["license"]

    @property
    def license_file(self) -> str | None:  # noqa: D102
        return self._data["license_file"]

    @property
    def description(self) -> str | None:  # noqa: D102
        return self._data["description"]

    @property
    def dependencies(self) -> list[Dependency]:  # noqa: D102
        return [Dependency(dependency) for dependency in self._data["dependencies"]]

    @property
    def targets(self) -> list[Target]:  # noqa: D102
        return [Target(target) for target in self._data["targets"]]

    @property
    def features(self) -> dict[str, list[str]]:  # noqa: D102
        return self._data["features"]

    @property
    def manifest_path(self) -> str:  # noqa: D102
        return self._data["manifest_path"]

    @property
    def rust_version(self) -> str | None:  # noqa: D102
        return self._data["rust_version"]

    @property
    def edition(self) -> str:  # noqa: D102
        return self._data["edition"]

    @property
    def homepage(self) -> str | None:  # noqa: D102
        return self._data["homepage"]

    @property
    def repository(self) -> str | None:  # noqa: D102
        return self._data["repository"]

    def get_feature_names(self) -> set[str]:
        """Return list of all crate features."""
        return set(self.features.keys())

    def get_normal_dependencies(self, *, optional: bool) -> dict[str, Dependency]:
        """Generate mapping between renamed names and actual names of dependencies."""
        normal = filter(lambda d: d.kind is None and d.optional == optional, self.dependencies)
        return {d.rename if d.rename else d.name: d for d in normal}

    def get_build_dependencies(self, *, optional: bool) -> dict[str, Dependency]:
        """Generate mapping between renamed names and actual names of build-dependencies."""
        build = filter(lambda d: d.kind == "build" and d.optional == optional, self.dependencies)
        return {d.rename if d.rename else d.name: d for d in build}

    def get_dev_dependencies(self) -> dict[str, Dependency]:
        """Generate mapping between renamed names and actual names of dev-dependencies."""
        dev = filter(lambda d: d.kind == "dev", self.dependencies)
        return {d.rename if d.rename else d.name: d for d in dev}

    def to_rpm_dependency(self, feature: str | None) -> str:
        """Return an RPM dependency string that represents a dependency on this crate.

        The returned string includes an exact requirement on the crate version.
        """
        ver = Version.parse(self.version)
        req = VersionReq([Comparator(Op.EXACT, ver.major, ver.minor, ver.patch, ver.pre)])
        return req.to_rpm(self.name, feature)

    def get_description(self) -> str | None:
        """Return a reformatted version of the package description with lines wrapped to 72 characters."""
        if self.description is None:
            return None

        # reformat contents so paragraphs become lines
        paragraphs = self.description.replace("\n\n", "\r").replace("\n", " ").replace("\r", "\n").strip()

        # ensure description starts with a capital letter
        if not paragraphs[0].isupper():
            paragraphs = paragraphs[0].upper() + paragraphs[1:]

        # ensure description ends with a full stop
        if not paragraphs.endswith("."):
            paragraphs += "."

        # return contents wrapped to 72 columns
        return "\n".join(textwrap.wrap(paragraphs, 72))

    def get_summary(self) -> str | None:
        """Return a shortened version of the package description based on a few heuristics."""
        if not self.description:
            return None

        # replace markdown markup (i.e. code fences)
        description = self.description.replace("`", "")

        # replace common phrases like "this is a" or "this {crate} provides an"
        stripped = re.sub(
            r"^((a|an|this)\s+)?(crate\s+)?((is|provides)\s+)?((a|an|the)\s+)?",
            "",
            description,
            flags=re.IGNORECASE,
        )

        # if stripped description still contains multiple lines, merge them
        stripped = re.sub(r"(\n+)", " ", stripped).strip()

        # ensure summary starts with a capital letter
        if not stripped[0].isupper():
            stripped = stripped[0].upper() + stripped[1:]

        # if length is already short enough, reformat as one line and return
        if len(stripped) <= DESCRIPTION_MAX_WIDTH:
            return stripped.removesuffix(".")

        # use some heuristics to determine phrase boundaries
        if (brace := stripped.find(" (")) != -1:
            return stripped[0:brace].removesuffix(".")
        if (period := stripped.find(". ")) != -1:
            return stripped[0:period].removesuffix(".")
        if (semicolon := stripped.find("; ")) != -1:
            return stripped[0:semicolon].removesuffix(".")

        # none of the heuristics matched:
        # fall back to returning the stripped description even if it's too long
        return stripped.removesuffix(".")

    def is_bin(self, flags: FeatureFlags) -> bool:
        """Check whether there are any "bin" targets in this package.

        Returns "True" if the package has a "bin" target and the required features
        for at least one "bin" target are enabled.
        """
        return len(self.get_binaries(flags or FeatureFlags())) > 0

    def is_lib(self) -> bool:
        """Check whether there is a "lib" or "proc-macro" target.

        Returns "True" if and only if the crate has a "lib" or "proc-macro" target.
        """
        for target in self.targets:
            if "lib" in target.kind and "lib" in target.crate_types:
                return True
            if "rlib" in target.kind and "rlib" in target.crate_types:
                return True
            if "proc-macro" in target.kind and "proc-macro" in target.crate_types:
                return True
        return False

    def is_cdylib(self, flags: FeatureFlags) -> bool:
        """Check whether there are any "cdylib" (C shared library") targets in this package.

        Returns "True" if the package has a "cdylib" target and the required
        features for at least one "cdylib" target are enabled.
        """
        enabled, _, _, _ = self.get_enabled_features_transitive(flags or FeatureFlags())

        for target in self.targets:
            if (
                "cdylib" in target.kind
                and "cdylib" in target.crate_types
                and all(feature in enabled for feature in target.required_features)
            ):
                return True
        return False

    def get_binaries(self, flags: FeatureFlags) -> set[str]:
        """Return the set of "bin" targets in this package.

        The returned set is filtered by whether all their "required-features" are covered
        by the enabled feature set.
        """
        enabled, _, _, _ = self.get_enabled_features_transitive(flags or FeatureFlags())

        bins = set()
        for target in self.targets:
            if "bin" in target.kind and all(feature in enabled for feature in target.required_features):
                bins.add(target.name)
        return bins

    def get_enabled_features_transitive(  # noqa: C901
        self,
        flags: FeatureFlags,
    ) -> tuple[set[str], set[str], dict[str, set[str]], dict[str, set[str]]]:
        """Resolve transitive closure of enabled features and dependencies.

        This includes enabled features, enabled optional dependencies, enabled
        features of (optional or non-optional) dependencies, and conditionally
        enabled features of optional dependencies, taking feature flags into
        account.
        """
        # get names of all optional dependencies
        optional_names = set(self.get_normal_dependencies(optional=True).keys()).union(
            set(self.get_build_dependencies(optional=True).keys()),
        )

        # collect enabled features of this crate
        enabled: set[str] = set()
        # collect enabled optional dependencies
        optional_enabled: set[str] = set()
        # collect enabled features of other crates
        other_enabled: defaultdict[str, set[str]] = defaultdict(set)
        # collect conditionally enabled features of other crates
        other_conditional: defaultdict[str, set[str]] = defaultdict(set)

        # process arguments
        feature_names = self.get_feature_names()

        if not flags.no_default_features and "default" not in flags.features and "default" in feature_names:
            enabled.add("default")

        if flags.all_features:
            enabled.update(feature_names)
        enabled.update(flags.features)

        # calculate transitive closure of enabled features
        while True:
            new = set()

            for feature in enabled:
                deps = self.features[feature]

                for dep in deps:
                    # named optional dependency
                    if dep.startswith("dep:"):
                        name = dep.removeprefix("dep:")
                        optional_enabled.add(name)
                        continue

                    # dependency/feature
                    if "/" in dep and "?/" not in dep:
                        name, feat = dep.split("/")

                        # using "foo/bar" in feature dependencies implicitly
                        # also enables the optional dependency "foo":
                        if name in optional_names:
                            optional_enabled.add(name)

                        other_enabled[name].add(feat)
                        continue

                    # dependency?/feature
                    if "?/" in dep:
                        name, feat = dep.split("?/")
                        other_conditional[name].add(feat)
                        continue

                    # feature name
                    if dep not in enabled:
                        new.add(dep)

            # continue until set of enabled "proper" features no longer changes
            if new:
                enabled.update(new)
            else:
                break

        return enabled, optional_enabled, other_enabled, other_conditional


@dataclass(frozen=True)
class Metadata:
    """Representation of top-level crate metadata.

    This contains the entire JSON dump produced by calling
    "cargo metadata --format-version 1". The format of this data is guaranteed
    to be stable.

    The format of the data is the same whether run against "Cargo.toml" from an
    isolated crate or against a "Cargo.toml" manifest that defines a cargo
    workspace. The only difference is that for a single crate, the list of
    packages will be of length one, and for a workspace, the list of packages
    will (in general) be two or larger.
    """

    _data: dict

    def __repr__(self) -> str:
        return repr(self._data)

    @staticmethod
    def from_json(data: str) -> "Metadata":
        """Load JSON dump from input data and return a "Metadata" object.

        This method is used for loading JSON dumps for test input, as it does
        not require any other files (i.e. crate sources) to be present.
        """
        return Metadata(json.loads(data))

    @staticmethod
    def from_cargo(path: str) -> "Metadata":  # pragma nocover
        """Load metadata from cargo.

        This method only returns correct results when run against "Cargo.toml"
        files included in complete crate sources. Otherwise, automatic target
        discovery (i.e. the default behaviour of "autobins", "autoexamples",
        "autotests", and "autobenches") will result in missing build targets,
        and missing source files for explicitly specified "bin", "example",
        "test", or "bench" targets will cause errors.
        """
        ret = subprocess.run(  # noqa: S603
            [
                CARGO,
                "metadata",
                "--quiet",
                "--format-version",
                "1",
                "--offline",
                "--no-deps",
                "--manifest-path",
                path,
            ],
            capture_output=True,
            check=True,
            text=True,
        )

        if ret.stderr:
            print(ret.stderr, file=sys.stderr)  # noqa: T201

        return Metadata.from_json(ret.stdout)

    @property
    def packages(self) -> list[Package]:  # noqa: D102
        return [Package(package) for package in self._data["packages"]]

    @property
    def target_directory(self) -> str:  # noqa: D102
        return self._data["target_directory"]

    def is_workspace(self) -> bool:
        """Check whether this is metadata for a cargo workspace.

        A workspace with a single member is equivalent to no workspace (since
        no path dependencies are possible with only one workspace member), so
        the naive check for "at least two workspace members" is enough.
        """
        return len(self.packages) > 1

    def is_bin(self, flags: FeatureFlags) -> bool:
        """Check whether there are any "bin" targets in this workspace.

        Returns "True" if any workspace member has a "bin" target and the
        required features for at least one "bin" target are enabled.
        """
        return any(package.is_bin(flags) for package in self.packages)

    def is_lib(self) -> bool:
        """Check whether there is a "lib" or "proc-macro" target.

        Returns "True" if the crate has a "lib" or "proc-macro" target.
        Always returns "False" for cargo workspaces.
        """
        if len(self.packages) > 1:
            # do not report libs from workspaces until this is actually supported
            return False

        return any(package.is_lib() for package in self.packages)

    def is_cdylib(self, flags: FeatureFlags) -> bool:
        """Check whether there are any "cdylib" (C shared library") targets in this workspace.

        Returns "True" if any workspace member has a "cdylib" target and the
        required features for at least one "cdylib" target are enabled.
        """
        return any(package.is_cdylib(flags) for package in self.packages)

    def get_binaries(self, flags: FeatureFlags) -> set[str]:
        """Return the union of all sets of "bin" targets of all crates in this workspace.

        The returned set is filtered by whether all their "required-features" are covered
        by the enabled feature set.
        """
        bins = set()
        for package in self.packages:
            bins.update(package.get_binaries(flags))
        return bins

    def get_feature_flags_for_workspace_members(self, flags: FeatureFlags) -> dict[str, FeatureFlags]:  # noqa: C901,PLR0912,PLR0915
        """Resolve the transitive closure of enabled features for intra-workspace crate dependencies.

        This takes passed feature flags into account.
        """
        members = {package.name for package in self.packages}

        # keep track of workspace members and which features are enabled for them:
        # - determine union of enabled features for all workspace members
        member_features: dict[str, set[str]] = {}
        # - determine whether default features are enabled for workspace members
        member_defaults: dict[str, bool] = {}

        # apply feature flags to all packages
        for package in self.packages:
            if flags.all_features:
                features = member_features.get(package.name) or set()
                features.update(package.get_feature_names())
                member_features[package.name] = features

            if flags.features:
                features = member_features.get(package.name) or set()
                for feature in flags.features:
                    if feature in package.get_feature_names():
                        features.add(feature)
                member_features[package.name] = features

            if flags.no_default_features:
                member_defaults[package.name] = False

            # ensure that the mapping includes data for all packages
            features = member_features.get(package.name) or set()
            member_features[package.name] = features

        for package in self.packages:
            for dep in filter(lambda pkg: pkg.path is not None, package.dependencies):
                features = member_features.get(dep.name) or set()
                features.update(dep.features)
                member_features[dep.name] = features

                defaults = member_defaults.get(dep.name) or False
                defaults = defaults or dep.uses_default_features
                member_defaults[dep.name] = defaults

        # turn on default features for all workspace members that are not
        # explicitly referenced by other workspace members
        for package in self.packages:
            if package.name not in member_defaults:
                member_defaults[package.name] = True

        # enable features pulled in by feature dependencies of enabled features
        for package in self.packages:
            deps_real_names = {dep.rename or dep.name: dep.name for dep in package.dependencies}

            enabled = member_features[package.name].copy()
            if member_defaults[package.name] and "default" in package.get_feature_names():
                enabled.add("default")

            while True:
                new: set[str] = set()

                for feature_name, deps in package.features.items():
                    if feature_name not in enabled:
                        continue

                    for fdep in deps:
                        # named optional dependency
                        if fdep.startswith("dep:"):
                            # cargo builds all workspace members even if they are optional
                            continue

                        # dependency/feature
                        if "/" in fdep and "?/" not in fdep:
                            name, feat = fdep.split("/")

                            if deps_real_names[name] in members:
                                real_name = deps_real_names[name]
                                member_features[real_name].add(feat)
                            continue

                        # dependency?/feature
                        if "?/" in fdep:
                            name, feat = fdep.split("?/")

                            if deps_real_names[name] in members:
                                real_name = deps_real_names[name]
                                member_features[real_name].add(feat)
                            continue

                        # feature name
                        if fdep not in enabled:
                            new.add(fdep)
                            continue

                # continue until set of enabled "proper" features no longer changes
                if new:
                    enabled.update(new)
                else:
                    break

        # construct feature flags from collected settings
        member_flags: dict[str, FeatureFlags] = {}
        for package in self.packages:
            if member_features[package.name] == package.get_feature_names() and flags.all_features:
                flag_no_default_features = False
                flag_all_features = True
                flag_features = []
            else:
                flag_no_default_features = not member_defaults[package.name]
                flag_all_features = False
                flag_features = sorted(member_features[package.name])

            flags = FeatureFlags(all_features=flag_all_features, no_default_features=flag_no_default_features, features=flag_features)
            member_flags[package.name] = flags

        return member_flags
