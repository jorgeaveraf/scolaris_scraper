import time
import pandas as pd
from utils.sheets_helper import (
    leer_hoja_como_df,
    actualizar_status_en_hoja,
    subir_csv_a_google_sheets_append
)
from scraper.siged_scraper import SigedScraper
from utils.normalizer import normalizar_texto

class MunicipioEscuelaScraper:
    def __init__(self,
                 sheet_id,
                 hoja_municipios="Municipios",
                 hoja_filtros="Filters",
                 hoja_escuelas="Escuelas"):
        self.sheet_id      = sheet_id
        self.hoja_municipios = hoja_municipios
        self.hoja_filtros   = hoja_filtros
        self.hoja_escuelas  = hoja_escuelas
        self.output_csv     = "escuelas.csv"

    def ejecutar(self):
        # 1) Cargo pendientes en Municipios
        df_muni   = leer_hoja_como_df(self.sheet_id, self.hoja_municipios)
        df_filtros = leer_hoja_como_df(self.sheet_id, self.hoja_filtros)
        pendientes = df_muni[df_muni["status"] == "pendiente"]

        if pendientes.empty:
            print("✅ No hay municipios pendientes.")
            return

        # 2) Tomo el primer municipio pendiente
        fila = pendientes.iloc[0]
        estado    = fila["estado"]
        municipio = fila["municipio"]
        print(f"🚀 Procesando municipio: {municipio} ({estado})")

        # 3) Arranco el scraper y limpio el CSV
        scraper = SigedScraper(debug=True)
        scraper.open()
        # escribo sólo encabezado
        columnas = ["nombre","cct","nivel","servicio_educativo","turno",
                    "entidad","municipio","localidad","direccion",
                    "codigo_postal","alumnos","docentes","grupos",
                    "aulas","computadoras"]
        pd.DataFrame(columns=columnas).to_csv(self.output_csv, index=False)

        # 4) Por cada combinación de filtros
        for idx, filtro in df_filtros.iterrows():
            combinacion = {
                "state":       estado,
                "municipality":municipio,
                "tipoEducativo": filtro["tipoEducativo"],
                "level":       filtro["nivel"],
                "sector":      filtro["sector"],
                "subcontrol":  filtro["subcontrol"],
            }
            print(f"\n🔍 Filtro {idx+1}/{len(df_filtros)} → {combinacion}")
            try:
                # 4.1) Aplico filtro
                scraper.aplicar_filtros(combinacion)
                time.sleep(2)

                # 4.2) Extraigo resultados
                scraper.extraer_resultados()

                # 4.3) Filtro sólo por municipio (por si hay desvíos)
                escuelas_validas = [
                    e for e in scraper.escuelas
                    if normalizar_texto(e.municipio) == normalizar_texto(municipio)
                ]

                # 4.4) Append a CSV sin encabezado
                pd.DataFrame([e.dict() for e in escuelas_validas]) \
                  .to_csv(self.output_csv,
                          mode='a',
                          header=False,
                          index=False)

                # 4.5) Subo este bloque a Sheets
                subir_csv_a_google_sheets_append(
                    self.output_csv,
                    sheet_id=self.sheet_id,
                    hoja=self.hoja_escuelas,
                    skip_header=True,
                    start_col='B',
                )
                print(f"✅ Filtro {idx+1} subido a '{self.hoja_escuelas}'.")

                # 4.6) Limpio lista para próxima iteración
                scraper.escuelas.clear()

            except Exception as e:
                print(f"❌ Error en filtro {idx+1}: {e}")

        scraper.cerrar()

        # 5) Marco el municipio como completado
        actualizar_status_en_hoja(
            sheet_id=self.sheet_id,
            hoja=self.hoja_municipios,
            columna_busqueda_1="estado",
            valor_1=estado,
            columna_busqueda_2="municipio",
            valor_2=municipio,
            columna_estado="status",
            nuevo_estado="completado"
        )
        print(f"📌 Municipio '{municipio}' marcado como completado.\n")
