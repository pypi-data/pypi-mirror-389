import re

import pytest

from cargo2rpm.metadata import FeatureFlags


def test_feature_flags_invalid():
    with pytest.raises(ValueError, match=re.escape("Cannot specify both '--all-features' and '--features'.")):
        FeatureFlags(all_features=True, features=["default"])

    with pytest.raises(ValueError, match=re.escape("Cannot specify both '--all-features' and '--no-default-features'.")):
        FeatureFlags(no_default_features=True, all_features=True)
