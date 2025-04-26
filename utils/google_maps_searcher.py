from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class GoogleMapsSearcher:
    def __init__(self, driver):
        self.driver = driver
        self.url = "https://www.google.com/maps"

    def buscar_escuela(self, query):
        self.driver.get(self.url)
        try:
            input_box = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            input_box.clear()
            input_box.send_keys(query)
            input_box.send_keys(Keys.ENTER)

            # 🔍 Esperamos resultado directo (perfil de lugar)
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1 span, .DUwDvf"))
                )
                return True
            except TimeoutException:
                # 🪄 Si no se carga un perfil directo, clic en el primer resultado
                first_result = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".Nv2PK")))
                first_result.click()

                # Esperamos ahora el modal del lugar
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1 span, .DUwDvf"))
                )
                return True

        except Exception as e:
            print(f"[ERROR] Fallo búsqueda para: {query} → {e}")
            return False
