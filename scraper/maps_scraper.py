from utils.google_maps_searcher import GoogleMapsSearcher
from utils.maps_validator import validar_direccion, extraer_direccion_cp
from bs4 import BeautifulSoup
import time
import re

class GoogleMapsDataEnricher:
    def __init__(self, driver):
        self.driver = driver
        self.searcher = GoogleMapsSearcher(driver)

    def enriquecer_fila(self, fila_df):
        nombre = fila_df["nombre"]
        municipio = fila_df.get("municipio", "")
        direccion = str(fila_df["direccion"])
        cp = str(fila_df["codigo_postal"])

        query = self.generar_query(nombre, direccion, municipio)
        print(f"🔍 Buscando escuela: {query}")
        if not self.searcher.buscar_escuela(query):
            print("❌ Falló la búsqueda.")
            return None

        time.sleep(2)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        nombre_maps = soup.select_one("h1 span, .DUwDvf")
        nombre_maps = nombre_maps.text.strip() if nombre_maps else "Desconocido"

        direccion_maps, cp_maps = extraer_direccion_cp(soup)

        return self.extraer_info(soup, nombre_maps, direccion_maps, cp_maps)

    def extraer_info(self, soup, nombre_maps, direccion_maps, cp_maps):
        
        def extraer_href(selector):
            tag = soup.select_one(selector)
            return tag["href"].strip() if tag and tag.has_attr("href") else ""
        
        def es_telefono_valido(telefono):
            if not telefono:
                return False
            digitos = re.sub(r"\D", "", telefono)  # elimina todo excepto números
            return len(digitos) >= 10
        

        # 📅 Horario
        horario_tag = soup.find("div", attrs={"aria-label": lambda x: x and "lunes" in x})
        horario = horario_tag["aria-label"].strip() if horario_tag else ""

        bloques = soup.select('div.Io6YTe.fontBodyMedium.kR99db.fdkmkc')
        telefono = ""
        if len(bloques) >= 2:
            telefono = bloques[2].text.strip()
        
        if not es_telefono_valido(telefono):
            telefono = ""

        pagina_web = extraer_href('a[data-item-id="authority"]')

        datos = {
            "telefono": telefono,
            "pagina_web": pagina_web,
            "horario": horario,
        }

        print("\n📌 Datos para:")
        print(f"   Nombre Maps  : {nombre_maps}")
        print(f"   Dirección    : {direccion_maps}")
        print(f"   Código Postal: {cp_maps}")
        print("   Datos obtenidos:")
        for k, v in datos.items():
            print(f"   → {k}: {v}")

        return datos

    def generar_query(self, nombre, direccion, municipio):
        partes = nombre.strip().split()
        clave = " ".join(partes[:2]) if len(partes) >= 2 else nombre
        return f"{clave} {direccion} {municipio}"
