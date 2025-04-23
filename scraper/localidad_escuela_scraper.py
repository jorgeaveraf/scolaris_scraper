import time
import pandas as pd
from utils.sheets_helper import (
    leer_hoja_como_df,
    actualizar_status_en_hoja,
    subir_csv_a_google_sheets_append
)
from utils.filter_helper import filtrar_por_localidad
from scraper.siged_scraper import SigedScraper

class LocalidadEscuelaScraper:
    def __init__(self,
                 sheet_id,
                 hoja_localidades="Localidades",
                 hoja_filtros="Filters",
                 hoja_escuelas="Escuelas"):
        self.sheet_id = sheet_id
        self.hoja_localidades = hoja_localidades
        self.hoja_filtros   = hoja_filtros
        self.hoja_escuelas  = hoja_escuelas
        self.output_csv     = "escuelas.csv"

    def ejecutar(self):
        df_localidades = leer_hoja_como_df(self.sheet_id, self.hoja_localidades)
        df_filtros    = leer_hoja_como_df(self.sheet_id, self.hoja_filtros)

        pendientes = df_localidades[df_localidades["status"] == "pendiente"]
        if pendientes.empty:
            print("✅ No hay localidades pendientes por procesar.")
            return

        # Tomamos la primera pendiente
        localidad_obj = pendientes.iloc[0]
        estado    = localidad_obj["estado"]
        municipio = localidad_obj["municipio"]
        localidad = localidad_obj["localidad"]

        print(f"🚀 Procesando localidad: {localidad} ({municipio}, {estado})")

        scraper = SigedScraper(debug=True)
        scraper.open()

        # Nos aseguramos de partir con CSV vacío
        pd.DataFrame().to_csv(self.output_csv, index=False)

        # Iteramos cada combinación de filtros
        for idx, filtro in df_filtros.iterrows():
            time.sleep(2)
            combinacion = {
                "state":       estado,
                "municipality":municipio,
                "olocation":   localidad,
                "tipoEducativo": filtro["tipoEducativo"],
                "level":       filtro["nivel"],
                "subnivel":    filtro["subnivel"],
                "sector":      filtro["sector"],
                "subcontrol":  filtro["subcontrol"],
                "schedule":    filtro["schedule"]
            }

            print(f"🔍 Filtro {idx+1}/{len(df_filtros)} → {combinacion}")
            try:
                # 1) Aplico filtro
                scraper.aplicar_filtros(combinacion)
                time.sleep(2)

                # 2) Extraigo resultados
                scraper.extraer_resultados()

                # 3) Me quedo sólo con la localidad correcta
                escuelas_filtradas = filtrar_por_localidad(scraper.escuelas, localidad)

                # 4) Vuelco sólo **este bloque** al CSV
                pd.DataFrame([e.dict() for e in escuelas_filtradas]) \
                  .to_csv(self.output_csv, mode='a', header=False, index=False)

                # 5) Lo subo a Sheets (skip_header porque ya tengo encabezado en A1…)
                subir_csv_a_google_sheets_append(
                    self.output_csv,
                    sheet_id=self.sheet_id,
                    hoja=self.hoja_escuelas,
                    start_col='B',
                    skip_header=True
                )
                print(f"✅ Filtro {idx+1} subido a hoja '{self.hoja_escuelas}'.")

                # 6) ¡Y limpio para la próxima iteración!
                scraper.escuelas.clear()

            except Exception as e:
                print(f"❌ Error en filtro {idx+1}: {e}")

        scraper.cerrar()

        # Marcamos la localidad como procesada
        actualizar_status_en_hoja(
            sheet_id=self.sheet_id,
            hoja=self.hoja_localidades,
            columna_busqueda_1="estado",
            valor_1=estado,
            columna_busqueda_2="municipio",
            valor_2=municipio,
            columna_estado="status",
            nuevo_estado="completado"
        )
        print(f"📌 Localidad marcada como completada en '{self.hoja_localidades}'.")

        print("✅ Terminado procesamiento de localidad.\n")

