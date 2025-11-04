"""Tests for URN normalization utilities."""

import pytest

from international_urns.normalization import create_normalizer, normalize_urn


@pytest.mark.parametrize(
    "input_urn,expected",
    [
        ("URN:ES:DNI:12345678X", "urn:es:dni:12345678X"),
        ("urn:es:dni:12345678X", "urn:es:dni:12345678X"),
        ("URN:ES:DNI:12345678x", "urn:es:dni:12345678x"),
        ("urn:FR:NIR:123456789012345", "urn:fr:nir:123456789012345"),
        ("URN:--:--:anything", "urn:--:--:anything"),
        ("urn:MX:CURP:ABCD123456HDFRRL09", "urn:mx:curp:ABCD123456HDFRRL09"),
    ],
)
def test_normalize_urn(input_urn, expected):
    """Test URN normalization with various inputs."""
    assert normalize_urn(input_urn) == expected


@pytest.mark.parametrize(
    "invalid_urn",
    [
        "not a urn",
        "urn:es",
        "urn:es:dni",
        "urn::dni:123",
        "es:dni:123",
        "urn:es::123",
        "",
    ],
)
def test_normalize_urn_invalid_format(invalid_urn):
    """Test that invalid URN formats raise ValueError."""
    with pytest.raises(ValueError, match="Invalid URN format"):
        normalize_urn(invalid_urn)


def test_normalize_urn_preserves_nss_case():
    """Test that the NSS remainder preserves its original case."""
    urn = "URN:ES:DNI:AbCdEfGh"
    normalized = normalize_urn(urn)

    # Scheme, country, and doc type should be lowercase
    # NSS remainder should preserve case
    assert normalized == "urn:es:dni:AbCdEfGh"


def test_create_normalizer():
    """Test that create_normalizer returns a working function."""
    normalizer = create_normalizer()

    assert callable(normalizer)
    assert normalizer("URN:ES:DNI:12345678X") == "urn:es:dni:12345678X"
