import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from utils.sheets_helper import subir_csv_a_google_sheets, subir_csv_a_google_sheets_append



class MunicipioScraper:
    BASE_URL = "https://www.siged.sep.gob.mx/SIGED/escuelas.html"

    def __init__(self, estado, output_csv="municipios.csv", headless=True):
        self.estado = estado
        self.output_csv = output_csv

        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

        # Cargar municipios existentes
        if os.path.exists(self.output_csv) and os.path.getsize(self.output_csv) > 0:
            self.df = pd.read_csv(self.output_csv)
        else:
            self.df = pd.DataFrame(columns=["estado", "municipio", "status"])


    def open(self):
        print("🌐 Abriendo sitio...")
        self.driver.get(self.BASE_URL)
        time.sleep(2)
        self.wait.until(EC.presence_of_element_located((By.ID, "lstStates")))
        print("✅ Página cargada.")

    def seleccionar_estado(self):
        print(f"📌 Buscando estado: {self.estado}")
        selector = self.wait.until(EC.presence_of_element_located((By.ID, "lstStates")))

        opciones = selector.find_elements(By.TAG_NAME, "option")
        print("🌍 Estados disponibles:")
        for opt in opciones:
            print(f"→ '{opt.text.strip()}'")

        # Ahora intentar seleccionar el correcto
        Select(selector).select_by_visible_text(self.estado)
        time.sleep(1)
        print("✅ Estado seleccionado.")


    def obtener_municipios(self):
        self.open()
        self.seleccionar_estado()

        selector = self.wait.until(EC.presence_of_element_located((By.ID, "lstMunicipalities")))
        opciones = selector.find_elements(By.TAG_NAME, "option")
        municipios = [opt.text.strip() for opt in opciones if opt.get_attribute("value")]

        print(f"🏙️ Municipios encontrados: {len(municipios)}")

        nuevos = 0
        for municipio in municipios:
            if not ((self.df["estado"] == self.estado) & (self.df["municipio"] == municipio)).any():
                print("→ Guardando:", municipio)
                self.df = pd.concat([
                    self.df,
                    pd.DataFrame([{
                        "estado": self.estado,
                        "municipio": municipio,
                        "status": "pendiente"
                    }])
                ])
                nuevos += 1

                # Guardar incrementalmente
                self.df.to_csv(self.output_csv, index=False)
                time.sleep(0.2)

        print(f"✅ Proceso completo. Municipios nuevos agregados: {nuevos}")
        if nuevos > 0:
            print("📤 Subiendo cambios a Google Sheets...")
            self.df.to_csv(self.output_csv, index=False)
            try:
                subir_csv_a_google_sheets_append(
                    self.output_csv,
                    sheet_id="1wvJ9gJPP-Q4YQvtLX94YKnS04peSWR6S-LAck6dQcIU",
                    hoja="municipios"
                )
                print("✅ Actualización en Google Sheets completa.")
            except Exception as e:
                print(f"⚠️ Error al subir a Google Sheets: {e}")
                print("⏳ Reintentando en 60 segundos...")
                time.sleep(60)
                try:
                    subir_csv_a_google_sheets_append(
                        self.output_csv,
                        sheet_id="1wvJ9gJPP-Q4YQvtLX94YKnS04peSWR6S-LAck6dQcIU",
                        hoja="municipios"
                    )
                    print("✅ Subida exitosa al reintentar.")
                except Exception as e2:
                    print(f"❌ Segundo intento fallido: {e2}")


    def cerrar(self):
        self.driver.quit()
