"""International URNs plugin for Spain.

This plugin provides validators and generators for Spanish documents including:
- DNI (Documento Nacional de Identidad)
- NIF (Número de Identificación Fiscal)
- NIE (Número de Identidad de Extranjero)
- CIF (Código de Identificación Fiscal)
- DIR3 (Directorio Común)
- NSS (Número de la Seguridad Social)
- License Plates (Matrículas)

Author: Jesús Alonso Abad
"""

import international_urns

from international_urns_es.generators import (
    generate_cif,
    generate_dir3,
    generate_dni,
    generate_nie,
    generate_nif,
    generate_nss,
    generate_plate,
)
from international_urns_es.validators import (
    CIFValidator,
    DIR3Validator,
    DNIValidator,
    NIEValidator,
    NIFValidator,
    NSSValidator,
    PlateValidator,
)

__version__ = "1.0.0rc2"
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


# Register generators
_registry = international_urns.get_generator_registry()
_registry.register("es", "dni", generate_dni)
_registry.register("es", "nie", generate_nie)
_registry.register("es", "nif", generate_nif)
_registry.register("es", "cif", generate_cif)
_registry.register("es", "dir3", generate_dir3)
_registry.register("es", "nss", generate_nss)
_registry.register("es", "plate", generate_plate)
_registry.register("es", "matricula", generate_plate)  # Alternative name for plate


__all__ = [
    "SpainValidators",
    "CIFValidator",
    "DIR3Validator",
    "DNIValidator",
    "NIEValidator",
    "NIFValidator",
    "NSSValidator",
    "PlateValidator",
    "generate_cif",
    "generate_dir3",
    "generate_dni",
    "generate_nie",
    "generate_nif",
    "generate_nss",
    "generate_plate",
    "__version__",
    "__author__",
]
