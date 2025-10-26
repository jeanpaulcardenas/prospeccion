import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def wait_css_located(driver: webdriver.Chrome, css_selector: str, time: int = 10) -> None:
    WebDriverWait(driver, time).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))


def default_options() -> Options:
    """return options as headless, disabled gpy and no sandbox"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return options


def scrape_monapart(city: str):
    agent_anchor = "a.mon-link.link-primary"
    options = default_options()
    city = city.lower()
    driver = webdriver.Chrome(options=options)
    driver.get(f'https://www.monapart.com/agentes/{city}')

    wait_css_located(driver, agent_anchor)
    print('cargado')

    # Enlaces de los agentes
    agent_links = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "a.mon-link.link-primary")]
    agent_links = set(agent_links)  # eliminar duplicados
    agent_links = list(agent_links)

    data = []
    print(agent_links)

    for link in agent_links:
        driver.get(link)
        wait_css_located(driver, "a[href^='mailto:']")

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
    driver.quit()  # cerrar driver

    # Guardar CSV
    df = pd.DataFrame(data)
    file_path = f'C:/Users/Jean/Desktop/prospeccion/monapart/{city}.csv'
    df.to_csv(file_path, index=False, encoding="utf-8")
    print(f"Archivo CSV creado: {file_path}")


class RemaxScraper:
    _options = default_options()
    _BASE_URL = 'https://www.remax.es/buscador-de-agentes/'
    _CSS_SELECTORS = {
        'lead_name': 'span.titulo-ficha-propiedad',
        'address': 'span.box_ubicacion_oficina',
        'role': 'span.cargo_agente',
        'agency': 'span.box_nombre_oficina',
        'contact_number': 'a[href^="tel:"]',
        'e-mail': 'a[href^="mailto:"]',
        'next_page': 'ul.pagination a.arrow-next',
        'agent_page_link': 'span.nombre_agente a'
    }

    def __init__(self, city: str = ''):
        """city debe ser la ciudad. Puede ser aceptado ciudades como Madrid, Barcelona, etc y en en caso de querer
        municipios o sub regiones dentro de una ciudad de la forma 'madrid/majadaonda'"""

        self.driver = webdriver.Chrome(self._options)
        self.city = city.lower()
        self.page = 'remax'
        self.base_url = self._BASE_URL + self.city
        print(self.base_url)
        self.driver.get(self.base_url)
        wait_css_located(self.driver, css_selector=self._CSS_SELECTORS['agent_page_link'])
        self.agents = []
        self.agents_df = pd.DataFrame()

    def _get_page_agent_links(self):
        try:
            time.sleep(2)
            anchors = self.driver.find_elements(By.CSS_SELECTOR, self._CSS_SELECTORS['agent_page_link'])
            links = [a.get_attribute('href') for a in anchors]
            print(links)
            return links
        except TimeoutException as e:
            print(e)
            return []

    def _get_agent_info(self):
        css_selects = self._CSS_SELECTORS
        try:
            agent = {
                'lead_name':
                    self.driver.find_element(By.CSS_SELECTOR, css_selects['lead_name']).text.strip(),
                'url': self.driver.current_url,
                'address':
                    self.driver.find_element(By.CSS_SELECTOR, css_selects['address']).text.strip(),
                # 'role':
                #     self.driver.find_element(By.CSS_SELECTOR, css_selects['role']).text.strip(),
                # 'agency':
                #     self.driver.find_element(By.CSS_SELECTOR, css_selects['agency']).text.strip(),
                'contact_number':
                    self.driver.find_element(By.CSS_SELECTOR,
                                             css_selects['contact_number']).get_attribute('href').replace('tel:', ''),
                'e-mail': '',
                # 'e-mail': self.driver.find_element(By.CSS_SELECTOR,
                #                                    css_selects['e-mail']).get_attribute('href').replace('mailto:', '')
            }
            agent['contact_name'] = agent['lead_name']
            print(agent)
            return agent
        except TimeoutException as e:
            print(e)
            return {}

    def _page_scraper(self, agent_links: list[str]):
        for link in agent_links:
            self.driver.get(link)
            try:
                wait_css_located(self.driver, self._CSS_SELECTORS['lead_name'])
                self.agents.append(self._get_agent_info())
            except TimeoutException as e:
                print(e)

    def _find_next_page_link(self):
        try:
            print(self.driver.current_url)
            elem = self.driver.find_element(By.CSS_SELECTOR, self._CSS_SELECTORS['next_page'])
            print(elem)
            next_page_url = self.base_url.rstrip('/') + '/?page=' + elem.get_attribute('data-href')
            print(f'found next page:\n{next_page_url}')
            return next_page_url

        except Exception as e:
            print(f'error is:\n{e}')
            return None

    def get_all_agents(self):
        k = 0
        while True:
            k += 1
            print('getting next page link')
            next_page_link = self._find_next_page_link()

            if k > 130:
                raise Exception('too mane k')
            if k % 10 == 0:
                time.sleep(2)
                self.get_agents_df(directory=self.page)
            agent_links = self._get_page_agent_links()
            self._page_scraper(agent_links)
            print('page scrapped')
            if not next_page_link:
                break
            print('accessing')
            self.driver.get(next_page_link)
            print('accessed')
            try:
                wait_css_located(self.driver, css_selector=self._CSS_SELECTORS['agent_page_link'])
            except TimeoutException as e:
                print(f'time out: \n{e}')
                break

    def get_agents_df(self, directory: str):
        df = pd.DataFrame(self.agents)
        df.to_csv(f'C:/Users/Jean/Desktop/prospeccion/{directory}/all{self.city}.csv', index=False)
        return df


class SaftiScraper(RemaxScraper):
    _CSS_SELECTORS = {
        'lead_name': 'h1:has(span[data-testid="minisite-agent-specialized-sector"]) > span:first-child',
        'address': 'h1:has(span[data-testid="minisite-agent-specialized-sector"]) > span:nth-child(3)',
        'contact_number': 'a[data-testid="minisite_tetiere-phone-button"]',
        'e-mail': 'a[data-testid=minisite_tetiere-mail-button',
        'next_page': 'a.abtasty-pagination-next',
        'agent_page_link': 'a[data-testid="agent-card-name"]',
    }
    _BASE_URL = 'https://www.safti.es/encontrar-un-asesor'

    def __init__(self, city: str = ''):
        super().__init__(city)
        self.base_url = SaftiScraper._BASE_URL
        self.page = 'safti'

    def _find_next_page_link(self):
        try:
            print(self.driver.current_url)
            elem = self.driver.find_element(By.CSS_SELECTOR, self._CSS_SELECTORS['next_page'])
            print(elem)
            next_page_url = elem.get_attribute('href')
            print(f'found next page:\n{next_page_url}')
            return next_page_url

        except Exception as e:
            print(f'error is:\n{e}')
            return None


if __name__ == "__main__":
    'as'
    # scrape_monapart(city=)
    # remax_driver = RemaxScraper('?page=119')
    # print(remax_driver._get_page_agent_links())
    # remax_driver.get_all_agents()
    # agents_df = remax_driver.get_agents_df()
    # print(remax_driver.get_agents_df().info)
    # df = pd.read_csv(filepath_or_buffer='C:/Users/Jean/Desktop/prospeccion/remax/all.csv')
    # df_2 = pd.read_csv('C:/Users/Jean/Desktop/prospeccion/remax/last_3_pages.csv')
    # df_3 = pd.concat([df, df_2], ignore_index=True)
    # df_3.drop_duplicates(inplace=True)
    # df_3.to_csv('C:/Users/Jean/Desktop/prospeccion/remax/all_agents.csv')
