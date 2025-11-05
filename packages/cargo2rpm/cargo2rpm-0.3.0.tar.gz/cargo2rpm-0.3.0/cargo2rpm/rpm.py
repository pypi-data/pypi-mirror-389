"""Implementation of algorithms to translate from crate metadata to RPM metadata."""

from collections import defaultdict

from cargo2rpm.metadata import FeatureFlags, Metadata, Package
from cargo2rpm.semver import Version


class InvalidFeatureError(Exception):
    """Error raised when a function is called with an invalid feature name.

    This is usually the result of a packager error, for example, when
    a spec file has not been properly regenerated for a new crate version
    (which has removed a previously included feature) or after patching the
    upstream `Cargo.toml` file to remove unwanted features or optional
    dependencies.
    """

    def __init__(self, error: str):  # noqa: D107
        self.error = error
        super().__init__(error)


def _msrv_from_edition(edition: str) -> str | None:
    match edition:
        case "2015":
            return None
        case "2018":
            return "1.31"
        case "2021":
            return "1.56"
        case "2024":
            return "1.85"
        case _:
            msg = f"Invalid Edition: {edition}"
            raise ValueError(msg)


def buildrequires(package: Package, flags: FeatureFlags, *, with_dev_deps: bool) -> set[str]:  # noqa: C901,PLR0912,PLR0915
    """Resolve and return RPM `BuildRequires` of the `package` crate.

    This takes into account feature flags passed in the `flags` argument (which
    represents the presence of the `--all-features`, `--no-default-features, or
    `--features` CLI flags of cargo), and only includes dev-dependencies if
    `with_dev_deps` is passed as `True`.

    This happens in two stages - first, the list of enabled features (and
    whether they are used with "default" features) is resolved for all
    dependencies; then this information is used to generate the actual set of
    dependencies in RPM format.
    """
    enabled, optional_enabled, other_enabled, other_conditional = package.get_enabled_features_transitive(flags)

    normal = package.get_normal_dependencies(optional=False)
    normal_optional = package.get_normal_dependencies(optional=True)
    build = package.get_build_dependencies(optional=False)
    build_optional = package.get_build_dependencies(optional=True)
    dev = package.get_dev_dependencies()

    # keep track of dependencies and which features are enabled for them:
    # - determine union of enabled features for all dependencies
    deps_enabled_features: defaultdict[str, set[str]] = defaultdict(set)
    # - determine whether default features are enabled for all dependencies
    deps_default_features: dict[str, bool] = {}
    # - determine optional dependencies that need to be enabled as workarounds
    workarounds: dict[str, tuple[set[str], bool]] = {}

    # unconditionally enabled features of normal dependencies
    for name, dep in normal.items():
        deps_enabled_features[name].update(dep.features)

        defaults = deps_default_features.get(name) or False
        defaults = defaults or dep.uses_default_features
        deps_default_features[name] = defaults

    # unconditionally enabled features of enabled, optional, normal dependencies
    for name, dep in normal_optional.items():
        if name in optional_enabled:
            deps_enabled_features[name].update(dep.features)

            defaults = deps_default_features.get(name) or False
            defaults = defaults or dep.uses_default_features
            deps_default_features[name] = defaults

    # unconditionally enabled features of build-dependencies
    for name, dep in build.items():
        deps_enabled_features[name].update(dep.features)

        defaults = deps_default_features.get(name) or False
        defaults = defaults or dep.uses_default_features
        deps_default_features[name] = defaults

    # unconditionally enabled features of enabled, optional, build-dependencies
    for name, dep in build_optional.items():
        if name in optional_enabled:
            deps_enabled_features[name].update(dep.features)

            defaults = deps_default_features.get(name) or False
            defaults = defaults or dep.uses_default_features
            deps_default_features[name] = defaults

    # unconditionally enabled features of enabled dev-dependencies
    if with_dev_deps:
        for name, dep in dev.items():
            deps_enabled_features[name].update(dep.features)

            defaults = deps_default_features.get(name) or False
            defaults = defaults or dep.uses_default_features
            deps_default_features[name] = defaults

    # features unconditionally enabled by feature dependencies
    for name, other_features in other_enabled.items():
        deps_enabled_features[name].update(other_features)

        if "default" in deps_enabled_features[name]:
            deps_default_features[name] = True

    # features conditionally enabled by feature dependencies
    for name, other_features in other_conditional.items():
        deps_enabled_features[name].update(other_features)

        if name not in enabled:
            defaults = deps_default_features.get(name) or False
            if odep := normal_optional.get(name):
                defaults = defaults or odep.uses_default_features
                additional_features = odep.features
            if odep := build_optional.get(name):
                defaults = defaults or odep.uses_default_features
                additional_features = odep.features
            workarounds[name] = (set.union(other_features, additional_features), defaults)

    # collect dependencies taking into account which features are enabled
    brs = set()

    # minimum supported Rust version
    if (msrv := package.rust_version) or (msrv := _msrv_from_edition(package.edition)):
        brs.add(f"rust >= {msrv}")

    # normal dependencies
    for name, dep in normal.items():
        if dep.is_path_or_git():
            continue

        brs.add(dep.to_rpm("default" if deps_default_features[name] else None))
        brs.update(dep.to_rpm(feature) for feature in deps_enabled_features[name])

    # optional normal dependencies
    for name, dep in normal_optional.items():
        if dep.is_path_or_git():
            continue

        if name in optional_enabled:
            brs.add(dep.to_rpm("default" if deps_default_features[name] else None))
            brs.update(dep.to_rpm(feature) for feature in deps_enabled_features[name])

    # build-dependencies
    for name, dep in build.items():
        if dep.is_path_or_git():
            continue

        brs.add(dep.to_rpm("default" if deps_default_features[name] else None))
        brs.update(dep.to_rpm(feature) for feature in deps_enabled_features[name])

    # optional build-dependencies
    for name, dep in build_optional.items():
        if dep.is_path_or_git():
            continue

        if name in optional_enabled:
            brs.add(dep.to_rpm("default" if deps_default_features[name] else None))
            brs.update(dep.to_rpm(feature) for feature in deps_enabled_features[name])

    # dev-dependencies
    if with_dev_deps:
        for name, dep in dev.items():
            if dep.is_path_or_git():
                continue

            brs.add(dep.to_rpm("default" if deps_default_features[name] else None))
            brs.update(dep.to_rpm(feature) for feature in deps_enabled_features[name])

    # workarounds
    for name, (features, defaults) in workarounds.items():
        if odep := normal_optional.get(name):
            if odep.is_path_or_git():
                continue
            brs.add(odep.to_rpm("default" if defaults else None))
            brs.update(odep.to_rpm(feature) for feature in features)

        if odep := build_optional.get(name):
            if odep.is_path_or_git():
                continue
            brs.add(odep.to_rpm("default" if defaults else None))
            brs.update(odep.to_rpm(feature) for feature in features)

    return brs


