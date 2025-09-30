import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_monapart(city: str):
    # Configuración de Selenium en modo headless
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    city = city.lower()
    driver = webdriver.Chrome(options=options)
    driver.get(f'https://www.monapart.com/agentes/{city}')

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.mon-link.link-primary')))
    print('cargado')

    # Enlaces de los agentes
    agent_links = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "a.mon-link.link-primary")]
    agent_links = set(agent_links) # eliminar duplicados
    agent_links = list(agent_links)

    data = []
    print(agent_links)

    for link in agent_links:
        driver.get(link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='mailto:']")))

        # Extraer datos
        try:
            name = driver.find_element(By.CSS_SELECTOR, "h1").text.strip().split('\n')[0]
        except:
            print('name not found')
            name = ""

        try:
            phone = driver.find_element(By.CSS_SELECTOR, "a[href^='tel:']").text.strip()
        except:
            phone = ""

        try:
            email = driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")[1].text.strip()
        except:
            email = ""

        try:
            area = driver.find_element(
                By.XPATH,
                "//div[contains(text(), 'ÁREA')]/following-sibling::div[1]"
            ).text.strip()
        except:
            area = "Barcelona"

        try:
            comment = driver.find_element(By.XPATH, "//div[contains(text(), 'años')]").text.strip()
        except:
            comment = ""

        data.append({
            "nombre": name,
            "contacto telefonico": phone,
            "correo electrónico": email,
            "area": area,
            "comentario (años de experiencia)": comment,
            "url": link
        })

    print(data)
    driver.quit() # cerrar driver

    # Guardar CSV
    df = pd.DataFrame(data)
    file_path = f'../monapart/{city}.csv'
    df.to_csv(file_path, index=False, encoding="utf-8")
    print(f"Archivo CSV creado: {file_path}")


if __name__ == "__main__":
    scrape_monapart(city='Madrid')
