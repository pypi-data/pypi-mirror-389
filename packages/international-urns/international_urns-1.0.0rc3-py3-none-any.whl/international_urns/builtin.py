"""Built-in validators for general URN formats."""

import re

from .base import URNValidator


class WildcardValidator(URNValidator):
    """Validator for wildcard URN format: urn:--:--:...

    Accepts any string matching the pattern ^urn:.+:.+:.+$ when using
    the wildcard country code '--' and document type '--'.
    """

    country_code = "--"
    document_types = ["--"]

    def validate(self, urn: str) -> str:
        """Validate wildcard URN format.

        :param urn: The URN string to validate
        :type urn: str
        :return: The validated URN string
        :rtype: str
        :raises ValueError: If the URN doesn't match the basic format
        """
        if not re.match(r"^urn:--:--:.+$", urn, re.IGNORECASE):
            raise ValueError(
                f"Invalid wildcard URN format. Expected 'urn:--:--:...' but got: {urn}"
            )

        if not re.match(r"^urn:.+:.+:.+$", urn, re.IGNORECASE):
            raise ValueError(f"URN must have format 'urn:nid:nss-type:nss-value': {urn}")

        return urn


__all__ = ["WildcardValidator"]