def workspace_buildrequires(metadata: Metadata, flags: FeatureFlags, *, with_dev_deps: bool) -> set[str]:
    """Resolve and return RPM `BuildRequires` for an entire cargo workspace.

    Prior to generating `BuildRequires` for every individual workspace member,
    intra-workspace dependencies are resolved (i.e. which features of which
    workspace member are enabled).

    This takes into account "required features" of binary targets (i.e. crates
    with "bin" or "cdylib" targets).
    """
    all_brs = set()

    member_flags = metadata.get_feature_flags_for_workspace_members(flags)
    for package in metadata.packages:
        all_brs.update(buildrequires(package, member_flags[package.name], with_dev_deps=with_dev_deps))

    return all_brs


def devel_subpackage_names(package: Package) -> set[str]:
    """Return the set of subpackage names for a crate.

    If the crate does not provide a "lib" target, the set will be empty.
    Otherwise, the set of "features" of the crate is returned, with the
    implicitly defined "default" feature explicitly included.
    """
    # no feature subpackages are generated for binary-only crates
    if not package.is_lib():
        return set()

    names = package.get_feature_names()

    # the "default" feature is always implicitly defined
    if "default" not in names:
        names.add("default")

    return names


def _requires_crate(package: Package) -> set[str]:
    """Resolve install-time dependencies of the given crate.

    Used for automatically generating dependencies of crate packages with
    RPM generators.

    This only includes non-optional "normal" and "build-dependencies" of the
    crate (i.e. no enabled features or enabled optional dependencies), and
    a dependency on "cargo".
    """
    normal = package.get_normal_dependencies(optional=False)
    build = package.get_build_dependencies(optional=False)

    deps = set()

    # dependency on cargo is mandatory
    deps.add("cargo")

    # minimum supported Rust version
    if msrv := package.rust_version:
        deps.add(f"rust >= {msrv}")

    # normal dependencies
    for dep in normal.values():
        deps.add(dep.to_rpm("default" if dep.uses_default_features else None))
        deps.update(dep.to_rpm(depf) for depf in dep.features)

    # build-dependencies
    for dep in build.values():
        deps.add(dep.to_rpm("default" if dep.uses_default_features else None))
        deps.update(dep.to_rpm(depf) for depf in dep.features)

    return deps


