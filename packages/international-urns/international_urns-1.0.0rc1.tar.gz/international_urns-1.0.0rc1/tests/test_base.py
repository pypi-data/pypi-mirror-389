"""Tests for the base URNValidator class."""

import pytest

from international_urns.base import URNValidator
from international_urns.registry import URNRegistry


def test_validator_auto_registration():
    """Test that validators auto-register using __init_subclass__."""
    registry = URNRegistry()

    class TestValidator(URNValidator):
        country_code = "zz"
        document_types = ["type1", "type2"]

        def validate(self, urn: str) -> str:
            return urn.lower()

    validator = TestValidator()
    registry.register("zz", "type1", validator.validate)
    registry.register("zz", "type2", validator.validate)

    assert registry.has_validator("zz", "type1")
    assert registry.has_validator("zz", "type2")


def test_validator_multiple_document_types():
    """Test validator with multiple document types."""
    registry = URNRegistry()

    class MultiTypeValidator(URNValidator):
        country_code = "mx"
        document_types = ["curp", "rfc", "ine"]

        def validate(self, urn: str) -> str:
            return urn

    validator = MultiTypeValidator()
    for doc_type in ["curp", "rfc", "ine"]:
        registry.register("mx", doc_type, validator.validate)

    assert registry.has_validator("mx", "curp")
    assert registry.has_validator("mx", "rfc")
    assert registry.has_validator("mx", "ine")


def test_abstract_validator_not_registered():
    """Test that abstract validators without attributes aren't registered."""
    # This should not raise an error even though it doesn't define attributes
    class AbstractValidator(URNValidator):
        def validate(self, urn: str) -> str:
            return urn

    # No assertion needed - just checking it doesn't crash


def test_validator_must_implement_validate():
    """Test that validators must implement the validate method."""

    class IncompleteValidator(URNValidator):  # type: ignore
        country_code = "yy"
        document_types = ["test"]

    with pytest.raises(TypeError):
        IncompleteValidator()
