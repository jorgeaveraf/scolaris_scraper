import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper.siged_scraper import SigedScraper
from scraper.municipioScraper import MunicipioScraper

def run():
    scraper = SigedScraper()
    try:
        scraper.open()
        scraper.aplicar_filtros()
        scraper.extraer_resultados()
        scraper.exportar_csv()
    finally:
        scraper.cerrar()

if __name__ == "__main__":
    """ run() """
    estado = "VERACRUZ DE IGNACIO DE LA LLAVE"
    sheet_id = "1wvJ9gJPP-Q4YQvtLX94YKnS04peSWR6S-LAck6dQcIU"
    
    scraper = MunicipioScraper(estado)
    scraper.obtener_municipios()
    scraper.cerrar()
