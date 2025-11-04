# International URNs - Examples

Common usage patterns and examples for the International URNs library.

## Basic Usage

### Simple Validation

```python
import international_urns as iurns

# Get a validator for Spanish DNI
validator = iurns.get_validator('es', 'dni')

# Validate a URN
try:
    result = validator('urn:es:dni:12345678X')
    print(f"Valid URN: {result}")
except ValueError as e:
    print(f"Invalid URN: {e}")
```

### Normalization

```python
import international_urns as iurns

# Normalize case-insensitive parts to lowercase
urn = "URN:ES:DNI:12345678X"
normalized = iurns.normalize_urn(urn)
print(normalized)  # Output: "urn:es:dni:12345678X"

# Document value case is preserved
urn = "URN:ES:DNI:AbCdEf"
normalized = iurns.normalize_urn(urn)
print(normalized)  # Output: "urn:es:dni:AbCdEf"
```

### Using the Wildcard Validator

```python
import international_urns as iurns

# Get the wildcard validator
validator = iurns.get_validator('--', '--')

# Accepts any URN with the wildcard format
result = validator('urn:--:--:any-value-here')
print(result)  # Output: "urn:--:--:any-value-here"

# Only accepts URNs specifically with urn:--:--: prefix
try:
    validator('urn:es:dni:12345678X')  # Fails!
except ValueError as e:
    print(f"Error: {e}")
```

## Registry Introspection

### Listing Available Validators

```python
import international_urns as iurns

# Get all registered validators
validators = iurns.list_validators()
print("Available validators:")
for country, doc_type in validators:
    print(f"  - {country}:{doc_type}")
```

### Checking Validator Availability

```python
import international_urns as iurns

# Check before getting
if iurns.has_validator('es', 'dni'):
    validator = iurns.get_validator('es', 'dni')
    print("Validator available")
else:
    print("No validator for es:dni")

# Handle missing validators gracefully
def get_safe_validator(country: str, doc_type: str):
    try:
        return iurns.get_validator(country, doc_type)
    except ValueError:
        print(f"No validator for {country}:{doc_type}")
        return None
```

## Creating Custom Validators

### Simple Validator

```python
from international_urns import URNValidator

class PassportValidator(URNValidator):
    country_code = "us"
    document_types = ["passport"]

    def validate(self, urn: str) -> str:
        # Extract the passport number
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        passport_number = parts[3]

        # Validate format (example: 9 alphanumeric characters)
        if not (len(passport_number) == 9 and passport_number.isalnum()):
            raise ValueError(
                f"Invalid passport number format: {passport_number}"
            )

        return urn
```

### Validator with Multiple Document Types

```python
from international_urns import URNValidator

class MexicanDocumentValidator(URNValidator):
    country_code = "mx"
    document_types = ["curp", "rfc", "ine"]

    def validate(self, urn: str) -> str:
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        doc_type = parts[2].lower()
        doc_value = parts[3]

        if doc_type == "curp":
            return self._validate_curp(urn, doc_value)
        elif doc_type == "rfc":
            return self._validate_rfc(urn, doc_value)
        elif doc_type == "ine":
            return self._validate_ine(urn, doc_value)
        else:
            raise ValueError(f"Unknown document type: {doc_type}")

    def _validate_curp(self, urn: str, value: str) -> str:
        if len(value) != 18:
            raise ValueError(f"CURP must be 18 characters: {value}")
        return urn

    def _validate_rfc(self, urn: str, value: str) -> str:
        if len(value) not in (12, 13):
            raise ValueError(f"RFC must be 12 or 13 characters: {value}")
        return urn

    def _validate_ine(self, urn: str, value: str) -> str:
        if not value.isdigit() or len(value) != 13:
            raise ValueError(f"INE must be 13 digits: {value}")
        return urn
```

### Validator with Checksum Verification

```python
from international_urns import URNValidator

class SpanishDNIValidator(URNValidator):
    country_code = "es"
    document_types = ["dni"]

    LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

    def validate(self, urn: str) -> str:
        parts = urn.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        dni = parts[3]

        # DNI format: 8 digits + 1 letter
        if len(dni) != 9:
            raise ValueError(f"DNI must be 9 characters: {dni}")

        number_part = dni[:8]
        letter = dni[8].upper()

        if not number_part.isdigit():
            raise ValueError(f"First 8 characters must be digits: {dni}")

        # Verify checksum
        expected_letter = self.LETTERS[int(number_part) % 23]
        if letter != expected_letter:
            raise ValueError(
                f"Invalid DNI checksum. Expected {expected_letter}, got {letter}"
            )

        return urn
```

