import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper.municipioScraper import MunicipioScraper
from scraper.siged_escuela_scraper import MunicipioEscuelaScraper

estado = "VERACRUZ DE IGNACIO DE LA LLAVE"
sheet_id="1wvJ9gJPP-Q4YQvtLX94YKnS04peSWR6S-LAck6dQcIU"

def municipioScraper():
    try:
        scraper = MunicipioScraper(estado)
        scraper.obtener_municipios()
    finally:
        scraper.cerrar()


def escuelaScraper():
    try:
        scraper = MunicipioEscuelaScraper(sheet_id)
        scraper.ejecutar()
    finally:
        scraper.cerrar()


if __name__ == "__main__":
    municipioScraper()
    #escuelaScraper()
    
    
