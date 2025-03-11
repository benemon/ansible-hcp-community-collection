import pytest
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.collection_utils import str_to_bool

def test_str_to_bool_true_values():
    # Test various representations that should be interpreted as True.
    true_values = ["y", "yes", "t", "true", "on", "1", "  YES  ", "True"]
    for value in true_values:
        assert str_to_bool(value) is True, f"Expected {value!r} to be True"

def test_str_to_bool_false_values():
    # Test various representations that should be interpreted as False.
    false_values = ["n", "no", "f", "false", "off", "0", "  NO  ", "False"]
    for value in false_values:
        assert str_to_bool(value) is False, f"Expected {value!r} to be False"

def test_str_to_bool_invalid_values():
    # Test values that should raise ValueError.
    invalid_values = ["maybe", "2", "", "   ", "foo", None, 123]
    for value in invalid_values:
        with pytest.raises(ValueError, match="Invalid truth value"):
            str_to_bool(value)
