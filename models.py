"""Clases del dominio (POO)."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
import itertools

_ids = itertools.count(1)


@dataclass
class Turno:
    nombre: str
    id: int = field(default_factory=lambda: next(_ids))
    creado: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


@dataclass
class Registro:
    material: str
    kg: float
    co2: float
    turno: str = ""
    origen: str = "manual"            # manual | api
    producto: str = ""
    id: int = 0
    fecha: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self):
        return asdict(self)
