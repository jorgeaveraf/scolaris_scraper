import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper.siged_scraper import SigedScraper
from scraper.municipioScraper import MunicipioScraper
from scraper.localidadScraper import LocalidadScraper
from scraper.localidad_escuela_scraper import MunicipioEscuelaScraper

estado = "VERACRUZ DE IGNACIO DE LA LLAVE"
sheet_id="1wvJ9gJPP-Q4YQvtLX94YKnS04peSWR6S-LAck6dQcIU"

def run():
    scraper = SigedScraper()
    try:
        scraper.open()
        scraper.aplicar_filtros()
        scraper.extraer_resultados()
        scraper.exportar_csv()
    finally:
        scraper.cerrar()

def municipioScraper():
    try:
        scraper = MunicipioScraper(estado)
        scraper.obtener_municipios()
    finally:
        scraper.cerrar()

def localidadScraper():
    try:
        scraper = LocalidadScraper(estado, sheet_id)
        scraper.ejecutar()
    finally:
        scraper.cerrar()

def escuelaScraper():
    try:
        scraper = MunicipioEscuelaScraper(sheet_id)
        scraper.ejecutar()
    finally:
        scraper.cerrar()


if __name__ == "__main__":
    #run()
    #municipioScraper()
    #localidadScraper()
    escuelaScraper()
    
    
