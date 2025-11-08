import time
import logging
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

# assumes default_options() and wait_css_located() are defined elsewhere in the project

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

    def __init__(self, city: str = '', driver: Optional[webdriver.Chrome] = None,
                 max_pages: int = 0, output_dir: str = None):
        """
        city: e.g. 'madrid' or 'madrid/majadahonda'
        driver: optionally supply an existing webdriver.Chrome instance
        max_pages: 0 means no explicit cap; otherwise stop after that many pages
        output_dir: where CSVs will be saved (defaults to your existing path)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            # basic default config (caller can reconfigure)
            logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

        self.city = city.lower()
        self.page = 'remax'
        self.base_url = self._BASE_URL + self.city
        self.max_pages = max_pages

        self.output_dir = Path(output_dir or Path.home() / "Desktop" / "prospeccion" / self.page)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.driver_provided = driver is not None
        self.driver = driver or webdriver.Chrome(self._options)
        self.agents: List[dict] = []
        self.agents_df = pd.DataFrame()

        self.logger.info("Opening base url: %s", self.base_url)
        try:
            self.driver.get(self.base_url)
            wait_css_located(self.driver, css_selector=self._CSS_SELECTORS['agent_page_link'])
        except Exception as e:
            self.logger.warning("Initial page load or wait failed: %s", e)

    def _get_page_agent_links(self) -> List[str]:
        try:
            time.sleep(1.0)  # small pause to let DOM settle
            anchors = self.driver.find_elements(By.CSS_SELECTOR, self._CSS_SELECTORS['agent_page_link'])
            links = [a.get_attribute('href') for a in anchors if a.get_attribute('href')]
            self.logger.debug("Found %d agent links on page", len(links))
            return links
        except Exception as e:
            self.logger.warning("Error getting agent links: %s", e)
            return []

    def _get_agent_info(self) -> dict:
        css = self._CSS_SELECTORS
        try:
            lead_name = self._safe_text(css['lead_name'])
            address = self._safe_text(css['address'])
            contact = self._safe_attr(css['contact_number'], 'href')
            if contact:
                contact = contact.replace('tel:', '').strip()
            email = self._safe_attr(css['e-mail'], 'href')
            if email:
                email = email.replace('mailto:', '').strip()

            agent = {
                'lead_name': lead_name,
                'contact_name': lead_name,
                'url': self.driver.current_url,
                'address': address,
                'contact_number': contact or '',
                'e-mail': email or ''
            }
            self.logger.debug("Agent parsed: %s", agent.get('lead_name'))
            return agent
        except Exception as e:
            self.logger.warning("Failed to parse agent info: %s", e)
            return {}

    def _safe_text(self, css_selector: str) -> str:
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            return el.text.strip()
        except Exception:
            return ''

    def _safe_attr(self, css_selector: str, attr: str) -> Optional[str]:
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            return el.get_attribute(attr)
        except Exception:
            return None

    def _page_scraper(self, agent_links: List[str]):
        for link in agent_links:
            try:
                self.driver.get(link)
                wait_css_located(self.driver, css_selector=self._CSS_SELECTORS['lead_name'])
                info = self._get_agent_info()
                if info:
                    self.agents.append(info)
            except TimeoutException as e:
                self.logger.warning("Timeout on agent page %s: %s", link, e)
            except WebDriverException as e:
                self.logger.error("Webdriver error on %s: %s", link, e)

    def _find_next_page_link(self) -> Optional[str]:
        try:
            elem = self.driver.find_element(By.CSS_SELECTOR, self._CSS_SELECTORS['next_page'])
            # prefer data-href if site uses it, else fallback to href
            data_href = elem.get_attribute('data-href') or elem.get_attribute('href')
            if not data_href:
                return None
            next_page_url = self.base_url.rstrip('/') + '/?page=' + data_href
            self.logger.debug("Found next page url: %s", next_page_url)
            return next_page_url
        except Exception:
            return None

    def get_all_agents(self):
        k = 0
        try:
            while True:
                k += 1
                if self.max_pages and k > self.max_pages:
                    self.logger.info("Reached max_pages=%d, stopping", self.max_pages)
                    break
                self.logger.info("Processing page %d", k)
                next_page_link = self._find_next_page_link()

                if k % 10 == 0:
                    self.logger.info("Persisting intermediate results at page %d", k)
                    self.get_agents_df()

                agent_links = self._get_page_agent_links()
                if not agent_links:
                    self.logger.info("No agent links found on page %d — stopping", k)
                    break
                self._page_scraper(agent_links)

                if not next_page_link:
                    self.logger.info("No next page link found — finished")
                    break

                self.logger.debug("Navigating to next page: %s", next_page_link)
                try:
                    self.driver.get(next_page_link)
                    wait_css_located(self.driver, css_selector=self._CSS_SELECTORS['agent_page_link'])
                except TimeoutException as e:
                    self.logger.warning("Timeout after navigating to next page: %s", e)
                    break
        finally:
            # always try to persist results and quit driver (unless provided externally)
            try:
                self.get_agents_df()
            except Exception as e:
                self.logger.warning("Failed saving results: %s", e)
            if not self.driver_provided:
                try:
                    self.driver.quit()
                except Exception:
                    pass

    def get_agents_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.agents)
        out_file = self.output_dir / f"all_{self.city}.csv"
        df.to_csv(out_file, index=False)
        self.logger.info("Saved %d agents to %s", len(df), out_file)
        return df