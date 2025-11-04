"""Integration tests for the complete URN validation system."""

import pytest

from international_urns import (
    URNValidator,
    create_normalizer,
    get_validator,
    list_validators,
)


def test_full_workflow():
    """Test the complete workflow from registration to validation."""
    # Create a custom validator
    class CustomValidator(URNValidator):
        country_code = "xy"
        document_types = ["test"]

        def validate(self, urn: str) -> str:
            # Simple validation: just check it starts with the right prefix
            if not urn.lower().startswith("urn:xy:test:"):
                raise ValueError(f"Invalid URN format: {urn}")
            return urn

    # The validator should auto-register via __init_subclass__
    # Verify it was registered
    from international_urns.registry import get_registry

    registry = get_registry()
    assert registry.has_validator("xy", "test")

    # Now we should be able to get and use it via the public API
    validator = get_validator("xy", "test")

    valid_urn = "urn:xy:test:12345"
    assert validator(valid_urn) == valid_urn

    with pytest.raises(ValueError):
        validator("urn:wrong:format:12345")


def test_normalization_with_validation():
    """Test using normalization before validation."""
    normalizer = create_normalizer()
    validator = get_validator("--", "--")

    # Normalize then validate
    urn = "URN:--:--:TEST"
    normalized = normalizer(urn)
    validated = validator(normalized)

    assert normalized == "urn:--:--:TEST"
    assert validated == "urn:--:--:TEST"


def test_pydantic_integration():
    """Test integration with Pydantic validators."""
    pytest.importorskip("pydantic")

    from typing import Annotated

    from pydantic import AfterValidator, BaseModel, BeforeValidator, ValidationError

    from international_urns import create_normalizer, get_validator

    class Document(BaseModel):
        urn: Annotated[
            str,
            BeforeValidator(create_normalizer()),
            AfterValidator(get_validator("--", "--")),
        ]

    # Valid URN
    doc = Document(urn="URN:--:--:test123")
    assert doc.urn == "urn:--:--:test123"

    # Invalid URN
    with pytest.raises(ValidationError):
        Document(urn="not-a-urn")


def test_wildcard_validator_registered():
    """Test that wildcard validator is automatically registered."""
    validators = list_validators()

    assert ("--", "--") in validators

    # Should be able to use it
    validator = get_validator("--", "--")
    assert validator("urn:--:--:anything") == "urn:--:--:anything"
