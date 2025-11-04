"""Tests for built-in validators."""

import pytest

from international_urns.builtin import WildcardValidator


@pytest.mark.parametrize(
    "valid_urn",
    [
        "urn:--:--:anything",
        "URN:--:--:ANYTHING",
        "urn:--:--:123",
        "urn:--:--:with:multiple:colons",
        "urn:--:--:special!@#$%chars",
    ],
)
def test_wildcard_validator_valid_urns(valid_urn):
    """Test that wildcard validator accepts valid URNs."""
    validator = WildcardValidator()
    result = validator.validate(valid_urn)
    assert result == valid_urn


@pytest.mark.parametrize(
    "invalid_urn",
    [
        "urn:es:dni:123",  # Not wildcard format
        "urn:--:dni:123",  # Partial wildcard
        "urn:es:--:123",  # Partial wildcard
        "not:--:--:urn",  # Wrong scheme
        "urn:--:--",  # Missing NSS value
        "urn:--",  # Incomplete
        "",  # Empty
    ],
)
def test_wildcard_validator_invalid_urns(invalid_urn):
    """Test that wildcard validator rejects invalid URNs."""
    validator = WildcardValidator()

    with pytest.raises(ValueError):
        validator.validate(invalid_urn)


def test_wildcard_validator_case_insensitive():
    """Test that wildcard validator is case-insensitive for prefix."""
    validator = WildcardValidator()

    urns = [
        "urn:--:--:test",
        "URN:--:--:test",
        "Urn:--:--:test",
        "urn:--:--:test",
    ]

    for urn in urns:
        result = validator.validate(urn)
        assert result == urn
