# tests/test_smoke_app.py
import os
from selenium.webdriver.common.by import By
from selenium import webdriver
import pytest


@pytest.fixture
def browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_smoke_test(browser):
    """SMOKE TEST: Verifica carga básica y título."""
    app_url = os.environ.get("APP_BASE_URL", "http://localhost:5000")
    print(f"Smoke test ejecutándose contra: {app_url}")
    try:
        browser.get(app_url + "/")
        print(f"Título de la página: {browser.title}")
        assert "Calculadora" in browser.title
        h1_element = browser.find_element(By.TAG_NAME, "h1")
        print(f"Texto H1: {h1_element.text}")
        assert h1_element.text == "Calculadora"
        print("Smoke test pasado exitosamente.")
    except Exception as e:
        print(f"Smoke test falló: {e}")
        raise
