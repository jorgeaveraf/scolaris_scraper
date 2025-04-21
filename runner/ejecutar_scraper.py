import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper.siged_scraper import SigedScraper

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
    run()
