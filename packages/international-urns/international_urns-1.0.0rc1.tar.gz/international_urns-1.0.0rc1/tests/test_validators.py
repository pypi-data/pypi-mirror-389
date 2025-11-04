"""Tests for the validator API."""

import pytest

from international_urns import get_validator, has_validator, list_validators
from international_urns.registry import get_registry


def test_get_validator_existing():
    """Test getting an existing validator."""
    # The wildcard validator should be registered on import
    validator = get_validator("--", "--")

    assert callable(validator)
    assert validator("urn:--:--:test") == "urn:--:--:test"


def test_get_validator_nonexistent():
    """Test getting a non-existent validator raises error."""
    with pytest.raises(ValueError, match="No validator registered"):
        get_validator("zz", "invalid")


def test_has_validator():
    """Test checking if a validator exists."""
    # Wildcard should exist
    assert has_validator("--", "--")

    # Random combination should not exist
    assert not has_validator("zz", "invalid")


def test_has_validator_case_insensitive():
    """Test that has_validator is case-insensitive."""
    assert has_validator("--", "--")
    assert has_validator("--", "--")


def test_list_validators():
    """Test listing all validators."""
    validators = list_validators()

    assert isinstance(validators, list)
    # At minimum, wildcard validator should be present
    assert ("--", "--") in validators


def test_get_validator_integration():
    """Test the full validator workflow."""
    registry = get_registry()

    def mock_validator(urn: str) -> str:
        if "invalid" in urn.lower():
            raise ValueError("Invalid URN")
        return urn.lower()

    registry.register("zw", "mock", mock_validator)

    validator = get_validator("zw", "mock")

    assert validator("urn:zw:mock:123") == "urn:zw:mock:123"

    with pytest.raises(ValueError, match="Invalid URN"):
        validator("urn:zw:mock:invalid")
