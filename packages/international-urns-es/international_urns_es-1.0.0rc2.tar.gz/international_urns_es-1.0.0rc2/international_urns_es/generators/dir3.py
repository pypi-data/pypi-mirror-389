"""DIR3 (Directorio Común) generator for Spain.

DIR3 codes identify administrative units and offices in the Spanish Public Administration.
Format: 1-2 letters (administration level) + 8 digits.
"""

import random

# Valid administration level codes
_ADMIN_LEVELS = ["A", "C", "L", "E"]

# Some codes can have a second letter
_SECOND_LETTERS = ["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]


def generate_dir3() -> str:
    """Generate a random valid DIR3 URN.

    :return: A valid DIR3 URN (e.g., urn:es:dir3:A01002844 or urn:es:dir3:LA0003516)
    :rtype: str
    """
    # Select random administration level
    admin_level = random.choice(_ADMIN_LEVELS)

    # Randomly decide if we want a second letter (20% chance for variety)
    if random.random() < 0.2:
        second_letter = random.choice(_SECOND_LETTERS[1:])  # Skip empty string
        # Generate 8 digits
        digits = f"{random.randint(0, 99999999):08d}"
        code = f"{admin_level}{second_letter}{digits}"
    else:
        # Generate 8 digits
        digits = f"{random.randint(0, 99999999):08d}"
        code = f"{admin_level}{digits}"

    # Format as URN
    return f"urn:es:dir3:{code}"


__all__ = ["generate_dir3"]
