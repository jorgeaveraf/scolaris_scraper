import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from utils.sheets_helper import (
    leer_hoja_como_df,
    actualizar_status_en_hoja,
    subir_csv_a_google_sheets_append
)
from utils.normalizer import normalizar_texto

class LocalidadScraper:
    BASE_URL = "https://www.siged.sep.gob.mx/SIGED/escuelas.html"

    def __init__(self, estado, sheet_id, output_csv="localidades.csv", headless=True):
        self.estado = estado
        self.sheet_id = sheet_id
        self.sheet_municipios = "Municipios"
        self.sheet_localidades = "Localidades"
        self.output_csv = output_csv

        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

        if os.path.exists(self.output_csv) and os.path.getsize(self.output_csv) > 0:
            self.df_localidades = pd.read_csv(self.output_csv)
        else:
            self.df_localidades = pd.DataFrame(columns=["estado", "municipio", "localidad", "status"])

    def open_siged(self):
        print("🌐 Abriendo sitio SIGED...")
        self.driver.get(self.BASE_URL)
        time.sleep(2)
        self.wait.until(EC.presence_of_element_located((By.ID, "lstStates")))
        print("✅ SIGED cargado correctamente.")

    def obtener_municipios_pendientes(self):
        df = leer_hoja_como_df(self.sheet_id, self.sheet_municipios)
        df_filtrado = df[(df["estado"] == self.estado) & (df["status"] == "pendiente")]
        return df_filtrado.to_dict(orient="records")

    def aplicar_filtros(self, estado, municipio):
        # Selección del estado tal cual
        Select(self.driver.find_element(By.ID, "lstStates")).select_by_visible_text(estado)
        time.sleep(2)

        # Obtener y normalizar opciones del municipio
        selector_municipios = self.driver.find_element(By.ID, "lstMunicipalities")
        opciones = selector_municipios.find_elements(By.TAG_NAME, "option")

        municipio_normalizado = normalizar_texto(municipio)

        matched_option = None
        for opt in opciones:
            texto_opt = opt.text.strip()
            if normalizar_texto(texto_opt) == municipio_normalizado:
                matched_option = texto_opt
                break

        if matched_option:
            Select(selector_municipios).select_by_visible_text(matched_option)
            time.sleep(2)
            print(f"🔍 Filtros aplicados → Estado: {estado}, Municipio: {matched_option}")
        else:
            raise Exception(f"❌ No se encontró coincidencia para municipio: {municipio}")

    def extraer_localidades(self):
        self.wait.until(lambda driver: len(
            driver.find_element(By.ID, "lstLocations").find_elements(By.TAG_NAME, "option")
        ) > 1)

        selector = self.wait.until(EC.presence_of_element_located((By.ID, "lstLocations")))
        opciones = selector.find_elements(By.TAG_NAME, "option")
        localidades = [opt.text.strip() for opt in opciones if opt.get_attribute("value")]
        print(f"🏘️  Localidades encontradas: {len(localidades)}")
        return localidades

    def guardar_localidades(self, estado, municipio, localidades):
        nuevos = pd.DataFrame([
            {"estado": estado, "municipio": municipio, "localidad": loc, "status": "pendiente"}
            for loc in localidades
        ])
        self.df_localidades = pd.concat([self.df_localidades, nuevos])
        self.df_localidades.to_csv(self.output_csv, index=False)

    def actualizar_status_municipio(self, estado, municipio):
        actualizar_status_en_hoja(
            self.sheet_id,
            hoja=self.sheet_municipios,
            columna_busqueda_1="estado",
            valor_1=estado,
            columna_busqueda_2="municipio",
            valor_2=municipio,
            columna_estado="status",
            nuevo_estado="completado"
        )

    def subir_a_sheets(self):
        subir_csv_a_google_sheets_append(
            self.output_csv,
            sheet_id=self.sheet_id,
            hoja=self.sheet_localidades,
            start_col='B',
            skip_header=True
        )

    def ejecutar(self):
        self.open_siged()
        municipios = self.obtener_municipios_pendientes()
        print(f"🧭 Municipios pendientes a procesar: {len(municipios)}")

        for item in municipios:
            try:
                self.aplicar_filtros(item["estado"], item["municipio"])
                time.sleep(4)

                localidades = self.extraer_localidades()
                self.guardar_localidades(item["estado"], item["municipio"], localidades)
                self.actualizar_status_municipio(item["estado"], item["municipio"])

                self.subir_a_sheets()

                print(f"✅ {item['municipio']} procesado. Esperando 60 segundos...\n")
                time.sleep(60)
            except Exception as e:
                print(f"❌ Error con municipio {item['municipio']}: {e}")

        self.subir_a_sheets()
        self.cerrar()

    def cerrar(self):
        self.driver.quit()
