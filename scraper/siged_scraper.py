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

    def __init__(self, headless=True):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.escuelas = []

    def open(self):
        self.driver.get(self.BASE_URL)
        print("Esperando que cargue el DOM completo...")
        time.sleep(5)
        print(self.driver.page_source[:1000])  # imprime un fragmento para confirmar que está cargando

        print("¡Iframe cargado! Listo para aplicar filtros.")

        selects = self.driver.find_elements(By.TAG_NAME, "select")
        print(f"Se encontraron {len(selects)} elementos <select>")

        for i, select in enumerate(selects):
            print(f"\n[{i}]")
            print(select.get_attribute("outerHTML"))

    def aplicar_filtros(self):
        print("Esperando que cargue el formulario de filtros...")
        self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//label[contains(text(),'Entidad')]")
        ))
        print("Formulario cargado")

        filtros = {
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

        for ng_model, valor in filtros.items():
            try:
                selector_xpath = f"//select[@ng-model='{ng_model}']"
                campo = self.wait.until(EC.presence_of_element_located((By.XPATH, selector_xpath)))
                campo.click()
                campo.send_keys(valor)
                print(f"✓ {ng_model} → {valor}")
                time.sleep(0.5)  # Evita que Angular se trabe en cascada
            except Exception as e:
                print(f"⚠️ No se pudo seleccionar {ng_model}: {e}")

        # Botón de buscar
        buscar_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Buscar')]")
        ))
        buscar_btn.click()
        print("✅ Filtros aplicados correctamente.")


    
    def extraer_resultados(self):
        print("Esperando resultados...")
        self.wait.until(EC.presence_of_element_located((By.ID, "sectionResultWithData")))
        self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table//tbody/tr")))

        filas = self.driver.find_elements(By.XPATH, "//table//tbody/tr")
        print(f"🔎 Filas detectadas: {len(filas)}")

        for idx, fila in enumerate(filas, 1):
            try:
                columnas = fila.find_elements(By.TAG_NAME, "td")
                nombre_tabla = columnas[6].text
                cct = columnas[0].text
                print(f"\n📌 {idx}. {cct} - {nombre_tabla}")

                self.driver.execute_script("arguments[0].scrollIntoView(true);", fila)
                self.driver.execute_script("arguments[0].click();", fila)

                self.wait.until(EC.visibility_of_element_located((By.ID, "modal_datos_escuela")))
                self.wait.until(EC.invisibility_of_element_located((By.ID, "cargando_escuela")))
                time.sleep(1)

                self.expandir_panel("panel-02")
                self.expandir_panel("panel-04")
                self.esperar_datos_modal()
                time.sleep(1)

                detalle = self.extraer_detalle_escuela()
                print("🧩 Detalle obtenido:", detalle)

                escuela = Escuela(
                    nombre=nombre_tabla,
                    cct=cct,
                    entidad=detalle.get("estado"),
                    municipio=detalle.get("municipio"),
                    localidad=detalle.get("localidad"),
                    nivel=columnas[4].text,
                    servicio_educativo=columnas[5].text,
                    turno=detalle.get("turno", ""),
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
                print(f"❌ Error al procesar fila {idx}: {e}")

            finally:
                try:
                    cerrar_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cerrar')]")))
                    cerrar_btn.click()
                    self.wait.until(EC.invisibility_of_element_located((By.ID, "modal_datos_escuela")))
                except:
                    print("⚠️ No se pudo cerrar el modal.\n")


    def expandir_panel(self, panel_id):
        try:
            toggle = self.driver.find_element(By.XPATH, f"//a[@href='#{panel_id}']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", toggle)
            toggle.click()
            print(f"⏬ Panel {panel_id} expandido.")
            self.wait.until(EC.visibility_of_element_located((By.ID, panel_id)))
            return True
        except Exception as e:
            print(f"❌ No se pudo expandir {panel_id}:", e)
            return False


    def esperar_datos_modal(self):
        print("⌛ Esperando que Angular rellene los datos...")
        self.wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "#panel-02 .ng-binding").text.strip() != "")
        print("✅ Datos cargados correctamente.")



    def extraer_detalle_escuela(self):
        try:
            self.expandir_panel("panel-02")
            self.expandir_panel("panel-04")

            print("⌛ Esperando que Angular rellene los datos...")
            self.wait.until(lambda d: "Dirección" in d.find_element(By.ID, "panel-02").text or 
                                    "Entidad" in d.find_element(By.ID, "panel-02").text)
            print("✅ Datos cargados correctamente.")

            html02 = self.driver.find_element(By.ID, "panel-02").get_attribute("innerHTML")
            html04 = self.driver.find_element(By.ID, "panel-04").get_attribute("innerHTML")

            soup02 = BeautifulSoup(html02, 'html.parser')
            soup04 = BeautifulSoup(html04, 'html.parser')

            def buscar_texto(campo):
                divs = soup02.find_all("div")
                for i, div in enumerate(divs):
                    if div.text.strip() == campo and i + 1 < len(divs):
                        return divs[i + 1].text.strip()
                return ""

            def buscar_valor_campo(soup, campo):
                textos = [t.strip() for t in soup.get_text(separator="\n").split("\n") if t.strip()]
                for i, linea in enumerate(textos):
                    if campo in linea and i + 1 < len(textos):
                        siguiente_valor = textos[i + 1]
                        try:
                            return int(siguiente_valor)
                        except ValueError:
                            return 0
                return 0


            entidad = buscar_texto("Entidad:")
            municipio = buscar_texto("Municipio:")
            localidad = buscar_texto("Localidad:")
            direccion = buscar_texto("Dirección:")
            codigo_postal = buscar_texto("Código Postal:")

            return {
                "estado": entidad,
                "municipio": municipio,
                "localidad": localidad,
                "direccion": direccion,
                "codigo_postal": codigo_postal,
                "alumnos": buscar_valor_campo(soup04, "Número de niñas") + buscar_valor_campo(soup04, "Número de niños"),
                "docentes": buscar_valor_campo(soup04, "Número de maestras") + buscar_valor_campo(soup04, "Número de maestros"),
                "grupos": buscar_valor_campo(soup04, "Grupos"),
                "aulas": buscar_valor_campo(soup04, "Aulas"),
                "computadoras": buscar_valor_campo(soup04, "Computadoras")
            }

        except Exception as e:
            print("❌ Error extrayendo detalles:", e)
            return {}


    def _seguro(self, valor):
        return valor if isinstance(valor, int) else 0

    def _extraer_numero(self, texto):
        digits = ''.join(filter(str.isdigit, texto))
        return int(digits) if digits else 0

    def buscar_numerico(self, campo, texto):
        for line in texto.split("\n"):
            if campo in line:
                digits = ''.join(filter(str.isdigit, line))
                return int(digits) if digits else None
        return None

    def exportar_csv(self, ruta="escuelas.csv"):
        df = pd.DataFrame([e.dict() for e in self.escuelas])
        df.to_csv(ruta, index=False)

    def cerrar(self):
        self.driver.quit()