def _requires_feature(package: Package, feature: str) -> set[str]:  # noqa: C901,PLR0912,PLR0915
    """Resolve install-time dependencies of the given crate feature.

    This includes optional "normal" and "build-dependencies" of the
    crate that are specified as dependencies of the given feature, a
    dependency on the "main" crate package, and a dependency on "cargo".

    Raises an `InvalidFeatureError` if the given feature is not a feature
    of the crate.
    """
    if feature != "default" and feature not in package.get_feature_names():
        msg = f"Unknown feature: {feature}"
        raise InvalidFeatureError(msg)

    deps = set()

    # dependency on cargo is mandatory
    deps.add("cargo")

    if feature == "default" and "default" not in package.get_feature_names():
        # default feature is implicitly defined but empty
        deps.add(package.to_rpm_dependency(None))
        return deps

    feature_deps = package.features[feature]

    normal = package.get_normal_dependencies(optional=False)
    normal_optional = package.get_normal_dependencies(optional=True)
    build_optional = package.get_build_dependencies(optional=True)

    # always add a dependency on the main crate
    deps.add(package.to_rpm_dependency(None))

    for fdep in feature_deps:
        if fdep.startswith("dep:"):
            # optional dependency
            name = fdep.removeprefix("dep:")

            found = False
            if dep := normal_optional.get(name):
                # optional normal dependency
                found = True
                deps.add(dep.to_rpm("default" if dep.uses_default_features else None))
                deps.update(dep.to_rpm(depf) for depf in dep.features)

            if dep := build_optional.get(name):
                # optional build-dependency
                found = True
                deps.add(dep.to_rpm("default" if dep.uses_default_features else None))
                deps.update(dep.to_rpm(depf) for depf in dep.features)

            if not found:  # pragma nocover
                msg = f"No optional dependency found with name {name!r}."
                raise InvalidFeatureError(msg)

        elif "/" in fdep and "?/" not in fdep:
            # dependency with specified feature
            name, feat = fdep.split("/")

            # implicitly enabled optional dependency
            if dep := normal_optional.get(name):
                deps.add(dep.to_rpm(feat))
                deps.add(dep.to_rpm("default" if dep.uses_default_features else None))
                deps.update(dep.to_rpm(depf) for depf in dep.features)

            if dep := build_optional.get(name):
                deps.add(dep.to_rpm(feat))
                deps.add(dep.to_rpm("default" if dep.uses_default_features else None))
                deps.update(dep.to_rpm(depf) for depf in dep.features)

            # normal dependency
            if dep := normal.get(name):
                deps.add(dep.to_rpm(feat))

        elif "?/" in fdep:
            # conditionally enabled dependency feature
            name, feat = fdep.split("?/")

            if dep := normal_optional.get(name):
                deps.add(f"{dep.to_rpm(feat)}")
                deps.add(dep.to_rpm("default" if dep.uses_default_features else None))
                deps.update(dep.to_rpm(depf) for depf in dep.features)

            if dep := build_optional.get(name):
                deps.add(f"{dep.to_rpm(feat)}")
                deps.add(dep.to_rpm("default" if dep.uses_default_features else None))
                deps.update(dep.to_rpm(depf) for depf in dep.features)

        else:
            # dependency on a feature of the current crate
            if fdep not in package.get_feature_names():  # pragma nocover
                msg = f"Invalid feature dependency (not a feature name): {fdep!r}"
                raise InvalidFeatureError(msg)

            deps.add(package.to_rpm_dependency(fdep))

    return deps


def requires(package: Package, feature: str | None) -> set[str]:
    """Return standardized "virtual Requires" for crates and their features."""
    if feature is None:
        return _requires_crate(package)
    return _requires_feature(package, feature)


def _provides_crate(package: Package) -> str:
    """Return a standardized identifier for the "main" crate subpackage.

    This is of the form `crate(foo) = x.y.z` which is used for the automatic
    generation of "virtual Provides".
    """
    rpm_version = Version.parse(package.version).to_rpm()
    return f"crate({package.name}) = {rpm_version}"


def _provides_feature(package: Package, feature: str) -> str:
    """Return a standardized identifier for the "feature" crate subpackages.

    This is of the form `crate(foo/bar) = x.y.z` and is used for the automatic
    generation of "virtual Provides".
    """
    if feature != "default" and feature not in package.get_feature_names():
        msg = f"Unknown feature: {feature}"
        raise InvalidFeatureError(msg)

    rpm_version = Version.parse(package.version).to_rpm()
    return f"crate({package.name}/{feature}) = {rpm_version}"


def provides(package: Package, feature: str | None) -> str:
    """Return standardized "virtual Provides" for crates and their features."""
    if feature is None:
        return _provides_crate(package)
    return _provides_feature(package, feature)
