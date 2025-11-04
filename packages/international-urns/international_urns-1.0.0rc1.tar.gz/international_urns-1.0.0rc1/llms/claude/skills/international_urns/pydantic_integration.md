# International URNs - Pydantic Integration

Complete guide for integrating International URNs with Pydantic models.

## Basic Integration

### Using AfterValidator

```python
from pydantic import BaseModel, AfterValidator
from typing import Annotated
import international_urns as iurns

class Document(BaseModel):
    """Model with URN validation."""

    urn: Annotated[
        str,
        AfterValidator(iurns.get_validator('es', 'dni'))
    ]

# Usage
doc = Document(urn="urn:es:dni:12345678Z")
print(doc.urn)  # Output: urn:es:dni:12345678Z

# Invalid URN raises ValidationError
try:
    Document(urn="invalid")
except Exception as e:
    print(f"Validation failed: {e}")
```

### Using BeforeValidator for Normalization

```python
from pydantic import BaseModel, BeforeValidator
from typing import Annotated
import international_urns as iurns

class NormalizedDocument(BaseModel):
    """Model that normalizes URNs before storage."""

    urn: Annotated[
        str,
        BeforeValidator(iurns.create_normalizer())
    ]

# Usage
doc = NormalizedDocument(urn="URN:ES:DNI:12345678X")
print(doc.urn)  # Output: "urn:es:dni:12345678X"
```

### Combining Normalization and Validation

```python
from pydantic import BaseModel, AfterValidator, BeforeValidator
from typing import Annotated
import international_urns as iurns

class ValidatedDocument(BaseModel):
    """Model with both normalization and validation."""

    urn: Annotated[
        str,
        BeforeValidator(iurns.create_normalizer()),
        AfterValidator(iurns.get_validator('es', 'dni'))
    ]

# Usage
doc = ValidatedDocument(urn="URN:ES:DNI:12345678Z")
print(doc.urn)  # Output: "urn:es:dni:12345678Z"
```

## Advanced Patterns

### Multiple URN Fields

```python
from pydantic import BaseModel, AfterValidator, BeforeValidator
from typing import Annotated
import international_urns as iurns

# Define type aliases for clarity
SpanishDNI = Annotated[
    str,
    BeforeValidator(iurns.create_normalizer()),
    AfterValidator(iurns.get_validator('es', 'dni'))
]

SpanishNIE = Annotated[
    str,
    BeforeValidator(iurns.create_normalizer()),
    AfterValidator(iurns.get_validator('es', 'nie'))
]

class Person(BaseModel):
    """Person with multiple identity documents."""

    name: str
    dni: SpanishDNI | None = None
    nie: SpanishNIE | None = None

    def model_post_init(self, __context):
        """Ensure at least one document is provided."""
        if self.dni is None and self.nie is None:
            raise ValueError("Either DNI or NIE must be provided")

# Usage
person = Person(
    name="John Doe",
    dni="URN:ES:DNI:12345678Z"
)
```

### Flexible URN Type

```python
from pydantic import BaseModel, field_validator
from typing import Annotated
import international_urns as iurns

class FlexibleDocument(BaseModel):
    """Model that accepts any valid URN."""

    urn: str

    @field_validator('urn')
    @classmethod
    def validate_urn(cls, v: str) -> str:
        """Validate URN format and normalize."""
        # Normalize
        normalized = iurns.normalize_urn(v)

        # Parse to get components
        parts = normalized.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {v}")

        country, doc_type = parts[1], parts[2]

        # Validate if validator exists
        if iurns.has_validator(country, doc_type):
            validator = iurns.get_validator(country, doc_type)
            return validator(normalized)

        # Accept if no validator available
        return normalized

# Usage
doc1 = FlexibleDocument(urn="urn:es:dni:12345678Z")  # Validated
doc2 = FlexibleDocument(urn="urn:unknown:type:value")  # Accepted but not validated
```

### Custom Validator Factory

```python
from pydantic import BaseModel, AfterValidator, BeforeValidator
from typing import Annotated, Callable
import international_urns as iurns

def create_urn_validator(country: str, doc_type: str):
    """Create a Pydantic-compatible URN validator."""
    normalizer = iurns.create_normalizer()
    validator = iurns.get_validator(country, doc_type)

    def validate_urn(value: str) -> str:
        normalized = normalizer(value)
        return validator(normalized)

    return validate_urn

# Define reusable types
SpanishDNI = Annotated[str, AfterValidator(create_urn_validator('es', 'dni'))]
FrenchNIR = Annotated[str, AfterValidator(create_urn_validator('fr', 'nir'))]

class InternationalPerson(BaseModel):
    name: str
    spanish_id: SpanishDNI | None = None
    french_id: FrenchNIR | None = None
```

## Field-Level Customization

