from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re

url = "https://codigospostales.com/nestcp.cgi?28"

chrome_options = Options()
chrome_options.add_argument("--headless=new")
driver = webdriver.Chrome(options=chrome_options)
driver.get(url)

# Diccionario final
cp_por_ciudad = {}

# Encuentra todos los fieldsets (cada uno es una ciudad)
fieldsets = driver.find_elements(By.TAG_NAME, "fieldset")

for fs in fieldsets:
    # --- Obtener nombre de ciudad ---
    legend = fs.find_element(By.TAG_NAME, "legend").text.strip()

    # Extraer el nombre después de "de"
    if "resto de la provincia" in legend.lower():
        ciudad = "resto"
    else:
        m = re.search(r"Códigos postales de\s+(.*)", legend, re.IGNORECASE)
        ciudad = m.group(1).strip() if m else legend

    # --- Obtener códigos postales dentro del <ul> ---
    codigos = [a.text.strip() for a in fs.find_elements(By.XPATH, ".//ul[@class='grande']//a") if
               a.text.strip().isdigit()]

    cp_por_ciudad[ciudad] = codigos

driver.quit()

# Mostrar resultado
for ciudad, codigos in cp_por_ciudad.items():
    print(f"{ciudad}: {len(codigos)} códigos")
    print(codigos[:10], "...\n")
