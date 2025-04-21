from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from models.escuela import Escuela
import pandas as pd
import time

class SigedScraper:
    BASE_URL = "https://www.siged.sep.gob.mx/SIGED/escuelas.html"
    PANEL_DIRECCION = "panel-02"
    PANEL_ESTADISTICAS = "panel-04"

    def __init__(self, headless=True, debug=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.escuelas = []
        self.debug = debug

    def log(self, msg):
        if self.debug:
            print(msg)

    def open(self):
        self.driver.get(self.BASE_URL)
        self.log("Esperando que cargue el DOM completo...")
        time.sleep(5)

    def _get_filtros(self, **kwargs):
        base = {
            'state': "VERACRUZ DE IGNACIO DE LA LLAVE",
            'municipality': "ORIZABA",
            'olocation': "ORIZABA",
            'tipoEducativo': "INICIAL",
            'level': "INICIAL",
            'subnivel': "LACTANTE Y MATERNAL",
            'sector': "PRIVADO",
            'subcontrol': "PRIVADO",
            'schedule': "MATUTINO"
        }
        base.update(kwargs)
        return base


    def aplicar_filtros(self, filtros=None):
        if filtros is None:
            filtros = self._get_filtros()

        self.log("Esperando que cargue el formulario de filtros...")
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'Entidad')]")))
        self.log("Formulario cargado")

        for ng_model, valor in filtros.items():
            try:
                selector_xpath = f"//select[@ng-model='{ng_model}']"
                campo = self.wait.until(EC.presence_of_element_located((By.XPATH, selector_xpath)))
                campo.click()
                campo.send_keys(valor)
                self.log(f"✓ {ng_model} → {valor}")
                time.sleep(0.5)
            except Exception as e:
                self.log(f"⚠️ No se pudo seleccionar {ng_model}: {e}")

        buscar_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Buscar')]")
        ))
        buscar_btn.click()
        self.log("✅ Filtros aplicados correctamente.")

    def extraer_resultados(self):
        self.wait.until(EC.presence_of_element_located((By.ID, "sectionResultWithData")))
        self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table//tbody/tr")))

        filas = self.driver.find_elements(By.XPATH, "//table//tbody/tr")
        self.log(f"🔎 Filas detectadas: {len(filas)}")

        for idx, fila in enumerate(filas, 1):
            try:
                columnas = fila.find_elements(By.TAG_NAME, "td")
                nombre_tabla = columnas[6].text
                cct = columnas[0].text
                self.log(f"\n📌 {idx}. {cct} - {nombre_tabla}")

                self.driver.execute_script("arguments[0].scrollIntoView(true);", fila)
                self.driver.execute_script("arguments[0].click();", fila)

                self.wait.until(EC.visibility_of_element_located((By.ID, "modal_datos_escuela")))
                self.wait.until(EC.invisibility_of_element_located((By.ID, "cargando_escuela")))
                time.sleep(1)

                self.expandir_paneles_info()
                self.esperar_datos_modal()

                detalle = self.extraer_detalle_escuela()
                self.log(f"🧩 Detalle obtenido: {detalle}")

                escuela = Escuela(
                    nombre=columnas[5].text,
                    cct=cct,
                    entidad=detalle.get("estado"),
                    municipio=detalle.get("municipio"),
                    localidad=detalle.get("localidad"),
                    nivel=columnas[4].text,
                    servicio_educativo=columnas[7].text,
                    turno=columnas[8].text,
                    direccion=detalle.get("direccion"),
                    codigo_postal=detalle.get("codigo_postal"),
                    alumnos=detalle.get("alumnos"),
                    docentes=detalle.get("docentes"),
                    grupos=detalle.get("grupos"),
                    aulas=detalle.get("aulas"),
                    computadoras=detalle.get("computadoras")
                )
                self.escuelas.append(escuela)

            except Exception as e:
                self.log(f"❌ Error al procesar fila {idx}: {e}")

            finally:
                try:
                    cerrar_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cerrar')]")))
                    cerrar_btn.click()
                    self.wait.until(EC.invisibility_of_element_located((By.ID, "modal_datos_escuela")))
                except:
                    self.log("⚠️ No se pudo cerrar el modal.\n")

    def expandir_panel(self, panel_id):
        try:
            toggle = self.driver.find_element(By.XPATH, f"//a[@href='#{panel_id}']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", toggle)
            toggle.click()
            self.wait.until(EC.visibility_of_element_located((By.ID, panel_id)))
            return True
        except Exception as e:
            self.log(f"❌ No se pudo expandir {panel_id}: {e}")
            return False

    def expandir_paneles_info(self):
        self.expandir_panel(self.PANEL_DIRECCION)
        self.expandir_panel(self.PANEL_ESTADISTICAS)

    def esperar_datos_modal(self):
        self.wait.until(lambda d: d.find_element(By.CSS_SELECTOR, f"#{self.PANEL_DIRECCION} .ng-binding").text.strip() != "")

    def extraer_detalle_escuela(self):
        try:
            html02 = self.driver.find_element(By.ID, self.PANEL_DIRECCION).get_attribute("innerHTML")
            html04 = self.driver.find_element(By.ID, self.PANEL_ESTADISTICAS).get_attribute("innerHTML")
            soup02 = BeautifulSoup(html02, 'html.parser')
            soup04 = BeautifulSoup(html04, 'html.parser')

            return {
                "estado": self._buscar_texto(soup02, "Entidad:"),
                "municipio": self._buscar_texto(soup02, "Municipio:"),
                "localidad": self._buscar_texto(soup02, "Localidad:"),
                "direccion": self._buscar_texto(soup02, "Dirección:"),
                "codigo_postal": self._buscar_texto(soup02, "Código Postal:"),
                "alumnos": self._buscar_valor_campo(soup04, "Número de niñas") + self._buscar_valor_campo(soup04, "Número de niños"),
                "docentes": self._buscar_valor_campo(soup04, "Número de maestras") + self._buscar_valor_campo(soup04, "Número de maestros"),
                "grupos": self._buscar_valor_campo(soup04, "Grupos"),
                "aulas": self._buscar_valor_campo(soup04, "Aulas"),
                "computadoras": self._buscar_valor_campo(soup04, "Computadoras")
            }
        except Exception as e:
            self.log(f"❌ Error extrayendo detalles: {e}")
            return {}

    def _buscar_texto(self, soup, campo):
        divs = soup.find_all("div")
        for i, div in enumerate(divs):
            if div.text.strip() == campo and i + 1 < len(divs):
                return divs[i + 1].text.strip()
        return ""

    def _buscar_valor_campo(self, soup, campo):
        textos = [t.strip() for t in soup.get_text(separator="\n").split("\n") if t.strip()]
        for i, linea in enumerate(textos):
            if campo in linea and i + 1 < len(textos):
                siguiente = textos[i + 1]
                return self._extraer_numero(siguiente)
        return 0

    def _extraer_numero(self, texto):
        digits = ''.join(filter(str.isdigit, texto))
        return int(digits) if digits else 0

    def exportar_csv(self, ruta="escuelas.csv"):
        df = pd.DataFrame([e.dict() for e in self.escuelas])
        df.to_csv(ruta, index=False)

    def cerrar(self):
        self.driver.quit()