### Custom Error Messages

```python
from pydantic import BaseModel, field_validator
import international_urns as iurns

class DocumentWithCustomErrors(BaseModel):
    """Model with custom validation error messages."""

    urn: str

    @field_validator('urn')
    @classmethod
    def validate_urn(cls, v: str) -> str:
        try:
            normalized = iurns.normalize_urn(v)
            validator = iurns.get_validator('es', 'dni')
            return validator(normalized)
        except ValueError as e:
            raise ValueError(
                f"Invalid Spanish DNI URN. Please provide a URN in the format "
                f"'urn:es:dni:NNNNNNNNL' where N is a digit and L is a letter. "
                f"Original error: {e}"
            )

# Usage
try:
    DocumentWithCustomErrors(urn="invalid")
except Exception as e:
    print(e)  # Shows custom error message
```

### Conditional Validation

```python
from pydantic import BaseModel, model_validator
import international_urns as iurns

class ConditionalDocument(BaseModel):
    """Model with conditional URN validation."""

    country: str
    doc_type: str
    urn: str

    @model_validator(mode='after')
    def validate_urn_for_country(self):
        """Validate URN based on country and type."""
        if iurns.has_validator(self.country, self.doc_type):
            validator = iurns.get_validator(self.country, self.doc_type)
            try:
                normalized = iurns.normalize_urn(self.urn)
                self.urn = validator(normalized)
            except ValueError as e:
                raise ValueError(
                    f"Invalid {self.doc_type.upper()} for {self.country.upper()}: {e}"
                )
        return self

# Usage
doc = ConditionalDocument(
    country="es",
    doc_type="dni",
    urn="urn:es:dni:12345678Z"
)
```

## Working with Lists

### Validating Multiple URNs

```python
from pydantic import BaseModel, AfterValidator
from typing import Annotated
import international_urns as iurns

URN = Annotated[
    str,
    BeforeValidator(iurns.create_normalizer()),
    AfterValidator(iurns.get_validator('es', 'dni'))
]

class DocumentBatch(BaseModel):
    """Model for batch URN processing."""

    urns: list[URN]

# Usage
batch = DocumentBatch(urns=[
    "URN:ES:DNI:12345678Z",
    "urn:es:dni:87654321X",
    "URN:ES:DNI:11111111H",
])

print(f"Processed {len(batch.urns)} URNs")
for urn in batch.urns:
    print(f"  - {urn}")
```

### Mixed URN Types

```python
from pydantic import BaseModel, field_validator
from typing import Literal
import international_urns as iurns

class MixedURNDocument(BaseModel):
    """Model accepting multiple URN types."""

    urn_type: Literal['dni', 'nie', 'passport']
    urn: str

    @field_validator('urn')
    @classmethod
    def validate_urn(cls, v: str, info) -> str:
        """Validate URN based on type."""
        urn_type = info.data.get('urn_type')
        if not urn_type:
            raise ValueError("urn_type must be set before urn")

        normalized = iurns.normalize_urn(v)

        # Map types to validators
        validators = {
            'dni': ('es', 'dni'),
            'nie': ('es', 'nie'),
            'passport': ('us', 'passport'),
        }

        country, doc_type = validators[urn_type]
        validator = iurns.get_validator(country, doc_type)
        return validator(normalized)

# Usage
doc = MixedURNDocument(
    urn_type="dni",
    urn="urn:es:dni:12345678Z"
)
```

## Integration with Pydantic Settings

### Configuration with URN Validation

```python
from pydantic_settings import BaseSettings
from pydantic import AfterValidator
from typing import Annotated
import international_urns as iurns

class AppSettings(BaseSettings):
    """Application settings with URN validation."""

    admin_dni: Annotated[
        str,
        AfterValidator(iurns.get_validator('es', 'dni'))
    ]
    default_country: str = "es"
    default_doc_type: str = "dni"

    class Config:
        env_file = ".env"

# Usage
# In .env: ADMIN_DNI=urn:es:dni:12345678Z
settings = AppSettings()
```

## Database Integration

### SQLModel Integration