## Error Handling

### Graceful Error Handling

```python
import international_urns as iurns

def validate_urn_safely(urn: str, country: str, doc_type: str) -> tuple[bool, str]:
    """Validate a URN and return success status and message."""
    try:
        # Check if validator exists
        if not iurns.has_validator(country, doc_type):
            return False, f"No validator for {country}:{doc_type}"

        # Get and run validator
        validator = iurns.get_validator(country, doc_type)
        result = validator(urn)
        return True, result

    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"

# Usage
success, result = validate_urn_safely('urn:es:dni:12345678X', 'es', 'dni')
if success:
    print(f"Valid: {result}")
else:
    print(f"Invalid: {result}")
```

### Custom Error Messages

```python
from international_urns import URNValidator

class VerboseValidator(URNValidator):
    country_code = "fr"
    document_types = ["nir"]

    def validate(self, urn: str) -> str:
        parts = urn.split(':')

        if len(parts) != 4:
            raise ValueError(
                f"URN must have exactly 4 parts separated by colons. "
                f"Expected format: 'urn:fr:nir:number'. Got: {urn}"
            )

        if parts[0].lower() != 'urn':
            raise ValueError(
                f"URN must start with 'urn' scheme. Got: {parts[0]}"
            )

        if parts[1].lower() != 'fr':
            raise ValueError(
                f"Country code must be 'fr' for this validator. Got: {parts[1]}"
            )

        if parts[2].lower() != 'nir':
            raise ValueError(
                f"Document type must be 'nir'. Got: {parts[2]}"
            )

        nir = parts[3]
        if not (len(nir) == 15 and nir.isdigit()):
            raise ValueError(
                f"NIR must be exactly 15 digits. Got: {nir} ({len(nir)} characters)"
            )

        return urn
```

## Testing Examples

### Basic Test

```python
import pytest
from international_urns import URNValidator

class TestMyValidator:
    def test_valid_urn(self):
        validator = MyValidator()
        result = validator.validate('urn:xx:id:ABC123')
        assert result == 'urn:xx:id:ABC123'

    def test_invalid_urn(self):
        validator = MyValidator()
        with pytest.raises(ValueError, match="Invalid URN"):
            validator.validate('invalid-urn')
```

### Parametrized Tests

```python
import pytest
from international_urns import URNValidator

class TestDocumentValidator:
    @pytest.mark.parametrize("urn,expected", [
        ("urn:us:passport:AB1234567", "urn:us:passport:AB1234567"),
        ("URN:US:PASSPORT:AB1234567", "URN:US:PASSPORT:AB1234567"),
        ("urn:us:passport:XY9876543", "urn:us:passport:XY9876543"),
    ])
    def test_valid_urns(self, urn, expected):
        validator = PassportValidator()
        result = validator.validate(urn)
        assert result == expected

    @pytest.mark.parametrize("invalid_urn", [
        "not-a-urn",
        "urn:us:passport",  # Missing value
        "urn:us:passport:123",  # Too short
        "urn:us:passport:ABCDEFGHIJ",  # Too long
        "urn:us:passport:ABC-12345",  # Invalid characters
    ])
    def test_invalid_urns(self, invalid_urn):
        validator = PassportValidator()
        with pytest.raises(ValueError):
            validator.validate(invalid_urn)
```

## Integration Examples

### With Logging

```python
import logging
import international_urns as iurns

logger = logging.getLogger(__name__)

def validate_with_logging(urn: str, country: str, doc_type: str) -> str | None:
    """Validate URN with logging."""
    logger.info(f"Validating URN: {urn} for {country}:{doc_type}")

    try:
        validator = iurns.get_validator(country, doc_type)
        result = validator(urn)
        logger.info(f"Validation successful: {result}")
        return result
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        return None
```

### With Data Processing

```python
import international_urns as iurns
from typing import Iterator

def process_urns(urns: list[str], country: str, doc_type: str) -> Iterator[tuple[str, bool, str]]:
    """Process multiple URNs and yield results."""
    validator = iurns.get_validator(country, doc_type)

    for urn in urns:
        try:
            result = validator(urn)
            yield (urn, True, result)
        except ValueError as e:
            yield (urn, False, str(e))

# Usage
urns = [
    'urn:es:dni:12345678X',
    'urn:es:dni:invalid',
    'urn:es:dni:87654321Y',
]

for original, valid, result in process_urns(urns, 'es', 'dni'):
    status = "✓" if valid else "✗"
    print(f"{status} {original}: {result}")
```
