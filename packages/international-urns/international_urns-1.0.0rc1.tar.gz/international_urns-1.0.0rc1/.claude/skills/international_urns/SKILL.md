# International URNs Skills

This skill helps you work with the International URNs library, a microkernel-based Python library for validating country-specific URN formats.

## Overview

International URNs validates URNs using the format: `urn:country_code:document_type:document_value`

- **Country codes**: ISO 3166-1 Alpha-2 (exactly 2 letters) or "--" (wildcard)
- **Case handling**: URN scheme, country code, and document type are case-insensitive; document value preserves case
- **Architecture**: Microkernel design with plugin-based validators

## Quick Start

### Import Convention

Always use the abbreviated alias for imports:

```python
import international_urns as iurns
```

### Basic Validation

Get a validator for a specific country and document type:

```python
import international_urns as iurns

# Get a validator
validator = iurns.get_validator('es', 'dni')

# Validate a URN
result = validator('urn:es:dni:12345678X')
```

### Normalization

Normalize URN case-insensitive parts to lowercase:

```python
import international_urns as iurns

normalized = iurns.normalize_urn("URN:ES:DNI:12345678X")
# Returns: "urn:es:dni:12345678X"
```

### Registry Introspection

```python
import international_urns as iurns

# List all available validators
validators = iurns.list_validators()

# Check if a validator exists
if iurns.has_validator('es', 'dni'):
    validator = iurns.get_validator('es', 'dni')
```

## Code Standards

When working with this library:

1. **Country codes**: Must be exactly 2 alphabetic characters (ISO 3166-1 Alpha-2) or "--"
2. **Docstrings**: Use Sphinx style with `:param:`, `:type:`, `:return:`, `:rtype:`, `:raises:`
3. **Type hints**: All functions must have full type annotations
4. **Module exports**: Define `__all__` in every module
5. **Error handling**: Raise `ValueError` with descriptive messages for invalid URNs

## Available Instruction Files

- `examples.md` - Common usage patterns and examples
- `advanced.md` - Advanced usage, custom validators, and registry management
- `plugin_development.md` - Creating and distributing validator plugins
- `pydantic_integration.md` - Integration with Pydantic models

## Common Tasks

### Create a Simple Validator

```python
from international_urns import URNValidator

class MyValidator(URNValidator):
    country_code = "xx"  # ISO 3166-1 Alpha-2
    document_types = ["passport", "id"]

    def validate(self, urn: str) -> str:
        # Validation logic
        if not self._is_valid(urn):
            raise ValueError(f"Invalid URN: {urn}")
        return urn

    def _is_valid(self, urn: str) -> bool:
        # Custom validation
        return True
```

### Testing Validators

```python
import pytest

def test_validator():
    validator = MyValidator()

    # Test valid URN
    result = validator.validate('urn:xx:passport:ABC123')
    assert result == 'urn:xx:passport:ABC123'

    # Test invalid URN
    with pytest.raises(ValueError):
        validator.validate('invalid')
```

## Key Modules

- `registry.py` - Central registry with `URNRegistry` class and `get_registry()` function
- `base.py` - `URNValidator` abstract base class with auto-registration
- `validators.py` - Public API: `get_validator()`, `list_validators()`, `has_validator()`
- `normalization.py` - `normalize_urn()` and `create_normalizer()` functions
- `builtin.py` - `WildcardValidator` for `urn:--:--:...` format
- `discovery.py` - `load_plugins()` for entry point discovery

## Development Commands

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=international_urns --cov-report=html

# Lint
ruff check .

# Type check
mypy international_urns
```

## Need More Help?

- For examples and usage patterns, see `examples.md`
- For advanced features, see `advanced.md`
- For creating plugins, see `plugin_development.md`
- For Pydantic integration, see `pydantic_integration.md`
