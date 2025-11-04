# International URNs - Plugin Development

Complete guide for creating, testing, and distributing validator plugins.

## Plugin Architecture

Plugins are separate Python packages that extend International URNs with country-specific validators. They:

1. Define validators by subclassing `URNValidator`
2. Auto-register via the `__init_subclass__` hook
3. Are discovered via Python entry points
4. Load automatically when `international_urns` is imported

## Creating a Plugin Package

### 1. Package Structure

```
international-urns-es/
├── international_urns_es/
│   ├── __init__.py
│   ├── dni.py
│   ├── nie.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_dni.py
│   └── test_nie.py
├── pyproject.toml
├── README.md
└── LICENSE
```

### 2. Configure pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "international-urns-es"
version = "0.1.0"
description = "Spanish document validators for International URNs"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
dependencies = [
    "international-urns>=0.1.0",
]

[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
]

# IMPORTANT: Register your plugin here
[project.entry-points.'international_urns.plugins']
es = 'international_urns_es'

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 3. Implement Validators

**international_urns_es/__init__.py:**

```python
"""Spanish document validators for International URNs."""

__version__ = "0.1.0"

# Import validators to trigger auto-registration
from .dni import DNIValidator
from .nie import NIEValidator

__all__ = ["DNIValidator", "NIEValidator"]
```

**international_urns_es/dni.py:**

```python
"""Spanish DNI (Documento Nacional de Identidad) validator."""

from international_urns import URNValidator

__all__ = ["DNIValidator"]


class DNIValidator(URNValidator):
    """Validator for Spanish DNI documents.

    DNI format: 8 digits followed by 1 letter (checksum).
    Example: 12345678Z
    """

    country_code = "es"
    document_types = ["dni"]

    CHECKSUM_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

    def validate(self, urn: str) -> str:
        """Validate Spanish DNI URN.

        :param urn: The URN string to validate
        :type urn: str
        :return: The validated URN string
        :rtype: str
        :raises ValueError: If the URN or DNI format is invalid
        """
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        dni = parts[3]

        # Validate format
        if len(dni) != 9:
            raise ValueError(f"DNI must be 9 characters (8 digits + 1 letter): {dni}")

        number_part = dni[:8]
        letter = dni[8].upper()

        if not number_part.isdigit():
            raise ValueError(f"First 8 characters must be digits: {dni}")

        if not letter.isalpha():
            raise ValueError(f"Last character must be a letter: {dni}")

        # Verify checksum
        expected_letter = self.CHECKSUM_LETTERS[int(number_part) % 23]
        if letter != expected_letter:
            raise ValueError(
                f"Invalid DNI checksum. Expected letter '{expected_letter}', "
                f"got '{letter}' for number {number_part}"
            )

        return urn
```

**international_urns_es/nie.py:**

```python
"""Spanish NIE (Número de Identidad de Extranjero) validator."""

from international_urns import URNValidator

__all__ = ["NIEValidator"]


class NIEValidator(URNValidator):
    """Validator for Spanish NIE documents.

    NIE format: Letter (X, Y, or Z) + 7 digits + 1 checksum letter.
    Example: X1234567L
    """

    country_code = "es"
    document_types = ["nie"]

    CHECKSUM_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
    VALID_PREFIXES = {'X': 0, 'Y': 1, 'Z': 2}

    def validate(self, urn: str) -> str:
        """Validate Spanish NIE URN.

        :param urn: The URN string to validate
        :type urn: str
        :return: The validated URN string
        :rtype: str
        :raises ValueError: If the URN or NIE format is invalid
        """
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        nie = parts[3]

        # Validate format
        if len(nie) != 9:
            raise ValueError(f"NIE must be 9 characters: {nie}")

        prefix = nie[0].upper()
        number_part = nie[1:8]
        letter = nie[8].upper()

        # Validate prefix
        if prefix not in self.VALID_PREFIXES:
            raise ValueError(
                f"NIE must start with X, Y, or Z. Got: {prefix}"
            )

        # Validate number part
        if not number_part.isdigit():
            raise ValueError(f"Characters 2-8 must be digits: {nie}")

        # Validate checksum letter
        if not letter.isalpha():
            raise ValueError(f"Last character must be a letter: {nie}")

        # Verify checksum
        # Replace prefix with its numeric value for checksum calculation
        checksum_number = int(str(self.VALID_PREFIXES[prefix]) + number_part)
        expected_letter = self.CHECKSUM_LETTERS[checksum_number % 23]

        if letter != expected_letter:
            raise ValueError(
                f"Invalid NIE checksum. Expected letter '{expected_letter}', "
                f"got '{letter}'"
            )

        return urn
```

