# International URNs - Advanced Usage

Advanced patterns and techniques for working with the International URNs library.

## Direct Registry Access

### Working with the Registry Singleton

```python
from international_urns.registry import get_registry

# Get the global registry
registry = get_registry()

# Register a validator manually (without using URNValidator base class)
def my_custom_validator(urn: str) -> str:
    if not urn.startswith('urn:xx:custom:'):
        raise ValueError(f"Invalid URN: {urn}")
    return urn

registry.register('xx', 'custom', my_custom_validator)

# Now you can use it
validator = registry.get_validator('xx', 'custom')
result = validator('urn:xx:custom:12345')
```

### Registry Introspection

```python
from international_urns.registry import get_registry

registry = get_registry()

# List all validators
all_validators = registry.list_validators()
print(f"Total validators: {len(all_validators)}")

# Check specific validators
if registry.has_validator('es', 'dni'):
    print("Spanish DNI validator is available")

# Get validator or None (no exception)
validator = registry.get_validator('unknown', 'type')
if validator is None:
    print("Validator not found")
```

## Custom Validation Strategies

### Composition Pattern

```python
from international_urns import URNValidator
from typing import Callable

class ComposableValidator(URNValidator):
    country_code = "xx"
    document_types = ["composite"]

    def __init__(self):
        super().__init__()
        self.validators: list[Callable[[str], bool]] = []

    def add_check(self, validator: Callable[[str], bool]) -> None:
        """Add a validation check to the chain."""
        self.validators.append(validator)

    def validate(self, urn: str) -> str:
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        doc_value = parts[3]

        # Run all validation checks
        for check in self.validators:
            if not check(doc_value):
                raise ValueError(f"Validation failed for: {doc_value}")

        return urn

# Usage
validator = ComposableValidator()
validator.add_check(lambda v: len(v) >= 8)
validator.add_check(lambda v: v.isalnum())
validator.add_check(lambda v: any(c.isdigit() for c in v))

result = validator.validate('urn:xx:composite:ABC12345')
```

### Strategy Pattern for Multiple Formats

```python
from international_urns import URNValidator
from abc import ABC, abstractmethod

class ValidationStrategy(ABC):
    @abstractmethod
    def is_valid(self, value: str) -> bool:
        pass

    @abstractmethod
    def get_error_message(self, value: str) -> str:
        pass

class NumericStrategy(ValidationStrategy):
    def __init__(self, length: int):
        self.length = length

    def is_valid(self, value: str) -> bool:
        return value.isdigit() and len(value) == self.length

    def get_error_message(self, value: str) -> str:
        return f"Must be {self.length} digits"

class AlphanumericStrategy(ValidationStrategy):
    def __init__(self, min_length: int, max_length: int):
        self.min_length = min_length
        self.max_length = max_length

    def is_valid(self, value: str) -> bool:
        return (
            value.isalnum() and
            self.min_length <= len(value) <= self.max_length
        )

    def get_error_message(self, value: str) -> str:
        return f"Must be {self.min_length}-{self.max_length} alphanumeric characters"

class FlexibleValidator(URNValidator):
    country_code = "xx"
    document_types = ["flex"]

    def __init__(self):
        super().__init__()
        self.strategies: dict[str, ValidationStrategy] = {
            'numeric': NumericStrategy(10),
            'alphanum': AlphanumericStrategy(8, 12),
        }

    def validate(self, urn: str) -> str:
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        doc_value = parts[3]

        # Detect which strategy to use (could be based on format, prefix, etc.)
        strategy = self._select_strategy(doc_value)

        if not strategy.is_valid(doc_value):
            raise ValueError(strategy.get_error_message(doc_value))

        return urn

    def _select_strategy(self, value: str) -> ValidationStrategy:
        if value.isdigit():
            return self.strategies['numeric']
        return self.strategies['alphanum']
```

## Advanced Normalization

### Custom Normalization Functions

```python
import re
import international_urns as iurns

def normalize_and_uppercase_value(urn: str) -> str:
    """Normalize URN and uppercase the document value."""
    normalized = iurns.normalize_urn(urn)
    parts = normalized.split(':')

    if len(parts) == 4:
        parts[3] = parts[3].upper()
        return ':'.join(parts)

    return normalized

# Usage
urn = "URN:ES:DNI:abc123"
result = normalize_and_uppercase_value(urn)
print(result)  # Output: "urn:es:dni:ABC123"
```