```python
from sqlmodel import SQLModel, Field
from pydantic import AfterValidator, BeforeValidator
from typing import Annotated
import international_urns as iurns

URN = Annotated[
    str,
    BeforeValidator(iurns.create_normalizer()),
    AfterValidator(iurns.get_validator('es', 'dni'))
]

class User(SQLModel, table=True):
    """User model with validated URN."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    dni_urn: URN = Field(unique=True)

# Usage
user = User(
    name="John Doe",
    dni_urn="URN:ES:DNI:12345678Z"
)
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, AfterValidator, ValidationError
from typing import Annotated
import international_urns as iurns

app = FastAPI()

URN = Annotated[
    str,
    BeforeValidator(iurns.create_normalizer()),
    AfterValidator(iurns.get_validator('es', 'dni'))
]

class UserCreate(BaseModel):
    """User creation request."""
    name: str
    dni: URN

class UserResponse(BaseModel):
    """User response."""
    id: int
    name: str
    dni: str

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user with DNI validation."""
    # URN is already validated by Pydantic
    user_id = 1  # Would be from database
    return UserResponse(
        id=user_id,
        name=user.name,
        dni=user.dni
    )

@app.get("/validate/{urn:path}")
async def validate_urn(urn: str, country: str = "es", doc_type: str = "dni"):
    """Validate a URN."""
    try:
        normalized = iurns.normalize_urn(urn)
        validator = iurns.get_validator(country, doc_type)
        result = validator(normalized)
        return {"valid": True, "urn": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Testing with Pydantic Models

### Pytest Fixtures

```python
import pytest
from pydantic import ValidationError

@pytest.fixture
def valid_dni_urn():
    """Provide a valid DNI URN."""
    return "urn:es:dni:12345678Z"

@pytest.fixture
def invalid_dni_urn():
    """Provide an invalid DNI URN."""
    return "urn:es:dni:invalid"

def test_valid_document_creation(valid_dni_urn):
    """Test creating document with valid URN."""
    doc = ValidatedDocument(urn=valid_dni_urn)
    assert doc.urn == valid_dni_urn.lower()

def test_invalid_document_creation(invalid_dni_urn):
    """Test that invalid URN raises ValidationError."""
    with pytest.raises(ValidationError):
        ValidatedDocument(urn=invalid_dni_urn)
```

### Parametrized Tests

```python
import pytest
from pydantic import ValidationError

@pytest.mark.parametrize("urn", [
    "urn:es:dni:12345678Z",
    "URN:ES:DNI:12345678Z",  # Case variations
    "urn:ES:dni:12345678Z",
])
def test_valid_urns(urn):
    """Test that valid URNs are accepted."""
    doc = ValidatedDocument(urn=urn)
    assert doc.urn.startswith("urn:es:dni:")

@pytest.mark.parametrize("urn,error_substring", [
    ("invalid", "Invalid URN format"),
    ("urn:es:dni:12345678", "must be 9 characters"),
    ("urn:es:dni:12345678X", "Invalid DNI checksum"),
])
def test_invalid_urns(urn, error_substring):
    """Test that invalid URNs are rejected."""
    with pytest.raises(ValidationError, match=error_substring):
        ValidatedDocument(urn=urn)
```

## Performance Optimization

### Caching Validators

```python
from functools import lru_cache
from pydantic import BaseModel, AfterValidator
from typing import Annotated
import international_urns as iurns

@lru_cache(maxsize=100)
def get_cached_validator(country: str, doc_type: str):
    """Get and cache validator."""
    return iurns.get_validator(country, doc_type)

def create_cached_urn_type(country: str, doc_type: str):
    """Create URN type with cached validator."""
    validator = get_cached_validator(country, doc_type)
    return Annotated[
        str,
        BeforeValidator(iurns.create_normalizer()),
        AfterValidator(validator)
    ]

# Define types with caching
CachedSpanishDNI = create_cached_urn_type('es', 'dni')

class OptimizedDocument(BaseModel):
    urn: CachedSpanishDNI
```

## Complete Example: User Management System

```python
from datetime import datetime
from pydantic import BaseModel, AfterValidator, BeforeValidator, Field
from typing import Annotated, Literal
import international_urns as iurns

# Define URN types
SpanishDNI = Annotated[
    str,
    BeforeValidator(iurns.create_normalizer()),
    AfterValidator(iurns.get_validator('es', 'dni'))
]

SpanishNIE = Annotated[
    str,
    BeforeValidator(iurns.create_normalizer()),
    AfterValidator(iurns.get_validator('es', 'nie'))
]

class UserBase(BaseModel):
    """Base user model."""
    email: str
    name: str

class UserCreate(UserBase):
    """User creation model."""
    document_type: Literal['dni', 'nie']
    document_urn: str

    @field_validator('document_urn')
    @classmethod
    def validate_document(cls, v: str, info) -> str:
        """Validate document URN based on type."""
        doc_type = info.data.get('document_type')
        if not doc_type:
            raise ValueError("document_type must be set")

        normalized = iurns.normalize_urn(v)
        validator = iurns.get_validator('es', doc_type)
        return validator(normalized)

class User(UserBase):
    """Complete user model."""
    id: int
    document_urn: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# Usage
user_data = UserCreate(
    email="user@example.com",
    name="John Doe",
    document_type="dni",
    document_urn="URN:ES:DNI:12345678Z"
)

user = User(
    id=1,
    email=user_data.email,
    name=user_data.name,
    document_urn=user_data.document_urn
)
```
