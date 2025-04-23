from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webdriver import WebDriver
from .normalizer import normalizar_texto


def get_selected_option(driver: WebDriver, by_locator: tuple) -> str:
    """
    Devuelve el texto de la opción actualmente seleccionada en un <select>.
    by_locator debe ser una tupla (By.ID, 'lstStates'), etc.
    """
    select_el = Select(driver.find_element(*by_locator))
    return select_el.first_selected_option.text.strip()


def select_if_different(driver: WebDriver, by_locator: tuple, visible_text: str):
    """
    Selecciona la opción visible_text solo si difiere de la actualmente seleccionada.
    Use normalización para evitar errores por mayúsculas/acentos.
    """
    select_el = Select(driver.find_element(*by_locator))
    current = select_el.first_selected_option.text.strip()
    if normalizar_texto(current) != normalizar_texto(visible_text):
        select_el.select_by_visible_text(visible_text)
        return True
    return False
