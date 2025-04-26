# runner/ejecutar_scraper_maps.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.googleMapsEscuelasScraper import GoogleMapsEscuelasScraper

def main():
    sheet_id = "1wvJ9gJPP-Q4YQvtLX94YKnS04peSWR6S-LAck6dQcIU"
    scraper = GoogleMapsEscuelasScraper(sheet_id=sheet_id, hoja_escuelas="Escuelas")
    scraper.ejecutar()

if __name__ == "__main__":
    main()
