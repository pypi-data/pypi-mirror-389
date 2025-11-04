# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

International URNs is a microkernel-based Python library for validating country-specific URN (Uniform Resource Name) formats. URNs use the format `urn:country_code:document_type:document_value` where country codes follow ISO 3166-1 Alpha-2 standards (e.g., `urn:es:dni:12345678X`).

### Key Architecture Principles

**Microkernel Design**: The core library (`international_urns`) provides the validation framework and plugin infrastructure. Country-specific validators are provided by separate plugin packages (e.g., `international-urns-es` for Spanish documents).

**Auto-registration via `__init_subclass__`**: Validators automatically register themselves when their class is defined by inheriting from `URNValidator` and specifying `country_code` and `document_types` class attributes. This happens through the `__init_subclass__` hook.

**Plugin Discovery**: External plugins are discovered via Python entry points in the `international_urns.plugins` group. On import, the library scans for and loads all registered plugins using `importlib.metadata.entry_points()`.

**Case Sensitivity**: The URN scheme ('urn'), country code (NID), and document type (first NSS segment) are case-insensitive. The remainder of the NSS preserves its original case.

## Development Commands

### Setup

```bash
# Install dependencies with uv
uv pip install -e ".[test]"
```

### Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=international_urns --cov-report=html

# Run a specific test file
pytest tests/test_registry.py

# Run a specific test function
pytest tests/test_registry.py::test_registry_register_validator

# Run tests matching a pattern
pytest -k "wildcard"
```

### Linting and Type Checking

```bash
# Run ruff for linting and formatting
ruff check .
ruff format .

# Run mypy for type checking
mypy international_urns
```

### Building

```bash
# Build the package with hatch
hatch build

# Build and publish (use --dry-run for testing)
hatch publish --dry-run
```

## Core Architecture

### Module Structure

- **`registry.py`**: Central `URNRegistry` singleton that maps `(country_code, document_type)` tuples to validator functions. Enforces uniqueness constraints.

- **`base.py`**: Defines `URNValidator` abstract base class with `__init_subclass__` hook for automatic registration. Validators must implement the `validate(self, urn: str) -> str` method.

- **`validators.py`**: Public API functions (`get_validator`, `list_validators`, `has_validator`) for accessing registered validators.

- **`normalization.py`**: Provides `normalize_urn()` function and `create_normalizer()` factory for use with Pydantic's `BeforeValidator`.

- **`builtin.py`**: Contains `WildcardValidator` for the `urn:--:--:...` format that accepts any string matching `^urn:.+:.+:.+$`.

- **`discovery.py`**: Implements plugin loading via `importlib.metadata.entry_points()`. Scans the `international_urns.plugins` group and imports each plugin module.

### Registration Flow

1. When a `URNValidator` subclass is defined, `__init_subclass__` is triggered
2. For each `document_type` in the class's `document_types` list, an instance is created
3. The instance's `validate` method is registered with the global registry for `(country_code, document_type)`
4. The registry enforces uniqueness - duplicate registration raises `ValueError`

### Validation Flow

1. User calls `get_validator(country_code, document_type)`
2. Registry lookup returns the validator function or raises `ValueError` if not found
3. Validator function accepts URN string, validates it, and returns the (possibly normalized) URN
4. Invalid URNs should raise `ValueError` with a descriptive message

### Pydantic Integration Pattern

```python
from pydantic import BaseModel, AfterValidator, BeforeValidator
from typing_extensions import Annotated
import international_urns as iurns

class Document(BaseModel):
    urn: Annotated[
        str,
        BeforeValidator(iurns.create_normalizer()),
        AfterValidator(iurns.get_validator('es', 'dni'))
    ]
```

## Creating Plugins

External plugins should:

1. Create a separate package (e.g., `international-urns-es`)
2. Define validators by subclassing `URNValidator`:

```python
from international_urns import URNValidator

class SpanishDNIValidator(URNValidator):
    country_code = "es"
    document_types = ["dni", "nie"]

    def validate(self, urn: str) -> str:
        # Validation logic here
        # Raise ValueError if invalid
        return urn
```

3. Register the plugin via entry points in `pyproject.toml`:

```toml
[project.entry-points.'international_urns.plugins']
es = 'international_urns_es'
```

4. When the plugin module is imported, validators auto-register via `__init_subclass__`

## Testing Guidelines

- Use `pytest.mark.parametrize` for testing multiple input cases
- Mock the registry for isolated unit tests
- Test both valid and invalid inputs for validators
- Verify case-insensitivity for country codes and document types
- Verify case preservation for NSS remainder
- Test Pydantic integration with `pytest.importorskip("pydantic")`

## Code Standards

- **Docstrings**: All modules use Sphinx-style docstrings with `:param:`, `:type:`, `:return:`, `:rtype:`, and `:raises:` directives
- **Module exports**: Each module defines `__all__` to explicitly declare public API
- **ISO 3166-1 Alpha-2 enforcement**: Country codes must be exactly 2 alphabetic characters or "--" (wildcard)
- **Type hints**: Full type annotations on all functions and methods
- **No obvious comments**: Code should be self-documenting; avoid redundant inline comments

## Important Notes

- **No `src/` directory**: Package lives directly in `international_urns/` at repository root
- **Dynamic versioning**: Version is read from `international_urns/__init__.py` via hatch
- **Python 3.11+**: Minimum supported version is Python 3.11
- **Wildcard format**: The `urn:--:--:...` format only validates when explicitly requested, not as a fallback
- **Registry is global**: There's a single global registry instance accessed via `get_registry()`
- **Entry point group**: Plugins must use the `international_urns.plugins` entry point group
- **Country code validation**: The registry validates that country codes are valid ISO 3166-1 Alpha-2 format (2 letters) or "--" at registration time