**international_urns_es/utils.py:**

```python
"""Utility functions for Spanish document validation."""

__all__ = ["normalize_spanish_id"]


def normalize_spanish_id(id_value: str) -> str:
    """Normalize Spanish ID by removing common formatting.

    :param id_value: The ID value to normalize
    :type id_value: str
    :return: Normalized ID value
    :rtype: str
    """
    # Remove spaces, hyphens, and dots
    normalized = id_value.replace(' ', '').replace('-', '').replace('.', '')
    return normalized.upper()
```

## Testing Your Plugin

### Unit Tests

**tests/test_dni.py:**

```python
"""Tests for DNI validator."""

import pytest
from international_urns_es import DNIValidator


class TestDNIValidator:
    """Test suite for DNI validator."""

    @pytest.fixture
    def validator(self):
        """Create DNI validator instance."""
        return DNIValidator()

    @pytest.mark.parametrize("dni,expected", [
        ("urn:es:dni:12345678Z", "urn:es:dni:12345678Z"),
        ("urn:es:dni:00000000T", "urn:es:dni:00000000T"),
        ("urn:es:dni:99999999R", "urn:es:dni:99999999R"),
    ])
    def test_valid_dni(self, validator, dni, expected):
        """Test validation of valid DNI URNs."""
        result = validator.validate(dni)
        assert result == expected

    @pytest.mark.parametrize("invalid_dni,error_match", [
        ("not-a-urn", "Invalid URN format"),
        ("urn:es:dni:1234567", "must be 9 characters"),
        ("urn:es:dni:123456789", "must be digits"),  # No letter
        ("urn:es:dni:ABCDEFGHI", "must be digits"),  # All letters
        ("urn:es:dni:12345678X", "Invalid DNI checksum"),  # Wrong checksum
    ])
    def test_invalid_dni(self, validator, invalid_dni, error_match):
        """Test rejection of invalid DNI URNs."""
        with pytest.raises(ValueError, match=error_match):
            validator.validate(invalid_dni)

    def test_case_insensitive_letter(self, validator):
        """Test that checksum letter is case-insensitive."""
        result_upper = validator.validate("urn:es:dni:12345678Z")
        result_lower = validator.validate("urn:es:dni:12345678z")
        assert result_upper == result_lower

    def test_auto_registration(self):
        """Test that validator auto-registers with the registry."""
        import international_urns as iurns

        assert iurns.has_validator('es', 'dni')
        validator = iurns.get_validator('es', 'dni')
        assert validator is not None
```

### Integration Tests

**tests/test_integration.py:**

```python
"""Integration tests with international_urns."""

import pytest
import international_urns as iurns


class TestPluginIntegration:
    """Test plugin integration with core library."""

    def test_plugin_loaded(self):
        """Test that plugin validators are registered."""
        validators = iurns.list_validators()

        # Check that Spanish validators are registered
        assert ('es', 'dni') in validators
        assert ('es', 'nie') in validators

    def test_get_dni_validator(self):
        """Test getting DNI validator from registry."""
        validator = iurns.get_validator('es', 'dni')
        result = validator('urn:es:dni:12345678Z')
        assert result == 'urn:es:dni:12345678Z'

    def test_get_nie_validator(self):
        """Test getting NIE validator from registry."""
        validator = iurns.get_validator('es', 'nie')
        result = validator('urn:es:nie:X1234567L')
        assert result == 'urn:es:nie:X1234567L'

    def test_normalization_with_validation(self):
        """Test normalization combined with validation."""
        normalizer = iurns.create_normalizer()
        validator = iurns.get_validator('es', 'dni')

        urn = "URN:ES:DNI:12345678Z"
        normalized = normalizer(urn)
        validated = validator(normalized)

        assert normalized == "urn:es:dni:12345678Z"
        assert validated == "urn:es:dni:12345678Z"
```

## Best Practices

### 1. Follow Code Standards

```python
from international_urns import URNValidator

__all__ = ["MyValidator"]  # Always define __all__


class MyValidator(URNValidator):
    """Brief description.

    Detailed description of what this validator does,
    including format requirements and examples.

    :Example:

        >>> validator = MyValidator()
        >>> validator.validate('urn:xx:type:value')
        'urn:xx:type:value'
    """

    country_code = "xx"  # Must be ISO 3166-1 Alpha-2
    document_types = ["type"]

    def validate(self, urn: str) -> str:
        """Validate URN.

        :param urn: The URN string to validate
        :type urn: str
        :return: The validated URN string
        :rtype: str
        :raises ValueError: If the URN is invalid
        """
        # Implementation
        return urn
```

