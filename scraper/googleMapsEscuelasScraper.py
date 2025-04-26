# scraper/googleMapsEscuelasScraper.py
from scraper.maps_scraper import GoogleMapsDataEnricher
from utils.sheets_helper import (
    leer_hoja_como_df,
    append_column_data,
    actualizar_status_en_sheet,
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
        df_pendientes = df[df["status"].str.lower() == "pendiente"]

        columnas_nuevas = ['telefono', 'correo', 'pagina_web', 'horario', 'extra_info']

        # Inicializar navegador
        options = Options()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=options)
        enricher = GoogleMapsDataEnricher(driver)

        for _, row in df_pendientes.iterrows():
            nombre = row["nombre"]
            print(f"\n🚀 Procesando: {nombre}")

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
                print(f"✅ Datos subidos para: {nombre}")
            else:
                print(f"⚠️ Sin datos útiles. {nombre} se mantiene como 'pendiente'.")

        driver.quit()
        print("\n🏁 Proceso finalizado.")
