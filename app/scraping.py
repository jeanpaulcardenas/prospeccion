import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def scrape_monapart_barcelona(output_csv="monapart_barcelona_agentes.csv"):
    # Configuración de Selenium en modo headless
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.monapart.com/agentes/madrid")

    time.sleep(5)  # esperar a que cargue
    print('cargado')

    # Enlaces de los agentes
    agent_links = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "a.mon-link.link-primary")]
    agent_links = set(agent_links) # eliminar duplicados
    agent_links = list(agent_links)

    data = []
    print(agent_links)

    for link in agent_links:
        driver.get(link)
        time.sleep(5) # esperar

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
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Archivo CSV creado: {output_csv}")


if __name__ == "__main__":
    scrape_monapart_barcelona(output_csv='monapart_madrid.csv')
