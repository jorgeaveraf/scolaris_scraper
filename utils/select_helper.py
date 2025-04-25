from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.remote.webdriver import WebDriver
from .normalizer import normalizar_texto


def get_selected_option(driver: WebDriver, by_locator: tuple) -> str:
    """
    Devuelve el texto de la opción actualmente seleccionada en un <select>.
    by_locator debe ser una tupla (By.ID, 'lstStates'), etc.
    """
    select_el = Select(driver.find_element(*by_locator))
    return select_el.first_selected_option.text.strip()


def select_if_different(driver: WebDriver, locator: tuple, visible_text: str) -> bool:
    """
    Selecciona la opción visible_text solo si difiere de la actualmente seleccionada.
    Usa normalización para evitar errores por mayúsculas/acentos.
    Devuelve True si hubo cambio.
    """
    # 1) Localiza el <select> y sea visible
    el = driver.find_element(*locator)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)

    sel = Select(el)
    current = sel.first_selected_option.text.strip()

    # 2) Compara normalizado
    if normalizar_texto(current) != normalizar_texto(visible_text):
        # 3) Intenta click nativo, si falla, fallback a JS
        try:
            el.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", el)
        # 4) Selecciona la opción
        sel.select_by_visible_text(visible_text)
        return True

    return False
