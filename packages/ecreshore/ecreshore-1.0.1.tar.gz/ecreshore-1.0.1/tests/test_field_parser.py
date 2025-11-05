"""Unit tests for parse_field() and FieldSpec from batch_config.py.

Following brain/patterns/fixture-pattern.xml and brain/patterns/factory-fixture-pattern.xml
for test structure and reusable fixtures.
"""

import pytest
from src.ecreshore.services.batch_config import FieldSpec, parse_field
from src.ecreshore.services.error_handler import ConfigurationError


# Fixtures following brain/patterns/fixture-pattern.xml

@pytest.fixture
def common_field_specs():
    """Reusable FieldSpec configurations for testing.

    Follows brain pattern: fixture-pattern for shared test data.
    """
    return {
        'required_string': FieldSpec('name', str, required=True),
        'optional_int': FieldSpec('count', int),
        'optional_bool': FieldSpec('enabled', bool, allow_none=True),
        'string_with_transform': FieldSpec('email', str, transform=str.lower),
        'string_with_strip': FieldSpec('title', str, transform=str.strip),
        'nullable_string': FieldSpec('description', str, allow_none=True),
    }


# Tests for required fields

def test_parse_field_required_present(common_field_specs):
    """Required field present in data - returns value."""
    data = {'name': 'test-value'}
    result = parse_field(data, common_field_specs['required_string'])

    assert result == 'test-value'


def test_parse_field_required_missing(common_field_specs):
    """Required field missing from data - raises ConfigurationError."""
    data = {}

    with pytest.raises(ConfigurationError, match="Missing required field 'name'"):
        parse_field(data, common_field_specs['required_string'])


# Tests for optional fields with defaults

def test_parse_field_optional_missing_with_default(common_field_specs):
    """Optional field missing - returns default value."""
    data = {}
    result = parse_field(data, common_field_specs['optional_int'], default=42)

    assert result == 42


def test_parse_field_optional_missing_no_default(common_field_specs):
    """Optional field missing, no default - returns None."""
    data = {}
    result = parse_field(data, common_field_specs['optional_int'])

    assert result is None


def test_parse_field_optional_present(common_field_specs):
    """Optional field present - returns value, ignores default."""
    data = {'count': 100}
    result = parse_field(data, common_field_specs['optional_int'], default=42)

    assert result == 100


# Tests for type validation

def test_parse_field_correct_type(common_field_specs):
    """Field with correct type - passes validation."""
    data = {'count': 50}
    result = parse_field(data, common_field_specs['optional_int'])

    assert result == 50
    assert isinstance(result, int)


def test_parse_field_wrong_type_string_expected_int(common_field_specs):
    """Field with wrong type - raises ConfigurationError with helpful message."""
    data = {'count': "not-an-int"}

    with pytest.raises(ConfigurationError, match="'count' must be an integer"):
        parse_field(data, common_field_specs['optional_int'])


def test_parse_field_wrong_type_int_expected_bool():
    """Bool field with int value - raises ConfigurationError."""
    spec = FieldSpec('flag', bool)
    data = {'flag': 1}  # Common mistake

    with pytest.raises(ConfigurationError, match="'flag' must be a boolean"):
        parse_field(data, spec)


# Tests for None handling

def test_parse_field_none_allowed(common_field_specs):
    """None value with allow_none=True - returns None."""
    data = {'description': None}
    result = parse_field(data, common_field_specs['nullable_string'])

    assert result is None


def test_parse_field_none_not_allowed():
    """None value with allow_none=False - raises ConfigurationError."""
    spec = FieldSpec('name', str, allow_none=False)
    data = {'name': None}

    with pytest.raises(ConfigurationError, match="Field 'name' cannot be None"):
        parse_field(data, spec)


def test_parse_field_none_with_transform(common_field_specs):
    """None value with transform and allow_none=True - returns None without calling transform."""
    data = {'description': None}
    result = parse_field(data, common_field_specs['nullable_string'])

    # Should return None without attempting str.strip() on None
    assert result is None


# Tests for transform functions

def test_parse_field_transform_applied(common_field_specs):
    """Transform function is applied to value."""
    data = {'email': 'TEST@EXAMPLE.COM'}
    result = parse_field(data, common_field_specs['string_with_transform'])

    assert result == 'test@example.com'


def test_parse_field_transform_strip_whitespace(common_field_specs):
    """Transform strips whitespace from string."""
    data = {'title': '  Hello World  '}
    result = parse_field(data, common_field_specs['string_with_strip'])

    assert result == 'Hello World'


def test_parse_field_transform_with_lambda():
    """Transform using lambda function."""
    spec = FieldSpec(
        'path',
        str,
        transform=lambda s: s.strip() if s else None
    )

    # With value
    data1 = {'path': '  /home/user  '}
    result1 = parse_field(data1, spec)
    assert result1 == '/home/user'

    # With empty string
    data2 = {'path': ''}
    result2 = parse_field(data2, spec)
    assert result2 is None


# Tests for edge cases

def test_parse_field_empty_string_allowed():
    """Empty string is valid if type matches."""
    spec = FieldSpec('name', str)
    data = {'name': ''}
    result = parse_field(data, spec)

    assert result == ''


def test_parse_field_list_type():
    """List type validation works."""
    spec = FieldSpec('items', list)
    data = {'items': ['a', 'b', 'c']}
    result = parse_field(data, spec)

    assert result == ['a', 'b', 'c']


def test_parse_field_list_type_wrong():
    """Non-list for list field - raises error."""
    spec = FieldSpec('items', list)
    data = {'items': 'not-a-list'}

    with pytest.raises(ConfigurationError, match="'items' must be a list"):
        parse_field(data, spec)


# Integration test - typical usage pattern

def test_parse_field_typical_settings_workflow():
    """Test parsing multiple fields like in _parse_settings()."""
    settings_data = {
        'concurrent_transfers': 5,
        'retry_attempts': 3,
        'region': '  us-west-2  ',
        'verify_digests': True
    }

    # Parse each field
    concurrent = parse_field(
        settings_data,
        FieldSpec('concurrent_transfers', int),
        default=3
    )

    retry = parse_field(
        settings_data,
        FieldSpec('retry_attempts', int),
        default=3
    )

    region = parse_field(
        settings_data,
        FieldSpec('region', str, allow_none=True, transform=lambda s: s.strip() if s else None),
        default=None
    )

    verify = parse_field(
        settings_data,
        FieldSpec('verify_digests', bool),
        default=True
    )

    assert concurrent == 5
    assert retry == 3
    assert region == 'us-west-2'  # Stripped
    assert verify is True


# Edge case: error message format validation

def test_parse_field_error_message_format_required():
    """Error message for required field follows expected format."""
    spec = FieldSpec('api_key', str, required=True)
    data = {}

    try:
        parse_field(data, spec)
        pytest.fail("Expected ConfigurationError to be raised")
    except ConfigurationError as e:
        assert "Missing required field 'api_key'" in str(e)


def test_parse_field_error_message_format_type():
    """Error message for type mismatch follows expected format."""
    spec = FieldSpec('port', int)
    data = {'port': '8080'}

    try:
        parse_field(data, spec)
        pytest.fail("Expected ConfigurationError to be raised")
    except ConfigurationError as e:
        assert "'port' must be an integer" in str(e)
