"""Tests for the URN registry."""

import pytest

from international_urns.registry import URNRegistry


def test_registry_register_validator():
    """Test registering a validator."""
    registry = URNRegistry()

    def dummy_validator(urn: str) -> str:
        return urn

    registry.register("es", "dni", dummy_validator)

    assert registry.has_validator("es", "dni")
    assert registry.get_validator("es", "dni") == dummy_validator


def test_registry_case_insensitive():
    """Test that country codes and document types are case-insensitive."""
    registry = URNRegistry()

    def dummy_validator(urn: str) -> str:
        return urn

    registry.register("ES", "DNI", dummy_validator)

    # Should be accessible with different cases
    assert registry.has_validator("es", "dni")
    assert registry.has_validator("ES", "DNI")
    assert registry.has_validator("Es", "Dni")
    assert registry.get_validator("es", "dni") == dummy_validator


def test_registry_duplicate_registration():
    """Test that duplicate registration raises an error."""
    registry = URNRegistry()

    def validator1(urn: str) -> str:
        return urn

    def validator2(urn: str) -> str:
        return urn.upper()

    registry.register("es", "dni", validator1)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("es", "dni", validator2)


def test_registry_get_nonexistent_validator():
    """Test getting a non-existent validator returns None."""
    registry = URNRegistry()

    assert registry.get_validator("fr", "nie") is None
    assert not registry.has_validator("fr", "nie")


def test_registry_list_validators():
    """Test listing all registered validators."""
    registry = URNRegistry()

    def dummy_validator(urn: str) -> str:
        return urn

    registry.register("es", "dni", dummy_validator)
    registry.register("es", "nie", dummy_validator)
    registry.register("fr", "nir", dummy_validator)

    validators = registry.list_validators()

    assert len(validators) == 3
    assert ("es", "dni") in validators
    assert ("es", "nie") in validators
    assert ("fr", "nir") in validators


def test_registry_validates_country_code_format():
    """Test that registry enforces ISO 3166-1 Alpha-2 format."""
    registry = URNRegistry()

    def dummy_validator(urn: str) -> str:
        return urn

    with pytest.raises(ValueError, match="ISO 3166-1 Alpha-2"):
        registry.register("usa", "ssn", dummy_validator)

    with pytest.raises(ValueError, match="ISO 3166-1 Alpha-2"):
        registry.register("e", "dni", dummy_validator)

    with pytest.raises(ValueError, match="ISO 3166-1 Alpha-2"):
        registry.register("123", "tax", dummy_validator)

    registry.register("--", "wildcard", dummy_validator)
    assert registry.has_validator("--", "wildcard")
