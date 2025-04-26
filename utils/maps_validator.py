# utils/maps_validator.py
from unidecode import unidecode

def normalizar_texto(texto):
    import re
    texto = unidecode(texto.lower().strip())
    texto = re.sub(r'[^\w\s]', '', texto)  # elimina puntuación
    texto = texto.replace("av ", "avenida ")
    return texto

def validar_direccion(direccion_maps, direccion_sheet, cp_maps, cp_sheet):
    dir_maps = normalizar_texto(direccion_maps)
    dir_sheet = normalizar_texto(direccion_sheet)

    # Coincidencia flexible: ¿todas las palabras clave de la hoja están en el texto de Maps?
    palabras_clave = dir_sheet.split()
    match_direccion = all(palabra in dir_maps for palabra in palabras_clave if len(palabra) > 3)

    # CP exacto (si ambos existen)
    match_cp = cp_sheet and cp_maps and cp_sheet.strip() == cp_maps.strip()

    return match_direccion or match_cp


def extraer_direccion_cp(soup):
    # Dirección principal (puede venir de diferentes estructuras)
    direccion = ""
    cp = ""

    # Algunas clases típicas (pueden cambiar, pero suelen mantenerse)
    direccion_tag = soup.select_one('button[data-item-id="address"]') or soup.select_one('span[class*="UsdlK"]')
    if direccion_tag:
        direccion = direccion_tag.text.strip()

    # Extraer código postal con expresión regular si no viene separado
    import re
    match_cp = re.search(r"\b\d{5}\b", direccion)
    if match_cp:
        cp = match_cp.group()

    return direccion, cp

