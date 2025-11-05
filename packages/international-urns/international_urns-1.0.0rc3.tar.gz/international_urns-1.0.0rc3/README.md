# International URNs

A microkernel-based Python library for validating and generating country-specific URN (Uniform Resource Name) formats.

## Overview

International URNs provides a pluggable architecture for validating and generating URNs associated with countries using ISO 3166-1 Alpha-2 codes. The library uses a microkernel design where country-specific validators and generators are provided by separate plugin packages.

**URN Format:** `urn:country_code:document_type:document_value`

**Example:** `urn:es:dni:12345678X`

## Features

- **Microkernel Architecture**: Core library provides the framework, plugins provide country-specific validation and generation
- **Auto-registration**: Validators and generators automatically register themselves using Python's `__init_subclass__`
- **Entry Point Discovery**: Plugins are discovered and loaded via Python entry points
- **ISO 3166-1 Alpha-2 Enforcement**: Country codes are validated to be exactly 2 letters (or "--" for wildcard validators)
- **URN Generation**: Generate random valid URNs for testing and fixtures
- **Faker Integration**: Generators are compatible with Faker providers for easy test data generation
- **Pydantic Integration**: Seamless integration with Pydantic's `BeforeValidator` and `AfterValidator`
- **Case-Insensitive**: URN scheme, country codes, and document types are case-insensitive (NSS remainder preserves case)
- **Type-Safe**: Full type hints with mypy support
- **Extensible**: Easy to add new country and document type validators and generators

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

## URN Generation

The library provides generators for creating random valid URNs, useful for testing and fixtures.

### Basic Generation

```python
import international_urns as iurns

# Get a generator for a specific country and document type
dni_generator = iurns.get_generator('es', 'dni')

# Generate a random URN
urn = dni_generator()
print(urn)  # Output: "urn:es:dni:12345678Z" (random valid DNI)
```

### Generator Registry Introspection

```python
import international_urns as iurns

# List all available generators
generators = iurns.list_generators()
print(generators)  # [('es', 'dni'), ('es', 'nie'), ...]

# Check if a generator exists
if iurns.has_generator('es', 'dni'):
    gen = iurns.get_generator('es', 'dni')
    urn = gen()
```

### Faker Integration

Generators are designed to be compatible with [Faker](https://faker.readthedocs.io/) providers:

```python
from faker import Faker
from faker.providers import BaseProvider
import international_urns as iurns

class SpanishURNProvider(BaseProvider):
    def spanish_dni(self):
        return iurns.get_generator('es', 'dni')()

    def spanish_nie(self):
        return iurns.get_generator('es', 'nie')()

fake = Faker()
fake.add_provider(SpanishURNProvider)

# Generate random URNs
dni = fake.spanish_dni()
nie = fake.spanish_nie()
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
    country_code = "es"  # Must be 2 letters (or "--" for wildcard)
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

### 3. Define generators

Subclass `URNGenerator` to create random URNs. Note that wildcard ("--") is not supported for generators:

```python
from international_urns import URNGenerator
import random
import string

class SpanishDNIGenerator(URNGenerator):
    country_code = "es"  # Must be 2 letters (no wildcard for generators)
    document_types = ["dni", "nie"]

    def generate(self) -> str:
        # Generate a random valid URN
        # self.document_type contains the specific document type for this instance

        # Generate random DNI number (8 digits + letter)
        number = random.randint(10000000, 99999999)
        letter = random.choice(string.ascii_uppercase)

        return f"urn:{self.country_code}:{self.document_type}:{number}{letter}"
```

**Important**: When a generator class supports multiple document types, each registration creates a separate instance with `self.document_type` set to the appropriate value. Use `self.document_type` in your `generate()` method to create the correct URN format.

### 4. Register via entry points

In your plugin's `pyproject.toml`:

```toml
[project.entry-points.'international_urns.plugins']
es = 'international_urns_es'
```

Both validators and generators will automatically register themselves when the plugin is imported.

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
