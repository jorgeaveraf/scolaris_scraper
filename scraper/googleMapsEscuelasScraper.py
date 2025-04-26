# scraper/googleMapsEscuelasScraper.py
from scraper.maps_scraper import GoogleMapsDataEnricher
from utils.sheets_helper import (
    leer_hoja_como_df,
    append_column_data,
    actualizar_status_en_sheet
)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd

class GoogleMapsEscuelasScraper:
    def __init__(self, sheet_id, hoja_escuelas="Escuelas"):
        self.sheet_id = sheet_id
        self.hoja_escuelas = hoja_escuelas
        self.output_csv = "escuelas_enriquecidas.csv"

    def ejecutar(self):
        print("📥 Leyendo hoja de cálculo...")
        df = leer_hoja_como_df(self.sheet_id, self.hoja_escuelas)
        columnas_nuevas = ['telefono', 'pagina_web', 'horario', 'extra_info']

        # Filtrar solo las filas pendientes
        df_pendientes = df[df["status"].str.lower() == "pendiente"]

        if df_pendientes.empty:
            print("✅ No hay escuelas pendientes.")
            return

        # Inicializar navegador
        options = Options()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=options)
        enricher = GoogleMapsDataEnricher(driver)

        for _, row in df_pendientes.iterrows():
            nombre = row["nombre"]
            print(f"🔍 Procesando: {nombre}")

            datos = enricher.enriquecer_fila(row)

            if datos and any(datos.values()):
                df_update = pd.DataFrame([{"nombre": nombre, **datos}])

                append_column_data(
                    sheet_id=self.sheet_id,
                    hoja=self.hoja_escuelas,
                    id_columna="nombre",
                    df_nuevo=df_update[["nombre"] + columnas_nuevas]
                )

                actualizar_status_en_sheet(
                    sheet_id=self.sheet_id,
                    hoja=self.hoja_escuelas,
                    id_columna="nombre",
                    id_valor=nombre,
                    columna_status="status",
                    nuevo_estado="completado"
                )

                print(f"✅ Datos subidos y estado actualizado para: {nombre}\n")
            else:
                print(f"⚠️ No se extrajo información para: {nombre}. Se mantiene como pendiente.\n")

        driver.quit()
