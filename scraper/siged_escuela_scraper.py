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
        df_filtros = leer_hoja_como_df(self.sheet_id, self.hoja_filtros)
        
        while True:
            # 1) Releer municipios pendientes en cada ciclo
            df_muni = leer_hoja_como_df(self.sheet_id, self.hoja_municipios)
            pendientes = df_muni[df_muni["status"] == "pendiente"]

            if pendientes.empty:
                print("✅ No hay más municipios pendientes.")
                break

            # 2) Tomar el primer municipio pendiente
            fila = pendientes.iloc[0]
            estado = fila["estado"]
            municipio = fila["municipio"]
            print(f"\n🚀 Procesando municipio: {municipio} ({estado})")

            # 3) Iniciar scraper
            scraper = SigedScraper(debug=True)
            scraper.open()

            # Reiniciar el CSV (con encabezado)
            columnas = ["nombre", "cct", "nivel", "servicio_educativo", "turno",
                        "entidad", "municipio", "localidad", "direccion",
                        "codigo_postal", "alumnos", "docentes", "grupos",
                        "aulas", "computadoras"]
            pd.DataFrame(columns=columnas).to_csv(self.output_csv, index=False)

            # 4) Ejecutar todos los filtros
            for idx, filtro in df_filtros.iterrows():
                combinacion = {
                    "state": estado,
                    "municipality": municipio,
                    "tipoEducativo": filtro["tipoEducativo"],
                    "level": filtro["nivel"],
                    "sector": filtro["sector"],
                    "subcontrol": filtro["subcontrol"],
                }
                print(f"\n🔍 Filtro {idx+1}/{len(df_filtros)} → {combinacion}")
                try:
                    scraper.aplicar_filtros(combinacion)
                    time.sleep(2)

                    scraper.extraer_resultados()

                    escuelas_validas = [
                        e for e in scraper.escuelas
                        if normalizar_texto(e.municipio) == normalizar_texto(municipio)
                    ]

                    pd.DataFrame([e.dict() for e in escuelas_validas]) \
                        .to_csv(self.output_csv, mode='a', header=False, index=False)

                    subir_csv_a_google_sheets_append(
                        self.output_csv,
                        sheet_id=self.sheet_id,
                        hoja=self.hoja_escuelas,
                        skip_header=True,
                        start_col='B',
                    )

                    print(f"✅ Filtro {idx+1} subido a '{self.hoja_escuelas}'.")
                    scraper.escuelas.clear()

                except Exception as e:
                    print(f"❌ Error en filtro {idx+1}: {e}")

            scraper.cerrar()

            # 5) Actualizar status del municipio como completado
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
