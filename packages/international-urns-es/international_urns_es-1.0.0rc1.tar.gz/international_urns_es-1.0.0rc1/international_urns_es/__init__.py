"""International URNs plugin for Spain.

This plugin provides validators for Spanish documents including:
- DNI (Documento Nacional de Identidad)
- NIF (Número de Identificación Fiscal)
- NIE (Número de Identidad de Extranjero)
- CIF (Código de Identificación Fiscal)
- DIR3 (Directorio Común)
- NSS (Número de la Seguridad Social)
- License Plates (Matrículas)

Author: Jesús Alonso Abad
"""

from international_urns_es.validators import (
    CIFValidator,
    DIR3Validator,
    DNIValidator,
    NIEValidator,
    NIFValidator,
    NSSValidator,
    PlateValidator,
)

__version__ = "1.0.0rc1"
__author__ = "Jesús Alonso Abad"


class SpainValidators:
    """Container class for Spain validators.

    This class is used as the entry point for the international_urns plugin system.
    All validator classes are automatically registered when imported.
    """

    validators = [
        DNIValidator,
        NIEValidator,
        NIFValidator,
        CIFValidator,
        DIR3Validator,
        NSSValidator,
        PlateValidator,
    ]


__all__ = [
    "SpainValidators",
    "CIFValidator",
    "DIR3Validator",
    "DNIValidator",
    "NIEValidator",
    "NIFValidator",
    "NSSValidator",
    "PlateValidator",
    "__version__",
    "__author__",
]
