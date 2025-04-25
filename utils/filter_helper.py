# utils/filter_helper.py

from typing import List
from models.escuela import Escuela
from utils.normalizer import normalizar_texto

def filtrar_por_localidad(
    escuelas: List[Escuela],
    localidad_filtro: str
) -> List[Escuela]:
    """
    Devuelve sólo aquellas instancias de Escuela cuya propiedad .localidad,
    una vez normalizada, sea igual a la localidad_filtro normalizada.
    """
    loc_norm = normalizar_texto(localidad_filtro)
    filtradas = []
    for e in escuelas:
        if normalizar_texto(e.localidad) == loc_norm:
            filtradas.append(e)
    return filtradas
