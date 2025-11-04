# International URNs Skills - Quick Reference

Quick navigation for International URNs library skills.

## Skill Files

### 📘 [SKILLS.md](SKILLS.md) - Getting Started
**Use this for:** Basic usage, quick start, and general overview

Topics covered:
- Import conventions (`import international_urns as iurns`)
- Basic validation and normalization
- Registry introspection
- Code standards
- Development commands
- Module overview

### 📚 [examples.md](examples.md) - Common Patterns
**Use this for:** Practical examples and usage patterns

Topics covered:
- Basic validation examples
- Normalization examples
- Wildcard validator usage
- Registry introspection examples
- Creating custom validators
- Error handling patterns
- Testing examples
- Integration with logging and data processing

### 🚀 [advanced.md](advanced.md) - Advanced Techniques
**Use this for:** Complex scenarios and advanced patterns

Topics covered:
- Direct registry access
- Custom validation strategies (composition, strategy patterns)
- Advanced normalization techniques
- Validation caching
- Batch validation (sequential and parallel)
- Dynamic validator loading
- URN parsing and analysis
- Testing utilities and fixtures

### 🔌 [plugin_development.md](plugin_development.md) - Creating Plugins
**Use this for:** Building and distributing validator plugins

Topics covered:
- Plugin architecture overview
- Package structure and configuration
- Implementing validators
- Testing plugins
- Best practices and code standards
- Publishing to PyPI
- Multi-country plugins
- Complete plugin examples

### 🔗 [pydantic_integration.md](pydantic_integration.md) - Pydantic Integration
**Use this for:** Using International URNs with Pydantic models

Topics covered:
- Basic integration with AfterValidator/BeforeValidator
- Multiple URN fields
- Custom validators and error messages
- Conditional validation
- Working with lists
- Integration with Pydantic Settings
- Database integration (SQLModel)
- FastAPI integration
- Testing Pydantic models
- Performance optimization

## Quick Command Reference

```bash
# Development
pytest                          # Run tests
pytest --cov=international_urns # Run with coverage
ruff check .                    # Lint code
mypy international_urns         # Type check

# Installation
pip install international-urns              # Install library
pip install international-urns[test]        # Install with test deps
uv pip install -e ".[test]"                 # Install in dev mode
```

## Common Code Snippets

### Basic Validation
```python
import international_urns as iurns

validator = iurns.get_validator('es', 'dni')
result = validator('urn:es:dni:12345678Z')
```

### With Pydantic
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
```

### Creating a Validator
```python
from international_urns import URNValidator

class MyValidator(URNValidator):
    country_code = "xx"  # ISO 3166-1 Alpha-2
    document_types = ["type"]

    def validate(self, urn: str) -> str:
        # Validation logic
        return urn
```

## Need Help?

1. **Getting started?** → Start with [SKILLS.md](SKILLS.md)
2. **Need examples?** → Check [examples.md](examples.md)
3. **Building a plugin?** → See [plugin_development.md](plugin_development.md)
4. **Using with Pydantic?** → Read [pydantic_integration.md](pydantic_integration.md)
5. **Advanced use cases?** → Explore [advanced.md](advanced.md)