### Normalization with Stripping

```python
import international_urns as iurns

def normalize_and_strip(urn: str) -> str:
    """Normalize URN and strip whitespace from all parts."""
    # Strip whitespace first
    stripped = ':'.join(part.strip() for part in urn.split(':'))

    # Then normalize
    return iurns.normalize_urn(stripped)

# Usage
urn = " URN : ES : DNI : 12345678X "
result = normalize_and_strip(urn)
print(result)  # Output: "urn:es:dni:12345678X"
```

## Validation Caching

### Memoized Validator

```python
from functools import lru_cache
from international_urns import URNValidator

class CachedValidator(URNValidator):
    country_code = "xx"
    document_types = ["cached"]

    @lru_cache(maxsize=1000)
    def validate(self, urn: str) -> str:
        # Expensive validation logic here
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        doc_value = parts[3]

        # Simulate expensive check
        if not self._expensive_check(doc_value):
            raise ValueError(f"Failed expensive validation: {doc_value}")

        return urn

    def _expensive_check(self, value: str) -> bool:
        # Simulate expensive operation (e.g., database lookup, API call)
        return len(value) >= 5

# Note: Cache is per instance, so use singleton pattern for global cache
_cached_validator_instance = None

def get_cached_validator():
    global _cached_validator_instance
    if _cached_validator_instance is None:
        _cached_validator_instance = CachedValidator()
    return _cached_validator_instance
```

## Batch Validation

### Parallel Validation

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import international_urns as iurns
from typing import Iterator

def validate_batch_parallel(
    urns: list[str],
    country: str,
    doc_type: str,
    max_workers: int = 4
) -> Iterator[tuple[str, bool, str]]:
    """Validate multiple URNs in parallel."""
    validator = iurns.get_validator(country, doc_type)

    def validate_one(urn: str) -> tuple[str, bool, str]:
        try:
            result = validator(urn)
            return (urn, True, result)
        except ValueError as e:
            return (urn, False, str(e))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(validate_one, urn): urn for urn in urns}

        for future in as_completed(futures):
            yield future.result()

# Usage
urns = [f'urn:es:dni:1234567{i}X' for i in range(10)]
results = list(validate_batch_parallel(urns, 'es', 'dni'))
valid_count = sum(1 for _, valid, _ in results if valid)
print(f"Valid: {valid_count}/{len(urns)}")
```

### Batch with Early Stopping

```python
import international_urns as iurns

def validate_until_error(
    urns: list[str],
    country: str,
    doc_type: str
) -> tuple[int, str | None]:
    """Validate URNs until first error, return count and error."""
    validator = iurns.get_validator(country, doc_type)

    for i, urn in enumerate(urns):
        try:
            validator(urn)
        except ValueError as e:
            return i, str(e)

    return len(urns), None

# Usage
urns = ['urn:es:dni:valid1', 'urn:es:dni:valid2', 'invalid', 'urn:es:dni:valid3']
count, error = validate_until_error(urns, 'es', 'dni')
print(f"Validated {count} URNs before error: {error}")
```

## Dynamic Validator Loading

### Runtime Validator Creation

```python
from international_urns import URNValidator
from typing import Callable

def create_validator_class(
    country: str,
    doc_types: list[str],
    validation_func: Callable[[str], bool],
    error_message: str = "Validation failed"
):
    """Dynamically create a validator class at runtime."""

    class DynamicValidator(URNValidator):
        country_code = country
        document_types = doc_types

        def validate(self, urn: str) -> str:
            parts = urn.split(':')
            if len(parts) != 4:
                raise ValueError(f"Invalid URN format: {urn}")

            if not validation_func(parts[3]):
                raise ValueError(f"{error_message}: {parts[3]}")

            return urn

    return DynamicValidator

# Usage
ValidatorClass = create_validator_class(
    country='yy',
    doc_types=['dynamic'],
    validation_func=lambda v: len(v) == 10 and v.isalnum(),
    error_message="Must be 10 alphanumeric characters"
)

validator = ValidatorClass()
result = validator.validate('urn:yy:dynamic:ABC1234567')
```

## URN Parsing and Analysis

### URN Component Extraction

```python
import re
from typing import NamedTuple

class URNComponents(NamedTuple):
    scheme: str
    country_code: str
    document_type: str
    document_value: str
    is_valid_format: bool

