# International URNs

A microkernel-based Python library for validating country-specific URN (Uniform Resource Name) formats.

## Overview

International URNs provides a pluggable architecture for validating URNs associated with countries using ISO 3166-1 Alpha-2 codes. The library uses a microkernel design where country-specific validators are provided by separate plugin packages.

**URN Format:** `urn:country_code:document_type:document_value`

**Example:** `urn:es:dni:12345678X`

## Features

- **Microkernel Architecture**: Core library provides the framework, plugins provide country-specific validation
- **Auto-registration**: Validators automatically register themselves using Python's `__init_subclass__`
- **Entry Point Discovery**: Plugins are discovered and loaded via Python entry points
- **ISO 3166-1 Alpha-2 Enforcement**: Country codes are validated to be exactly 2 letters or "--" (wildcard)
- **Pydantic Integration**: Seamless integration with Pydantic's `BeforeValidator` and `AfterValidator`
- **Case-Insensitive**: URN scheme, country codes, and document types are case-insensitive (NSS remainder preserves case)
- **Type-Safe**: Full type hints with mypy support
- **Extensible**: Easy to add new country and document type validators

## Installation

```bash
pip install international-urns
```

For development:

```bash
# Create virtual environment and install with test dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[test]"
```

## Usage

> **Note:** Examples use `iurns` as an abbreviated import alias for convenience.

### Basic Validation with Pydantic

```python
from pydantic import BaseModel, AfterValidator, BeforeValidator
from typing import Annotated
import international_urns as iurns

class Document(BaseModel):
    urn: Annotated[
        str,
        BeforeValidator(iurns.create_normalizer()),
        AfterValidator(iurns.get_validator('es', 'dni'))
    ]

# Validates and normalizes the URN
doc = Document(urn="URN:ES:DNI:12345678X")
print(doc.urn)  # Output: "urn:es:dni:12345678X"
```

### Normalization

URN normalization converts the scheme, country code, and document type to lowercase while preserving the case of the document value:

```python
import international_urns as iurns

normalized = iurns.normalize_urn("URN:ES:DNI:12345678X")
print(normalized)  # Output: "urn:es:dni:12345678X"
```

### Wildcard Validator

The library includes a built-in wildcard validator that accepts any URN matching the pattern `urn:--:--:...`:

```python
import international_urns as iurns

validator = iurns.get_validator('--', '--')
result = validator('urn:--:--:anything')  # Valid
```

### Registry Introspection

```python
import international_urns as iurns

# List all available validators
validators = iurns.list_validators()
print(validators)  # [('--', '--'), ('es', 'dni'), ...]

# Check if a validator exists
if iurns.has_validator('es', 'dni'):
    validator = iurns.get_validator('es', 'dni')
    result = validator('urn:es:dni:12345678X')
```

## Creating Plugins

To create a plugin for a new country or document type:

### 1. Create a new package

Example: `international-urns-es` for Spanish documents

### 2. Define validators

Subclass `URNValidator` and specify the country code (ISO 3166-1 Alpha-2) and document types:

```python
from international_urns import URNValidator

class SpanishDNIValidator(URNValidator):
    country_code = "es"  # Must be 2 letters or "--"
    document_types = ["dni", "nie"]

    def validate(self, urn: str) -> str:
        # Implement validation logic
        # Raise ValueError if invalid
        # Return the URN (possibly normalized) if valid

        if not self._check_dni_format(urn):
            raise ValueError(f"Invalid DNI format: {urn}")

        return urn

    def _check_dni_format(self, urn: str) -> bool:
        # Custom validation logic here
        return True
```

### 3. Register via entry points

In your plugin's `pyproject.toml`:

```toml
[project.entry-points.'international_urns.plugins']
es = 'international_urns_es'
```

The validator will automatically register itself when the plugin is imported.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=international_urns --cov-report=html

# Run specific test file
pytest tests/test_registry.py
```

### Linting and Type Checking

```bash
# Lint and format
ruff check .
ruff format .

# Type checking
mypy international_urns
```

## Requirements

- Python 3.11+
- urnparse

## License

MIT License - see LICENSE file for details