### 2. Provide Clear Error Messages

```python
def validate(self, urn: str) -> str:
    parts = urn.split(':')

    if len(parts) != 4:
        raise ValueError(
            f"Invalid URN format. Expected 'urn:country:type:value', got: {urn}"
        )

    document_value = parts[3]

    if len(document_value) != 10:
        raise ValueError(
            f"Document value must be exactly 10 characters. "
            f"Got {len(document_value)} characters: {document_value}"
        )

    return urn
```

### 3. Use Helper Methods

```python
class WellStructuredValidator(URNValidator):
    country_code = "xx"
    document_types = ["well"]

    def validate(self, urn: str) -> str:
        parts = self._parse_urn(urn)
        value = parts[3]

        self._validate_format(value)
        self._validate_checksum(value)

        return urn

    def _parse_urn(self, urn: str) -> list[str]:
        """Parse and validate URN structure."""
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")
        return parts

    def _validate_format(self, value: str) -> None:
        """Validate document value format."""
        if not value.isalnum():
            raise ValueError(f"Value must be alphanumeric: {value}")

    def _validate_checksum(self, value: str) -> None:
        """Validate document checksum."""
        # Checksum validation logic
        pass
```

### 4. Write Comprehensive Tests

```python
import pytest

@pytest.mark.parametrize("valid_urn", [
    "urn:xx:type:value1",
    "urn:xx:type:value2",
    "URN:XX:TYPE:VALUE3",  # Test case-insensitivity
])
def test_valid_urns(validator, valid_urn):
    """Test that valid URNs pass validation."""
    result = validator.validate(valid_urn)
    assert result == valid_urn


@pytest.mark.parametrize("invalid_urn,error_substring", [
    ("not-a-urn", "Invalid URN format"),
    ("urn:xx:type", "must have 4 parts"),
    ("urn:xx:type:!@#$", "must be alphanumeric"),
])
def test_invalid_urns(validator, invalid_urn, error_substring):
    """Test that invalid URNs raise ValueError."""
    with pytest.raises(ValueError, match=error_substring):
        validator.validate(invalid_urn)
```

## Publishing Your Plugin

### 1. Prepare for Distribution

**README.md:**

```markdown
# International URNs - Spanish Documents

Spanish document validators for the International URNs library.

## Installation

```bash
pip install international-urns-es
```

## Supported Documents

- **DNI**: Documento Nacional de Identidad
- **NIE**: Número de Identidad de Extranjero

## Usage

```python
import international_urns as iurns

# DNI validation
dni_validator = iurns.get_validator('es', 'dni')
result = dni_validator('urn:es:dni:12345678Z')

# NIE validation
nie_validator = iurns.get_validator('es', 'nie')
result = nie_validator('urn:es:nie:X1234567L')
```

## License

MIT License
```

### 2. Build and Publish

```bash
# Install build tools
pip install build twine

# Run tests
pytest

# Build distribution
python -m build

# Upload to PyPI (test first!)
twine upload --repository testpypi dist/*

# Upload to production PyPI
twine upload dist/*
```

### 3. Version Your Package

Follow semantic versioning:

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backwards-compatible
- **Patch** (0.0.1): Bug fixes

## Multi-Country Plugins

You can create plugins that support multiple countries:

```python
# international_urns_eu/__init__.py

from .french import FrenchNIRValidator
from .german import GermanIDValidator
from .italian import ItalianCFValidator

__all__ = [
    "FrenchNIRValidator",
    "GermanIDValidator",
    "ItalianCFValidator",
]
```

**pyproject.toml:**

```toml
[project.entry-points.'international_urns.plugins']
eu = 'international_urns_eu'
```

## Example: Complete Plugin

See the `international-urns-es` package structure above for a complete, production-ready example of a validator plugin.

## Plugin Checklist

Before publishing your plugin:

- [ ] Country code is valid ISO 3166-1 Alpha-2 (or "--")
- [ ] All validators have Sphinx-style docstrings
- [ ] `__all__` is defined in all modules
- [ ] Full type hints on all methods
- [ ] Comprehensive test coverage (>90%)
- [ ] Clear error messages
- [ ] Entry point correctly registered
- [ ] README with usage examples
- [ ] License file included
- [ ] Version number follows semver
- [ ] Tests pass with pytest
- [ ] Code passes ruff and mypy checks
