from pydantic import BaseModel
from typing import Optional

class Escuela(BaseModel):
    nombre: str
    cct: str
    nivel: str
    servicio_educativo: str
    turno: str
    entidad: str
    municipio: str
    localidad: str
    direccion: Optional [str] = None
    codigo_postal: Optional[str] = None
    alumnos: Optional[int] = None
    docentes: Optional[int] = None
    grupos: Optional[int] = None
    aulas: Optional[int] = None
    computadoras: Optional[int] = None