def parse_urn(urn: str) -> URNComponents:
    """Parse URN into components."""
    pattern = r'^(urn):([^:]+):([^:]+):(.+)$'
    match = re.match(pattern, urn, re.IGNORECASE)

    if match:
        scheme, country, doc_type, value = match.groups()
        return URNComponents(
            scheme=scheme.lower(),
            country_code=country.lower(),
            document_type=doc_type.lower(),
            document_value=value,
            is_valid_format=True
        )
    else:
        return URNComponents('', '', '', '', False)

# Usage
components = parse_urn('urn:es:dni:12345678X')
print(f"Country: {components.country_code}")
print(f"Type: {components.document_type}")
print(f"Value: {components.document_value}")
```

### URN Statistics

```python
import international_urns as iurns
from collections import Counter
from typing import Iterator

def analyze_urns(urns: list[str]) -> dict:
    """Analyze a collection of URNs."""
    valid_count = 0
    invalid_count = 0
    countries = Counter()
    doc_types = Counter()
    errors = Counter()

    for urn in urns:
        try:
            components = parse_urn(urn)
            if not components.is_valid_format:
                invalid_count += 1
                errors['Invalid format'] += 1
                continue

            countries[components.country_code] += 1
            doc_types[components.document_type] += 1

            # Try to validate if validator exists
            if iurns.has_validator(components.country_code, components.document_type):
                validator = iurns.get_validator(
                    components.country_code,
                    components.document_type
                )
                validator(urn)
                valid_count += 1
            else:
                invalid_count += 1
                errors['No validator'] += 1

        except ValueError as e:
            invalid_count += 1
            errors[str(e)] += 1

    return {
        'total': len(urns),
        'valid': valid_count,
        'invalid': invalid_count,
        'countries': dict(countries),
        'document_types': dict(doc_types),
        'errors': dict(errors)
    }

# Usage
urns = [
    'urn:es:dni:12345678X',
    'urn:fr:nir:123456789012345',
    'invalid-urn',
    'urn:unknown:type:value',
]
stats = analyze_urns(urns)
print(f"Valid: {stats['valid']}/{stats['total']}")
print(f"Countries: {stats['countries']}")
print(f"Errors: {stats['errors']}")
```

## Testing Utilities

### Test Fixtures

```python
import pytest
from international_urns import URNValidator

@pytest.fixture
def sample_validator():
    """Create a sample validator for testing."""
    class SampleValidator(URNValidator):
        country_code = "zz"
        document_types = ["test"]

        def validate(self, urn: str) -> str:
            parts = urn.split(':')
            if len(parts) != 4:
                raise ValueError(f"Invalid format: {urn}")
            if not parts[3].isalnum():
                raise ValueError(f"Value must be alphanumeric: {parts[3]}")
            return urn

    return SampleValidator()

@pytest.fixture
def valid_urns():
    """Provide valid test URNs."""
    return [
        'urn:zz:test:ABC123',
        'urn:zz:test:XYZ789',
        'urn:zz:test:TEST001',
    ]

@pytest.fixture
def invalid_urns():
    """Provide invalid test URNs."""
    return [
        'not-a-urn',
        'urn:zz:test',
        'urn:zz:test:ABC-123',  # Contains hyphen
        'urn:zz:test:ABC 123',  # Contains space
    ]

# Usage in tests
def test_valid_urns(sample_validator, valid_urns):
    for urn in valid_urns:
        result = sample_validator.validate(urn)
        assert result == urn

def test_invalid_urns(sample_validator, invalid_urns):
    for urn in invalid_urns:
        with pytest.raises(ValueError):
            sample_validator.validate(urn)
```

### Mock Validators for Testing

```python
from unittest.mock import Mock
from international_urns.registry import get_registry

def setup_mock_validator(country: str, doc_type: str, return_value: str = None):
    """Register a mock validator for testing."""
    mock_validator = Mock()

    if return_value:
        mock_validator.return_value = return_value
    else:
        mock_validator.side_effect = lambda urn: urn

    registry = get_registry()
    registry.register(country, doc_type, mock_validator)

    return mock_validator

# Usage in tests
def test_with_mock():
    mock = setup_mock_validator('zz', 'mock', 'mocked-result')

    import international_urns as iurns
    validator = iurns.get_validator('zz', 'mock')
    result = validator('any-urn')

    assert result == 'mocked-result'
    mock.assert_called_once_with('any-urn')
```
