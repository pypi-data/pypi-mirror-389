"""International URNs - A microkernel library for country-specific URN validation.

This library provides a pluggable architecture for validating URNs associated with
countries using ISO 3166-1 Alpha-2 codes. URNs follow the format:

    urn:country_code:document_type:document_value

Example:
    urn:es:dni:12345678X
"""

__version__ = "1.0.0rc1"

# Import built-in validators to register them
# Public API
from .base import URNValidator
from .builtin import WildcardValidator  # noqa: F401

# Load external plugins
from .discovery import load_plugins
from .normalization import create_normalizer, normalize_urn
from .registry import URNRegistry, get_registry
from .validators import get_validator, has_validator, list_validators

__all__ = [
    # Version
    "__version__",
    # Main API
    "get_validator",
    "list_validators",
    "has_validator",
    "normalize_urn",
    "create_normalizer",
    # Base classes for plugin development
    "URNValidator",
    # Registry access
    "URNRegistry",
    "get_registry",
]

# Auto-load plugins on import
load_plugins()
