"""Base classes for URN validators."""

from abc import ABC, abstractmethod

from .registry import get_registry


class URNValidator(ABC):
    """Base class for URN validators with automatic registration.

    Subclasses should define class attributes:
    - country_code: ISO 3166-1 Alpha-2 country code
    - document_types: List of document type identifiers

    The validator will automatically register itself for all specified
    document types when the class is defined.
    """

    country_code: str
    document_types: list[str]

    def __init_subclass__(cls, **kwargs: dict) -> None:
        """Automatically register validator when subclass is created.

        :param kwargs: Additional keyword arguments
        :type kwargs: dict
        """
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "country_code") or not hasattr(cls, "document_types"):
            return

        registry = get_registry()

        for doc_type in cls.document_types:
            validator_instance = cls()
            registry.register(
                cls.country_code,
                doc_type,
                validator_instance.validate
            )

    @abstractmethod
    def validate(self, urn: str) -> str:
        """Validate and return the URN.

        :param urn: The URN string to validate
        :type urn: str
        :return: The validated/normalized URN string
        :rtype: str
        :raises ValueError: If the URN is invalid
        """
        pass


__all__ = ["URNValidator"]
