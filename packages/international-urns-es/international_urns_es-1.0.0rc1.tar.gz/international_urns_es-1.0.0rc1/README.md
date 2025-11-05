# International URNs - Spain Plugin

A comprehensive plugin for [International URNs](https://github.com/international-urns/international-urns) that provides validators for Spanish identity documents and administrative codes.

## Author

**Jesús Alonso Abad**

## Requirements

- Python 3.11 or higher
- Pydantic 2.0+ (optional, for Pydantic integration)

## Installation

```bash
pip install international-urns-es
```

## Supported Documents

This plugin validates the following Spanish document types:

- **DNI** - Documento Nacional de Identidad (National Identity Document)
- **NIE** - Número de Identidad de Extranjero (Foreigner Identity Number)
- **NIF** - Número de Identificación Fiscal (Tax Identification Number)
- **CIF** - Código de Identificación Fiscal (Company Tax Code)
- **DIR3** - Directorio Común de unidades y oficinas (Common Directory of Administrative Units)
- **NSS** - Número de la Seguridad Social (Social Security Number)
- **License Plates** - Matrículas de vehículos (Vehicle registration plates)

## Quick Start

```python
import international_urns as iurns

# Validate a DNI
dni_validator = iurns.get_validator('es', 'dni')
result = dni_validator('urn:es:dni:12345678Z')
print(result)  # urn:es:dni:12345678Z

# Validate a NIE
nie_validator = iurns.get_validator('es', 'nie')
result = nie_validator('urn:es:nie:X1234567L')
print(result)  # urn:es:nie:X1234567L

# Validate a license plate
plate_validator = iurns.get_validator('es', 'plate')
result = plate_validator('urn:es:plate:1234BBC')
print(result)  # urn:es:plate:1234BBC
```

## Document Types Reference

### DNI (Documento Nacional de Identidad)

The DNI is the national identity document for Spanish citizens.

**Format:** 8 digits + 1 check letter

**Examples:**
- `12345678Z`
- `00000000T`
- `99999999R`

**URN Format:**
```
urn:es:dni:12345678Z
```

**Usage:**
```python
import international_urns as iurns

validator = iurns.get_validator('es', 'dni')

# Valid DNI
try:
    result = validator('urn:es:dni:12345678Z')
    print(f"Valid: {result}")
except ValueError as e:
    print(f"Invalid: {e}")
```

**Validation Rules:**
- Must be exactly 8 digits followed by 1 letter
- Check letter is calculated using modulo 23 algorithm
- Case-insensitive for URN scheme, country, and document type
- Value preserves original case

---

### NIE (Número de Identidad de Extranjero)

The NIE is the identification number for foreign nationals residing in Spain.

**Format:** Letter (X, Y, or Z) + 7 digits + 1 check letter

**Examples:**
- `X1234567L`
- `Y0000000Z`
- `Z9999999R`

**URN Format:**
```
urn:es:nie:X1234567L
```

**Usage:**
```python
import international_urns as iurns

validator = iurns.get_validator('es', 'nie')
result = validator('urn:es:nie:X1234567L')
```

**Validation Rules:**
- Prefix must be X, Y, or Z
- Followed by exactly 7 digits
- Check letter calculated using same algorithm as DNI (with prefix conversion: X→0, Y→1, Z→2)

---

### NIF (Número de Identificación Fiscal)

The NIF is the tax identification number for individuals in Spain. It accepts both DNI and NIE formats.

**Format:** DNI format (8 digits + letter) or NIE format (letter + 7 digits + letter)

**Examples:**
- `12345678Z` (DNI format)
- `X1234567L` (NIE format)

**URN Format:**
```
urn:es:nif:12345678Z
urn:es:nif:X1234567L
```

**Usage:**
```python
import international_urns as iurns

validator = iurns.get_validator('es', 'nif')

# DNI format
result1 = validator('urn:es:nif:12345678Z')

# NIE format
result2 = validator('urn:es:nif:X1234567L')
```

**Validation Rules:**
- Accepts both DNI and NIE formats
- Validates check letter for both formats

---

### CIF (Código de Identificación Fiscal)

The CIF is the tax identification code for Spanish companies and organizations.

**Format:** 1 organization letter + 7 digits + 1 check character (letter or digit)

**Organization Type Letters:**
- **A** - Sociedades Anónimas (Public Limited Companies)
- **B** - Sociedades de Responsabilidad Limitada (Private Limited Companies)
- **C** - Sociedades Colectivas (General Partnerships)
- **D** - Sociedades Comanditarias (Limited Partnerships)
- **E** - Comunidades de Bienes (Communities of Property)
- **F** - Sociedades Cooperativas (Cooperatives)
- **G** - Asociaciones (Associations)
- **H** - Comunidades de Propietarios (Homeowner Associations)
- **J** - Sociedades Civiles (Civil Partnerships)
- **N** - Entidades Extranjeras (Foreign Entities)
- **P** - Corporaciones Locales (Local Corporations)
- **Q** - Organismos Autónomos (Autonomous Bodies)
- **R** - Congregaciones e Instituciones Religiosas (Religious Organizations)
- **S** - Órganos de la Administración del Estado (State Administration Bodies)
- **V** - Otros tipos no definidos (Other Undefined Types)
- **W** - Establecimientos permanentes de entidades no residentes (Permanent Establishments)

**Examples:**
- `A12345674` (SA - Sociedad Anónima, check digit is number)
- `B01234566` (SL - Sociedad Limitada, check digit is number)
- `N1234567J` (Foreign entity - check digit is letter)

**URN Format:**
```
urn:es:cif:A12345674
```

**Usage:**
```python
import international_urns as iurns

validator = iurns.get_validator('es', 'cif')
result = validator('urn:es:cif:A12345674')
```

**Validation Rules:**
- Organization types N, P, Q, R, S, W must have a letter as check digit
- Organization types A, B, E, H must have a number as check digit
- Other types can have either
- Check digit calculated using weighted sum algorithm

---

### DIR3 (Directorio Común)

DIR3 codes identify administrative units and offices in the Spanish Public Administration.

**Format:** 1-2 letters + 8 digits

**Administration Level Codes:**
- **A** - Administración del Estado (State Administration)
- **C** - Comunidad Autónoma (Autonomous Community)
- **L** - Administración Local (Local Administration)
- **E** - Otras Entidades (Other Entities)

**Examples:**
- `A01002844` (State administration unit)
- `LA0003516` (Local administration unit)
- `E00003801` (Other entity)

**URN Format:**
```
urn:es:dir3:A01002844
```

**Usage:**
```python
import international_urns as iurns

validator = iurns.get_validator('es', 'dir3')
result = validator('urn:es:dir3:A01002844')
```

**Validation Rules:**
- Must be 9-10 characters total
- First 1-2 characters must be letters indicating administration level
- Remaining 8 characters must be digits
- First letter must be A, C, L, or E

---

### NSS (Número de la Seguridad Social)

The NSS is the Social Security Number used in Spain.

**Format:** 12 digits, optionally formatted with slashes

**Structure:**
- First 2 digits: Province code (01-52 or special codes 66-99)
- Next 8 digits: Sequential number
- Last 2 digits: Check digits (calculated using modulo 97)

**Examples:**
- `281234567840` (without slashes)
- `28/12345678/40` (with slashes)

**URN Format:**
```
urn:es:nss:281234567840
urn:es:nss:28/12345678/40
```

**Usage:**
```python
import international_urns as iurns

validator = iurns.get_validator('es', 'nss')

# Without slashes
result1 = validator('urn:es:nss:281234567840')

# With slashes
result2 = validator('urn:es:nss:28/12345678/40')
```

**Validation Rules:**
- Must be exactly 12 digits
- Province code must be 01-52 (Spanish provinces) or 66-99 (special codes)
- Check digits validated using modulo 97 algorithm
- Accepts format with or without slashes

---

### License Plates (Matrículas)

Spanish vehicle license plates. Supports current, historical, and special formats.

**Current Format (since 2000):** 4 digits + 3 consonants (no vowels)

**Old Format (1971-2000):** 1-2 province letters + 4 digits + 1-2 letters

**Special Formats:** Diplomatic (CD), Consular (CC), Foreign (E), etc.

**Examples:**

*Current format:*
- `1234BBC`
- `0000ZZZ`
- `9999DFG`

*Old format:*
- `M1234AB` (Madrid)
- `B5678XY` (Barcelona)
- `PM9012CD` (Palma de Mallorca)

*Special format:*
- `CD1234` (Diplomatic)
- `CC12345` (Consular)
- `E12345` (Foreign)

**URN Format:**
```
urn:es:plate:1234BBC
urn:es:plate:M1234AB
urn:es:matricula:1234BBC
```

**Usage:**
```python
import international_urns as iurns

validator = iurns.get_validator('es', 'plate')

# Current format
result1 = validator('urn:es:plate:1234BBC')

# Old format
result2 = validator('urn:es:plate:M1234AB')

# With spaces or hyphens (automatically normalized)
result3 = validator('urn:es:plate:1234 BBC')
result4 = validator('urn:es:plate:M-1234-AB')
```

**Validation Rules:**

*Current format:*
- Must be 4 digits + 3 consonants
- Allowed consonants: B, C, D, F, G, H, J, K, L, M, N, P, R, S, T, V, W, X, Y, Z
- No vowels (A, E, I, O, U), Ñ, or Q allowed

*Old format:*
- Province code must be valid (M, B, MA, PM, etc.)
- Followed by 4 digits
- Ending with 1-2 letters

*Special format:*
- Recognized prefixes: CD, CC, E, ET, CMD, DGP, MF, MMA, PMM, CNP
- Followed by 4-5 digits

---

## Pydantic Integration

All validators work seamlessly with Pydantic v2 using the **international_urns registry interface** with `BeforeValidator` and `AfterValidator` annotations. Validators are automatically registered through the plugin system and can be used directly - no wrapper functions needed!

```python
from typing import Annotated

import international_urns as iurns
from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator, BeforeValidator


# Create type aliases using validators directly from the registry
DNI_URN = Annotated[str, AfterValidator(iurns.get_validator("es", "dni"))]
CIF_URN = Annotated[str, AfterValidator(iurns.get_validator("es", "cif"))]

# Type alias with both BeforeValidator and AfterValidator
DNI_URN_NORMALIZED = Annotated[
    str,
    BeforeValidator(str.strip),  # Built-in normalization
    AfterValidator(iurns.get_validator("es", "dni")),
]


# Use in models
class Person(BaseModel):
    name: str
    dni_urn: DNI_URN


class Company(BaseModel):
    name: str
    cif_urn: CIF_URN


class Employee(BaseModel):
    name: str
    dni_urn: DNI_URN_NORMALIZED  # Strips whitespace before validation


# Usage
person = Person(name="John Doe", dni_urn="urn:es:dni:12345678Z")
company = Company(name="Example SL", cif_urn="urn:es:cif:B01234566")  # SL uses B prefix
employee = Employee(name="Jane Doe", dni_urn="  urn:es:dni:12345678Z  ")  # Auto-strips
```

### Advanced Pydantic Examples

**Multiple validators in one model:**

```python
# Define additional validators using registry
PLATE_URN = Annotated[str, AfterValidator(iurns.get_validator("es", "plate"))]

class SpanishEntity(BaseModel):
    name: str
    dni_urn: DNI_URN | None = None
    cif_urn: CIF_URN | None = None
    plate_urn: PLATE_URN | None = None

# Person with DNI and vehicle
person = SpanishEntity(
    name="John Doe",
    dni_urn="urn:es:dni:12345678Z",
    plate_urn="urn:es:plate:1234BBC"
)
```

**List validation:**

```python
class CompanyFleet(BaseModel):
    company_name: str
    cif_urn: CIF_URN
    vehicles: list[PLATE_URN]

# SL companies use B prefix
fleet = CompanyFleet(
    company_name="Transport SL",
    cif_urn="urn:es:cif:B01234566",
    vehicles=["urn:es:plate:1234BBC", "urn:es:plate:5678DFG"]
)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://gitlab.com/Kencho1/international-urns-es.git
cd international-urns-es

# Create virtual environment with uv
uv venv

# Install dependencies with dev extras
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=international_urns_es --cov-report=html

# Run specific test file
pytest tests/test_dni.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Run ruff linter
ruff check .

# Run ruff formatter
ruff format .

# Run mypy type checker
mypy international_urns_es
```

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass
2. Code passes ruff and mypy checks
3. New validators include comprehensive tests
4. Documentation is updated

## License

MIT License

## Links

- [GitLab Repository](https://gitlab.com/Kencho1/international-urns-es)
- [Issue Tracker](https://gitlab.com/Kencho1/international-urns-es/-/issues)
- [International URNs](https://github.com/international-urns/international-urns)
- [PyPI Package](https://pypi.org/project/international-urns-es/)

## References

### Official Documentation

- [DNI - Spanish National ID](https://www.dnie.es/)
- [NIE - Foreigner ID](https://www.inclusion.gob.es/web/guest/nie)
- [Seguridad Social - Social Security](https://www.seg-social.es/)
- [DIR3 - Administrative Directory](https://administracionelectronica.gob.es/ctt/dir3)
- [DGT - Vehicle Plates](https://www.dgt.es/)

### Algorithm References

- DNI/NIE check letter calculation uses modulo 23
- CIF check digit uses weighted sum algorithm
- NSS check digits use modulo 97
- License plate formats follow Spanish regulations from different eras
