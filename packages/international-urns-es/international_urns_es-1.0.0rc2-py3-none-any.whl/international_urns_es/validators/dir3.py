"""DIR3 (Directorio Común de unidades y oficinas) validator for Spain.

DIR3 is the Common Directory of units and offices of the Spanish Public Administration.
Format: 9-10 character alphanumeric code.
Examples: A01002844, LA0003516, E00003801
"""

import re
from typing import ClassVar

from international_urns import URNValidator


class DIR3Validator(URNValidator):
    """Validator for Spanish DIR3 codes.

    DIR3 codes identify administrative units and offices in the Spanish
    Public Administration. They consist of 9-10 alphanumeric characters.

    Valid format: urn:es:dir3:A01002844

    The code structure:
    - First character: Letter indicating administration level
      (A=State, C=Autonomous Community, L=Local, E=Other entities)
    - Remaining 8-9 characters: Numeric or alphanumeric identifier

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"
    document_types: ClassVar[list[str]] = ["dir3"]

    # DIR3 pattern: Letter + 8-9 alphanumeric characters
    _DIR3_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z]{1,2}\d{8}$")

    def validate(self, urn: str) -> str:
        """Validate a Spanish DIR3 URN.

        :param urn: The URN to validate
        :type urn: str
        :return: The validated URN
        :rtype: str
        :raises ValueError: If the URN is invalid
        """
        # Parse URN
        parts = urn.split(":")
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        scheme, country, doc_type, value = parts

        if scheme.lower() != "urn":
            raise ValueError(f"Invalid URN scheme: {scheme}")

        if country.lower() != self.country_code:
            raise ValueError(f"Invalid country code: {country}")

        if doc_type.lower() not in self.document_types:
            raise ValueError(f"Invalid document type: {doc_type}")

        # Validate DIR3 format
        self._validate_dir3(value)

        # Return normalized URN (lowercase scheme, country, and doc_type)
        return f"urn:{country.lower()}:{doc_type.lower()}:{value}"

    def _validate_dir3(self, dir3: str) -> None:
        """Validate DIR3 code format.

        :param dir3: The DIR3 value to validate
        :type dir3: str
        :raises ValueError: If the DIR3 code is invalid
        """
        # Convert to uppercase for validation
        dir3 = dir3.upper()

        # Check length
        if len(dir3) < 9 or len(dir3) > 10:
            raise ValueError(f"Invalid DIR3 length: {dir3}. Expected 9-10 characters")

        # Validate format
        if not self._DIR3_PATTERN.match(dir3):
            raise ValueError(
                f"Invalid DIR3 format: {dir3}. Expected 1-2 letters followed by 8 digits"
            )

        # Validate first character (administration level)
        first_char = dir3[0]
        valid_levels = {"A", "C", "L", "E"}
        if first_char not in valid_levels:
            raise ValueError(
                f"Invalid DIR3 administration level: {first_char}. "
                f"Expected one of: {', '.join(sorted(valid_levels))}"
            )


__all__ = ["DIR3Validator"]
