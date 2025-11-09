import requests
import pandas as pd
from config import _PLACES_API_KEY
from scrapers.scrapers import ZipCodeScraper
import logging

# TODO: error handling for code:400 response['error']['message'] .... 'Request contains an invalid argument.'
# TODO: delete agencies with 'holidays' or 'vacation' and such in agency name 'apartments' 'stays' 'rental'
# TODO: Delete ?utm from links (keep just base url)


class NewPlacesDriverSpain:
    _TEXT_QUERY = 'agencia inmobiliaria en {0}, {1}, {2}'
    _DFLT_LANGUAGE = 'es'
    _COUNTRY = 'España'
    _DFLT_PAGE_SIZE = 80
    _INCLUDED_TYPE = 'real_estate_agency'
    _FIELDS = ('places.displayName', 'places.formattedAddress', 'places.rating', 'places.internationalPhoneNumber',
               'places.nationalPhoneNumber', 'places.userRatingCount', 'places.websiteUri', 'nextPageToken')
    _TEXT_QUERY_BASE_URL = 'https://places.googleapis.com/v1/places:searchText'
    _DFLT_KEY_VALUES = ('name', 'address', 'international_phone_number', 'url', 'rating', 'reviews_count', 'language',
                        'comment')
    agency_dflt_format = {key: [] for key in _DFLT_KEY_VALUES}

    def __init__(self, api_key: str):
        self.deleted_by_address = 0
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(asctime)s %(message)s')
        self._API_KEY = api_key
        self._agency_key_values = ['name']

    @property
    def api_key(self):
        return self._API_KEY

    def _text_query(self, zip_code: str, city: str, country: str):
        return self._TEXT_QUERY.format(zip_code, city, country)

    def headers(self, content_type: str = 'application/json', fields: list[str] = _FIELDS) -> dict:
        fields = ','.join(fields)
        return {
            'Content-Type': content_type,
            'X-Goog-Api-Key': self._API_KEY,
            'X-Goog-FieldMask': fields
        }

    def body(self, postal_code: str, city: str, token: str = '', country: str = _COUNTRY, text_query: str = _TEXT_QUERY,
             page_size: int = _DFLT_PAGE_SIZE, included_type: str = _INCLUDED_TYPE, language: str = _DFLT_LANGUAGE,
             include_non_physical: bool = True, strict_filtering: bool = True):

        body = {
            'textQuery': text_query.format(postal_code, city, country),
            'pageSize': str(page_size),
            'includePureServiceAreaBusinesses': str(include_non_physical).lower(),
            'includedType': included_type,
            'strictTypeFiltering': str(strict_filtering).lower(),
            'languageCode': language
        }
        if token:
            # add token to body if it exists
            body['pageToken'] = token
        return body

    @staticmethod
    def direction_matches(city: str, sub_zones: list[str], direction: str, secondary_city_name='') -> bool:
        if not direction:
            return True
        if city.capitalize() in direction or any([zone in direction for zone in sub_zones]):
            return True
        elif secondary_city_name:
            if secondary_city_name.capitalize() in direction:
                return True
            else:
                return False
        else:
            return False

    def text_search_request(self, zip_code: str, city: str, **kwargs) -> dict | None:
        """Returns a dict (json) with keys 'places' (list of dicts with place info) and 'nextPageToken'"""

        body = self.body(postal_code=zip_code, city=city, **kwargs)
        headers = self.headers()
        response = requests.post(url=self._TEXT_QUERY_BASE_URL, json=body, headers=headers)
        self.logger.info(f'{len(response.json().get("places"))} places in zip code or sub_area: {zip_code}')
        if response.json().get('places'):
            return dict(response.json())
        else:
            return None

    def full_text_search_request(self, zip_codes, city, **kwargs) -> list[dict]:
        places = []
        token = ''
        for zip_code in zip_codes:
            n_places = 0
            while True:
                response = self.text_search_request(zip_code, city, token=token, **kwargs)
                if response:
                    places += response['places']
                token = response.get('nextPageToken', '')
                n_places += len(response['places'])
                if token:
                    self.logger.info(f'token found for zip code: {zip_code}')
                else:
                    if n_places == 600000:
                        self.logger.info(f'found 60 places in zip code {zip_code}')
                    else:
                        break

        return places

    def places_list_to_dict(self, places: list[dict], city: str, sub_zones: list[str], secondary_city_name='') -> dict:
        agencies = NewPlacesDriverSpain.agency_dflt_format
        for place in places:
            if self.direction_matches(direction=place.get('formattedAddress'), city=city, sub_zones=sub_zones,
                                      secondary_city_name=secondary_city_name):
                agencies['name'].append(place.get('displayName').get('text'))
                agencies['address'].append(place.get('formattedAddress'))
                agencies['rating'].append(place.get('rating'))
                agencies['url'].append(place.get('websiteUri'))
                agencies['reviews_count'].append(place.get('userRatingCount'))
                agencies['international_phone_number'].append(str(place.get('internationalPhoneNumber')))
                agencies['language'].append(place.get('displayName').get('languageCode'))
                agencies['comment'].append("Google reviews: " + str(place.get('rating', '')) + '* / ' +
                                       str(place.get('userRatingCount')))
            else:
                print(f"deleted: {place.get('formattedAddress')}")
                self.deleted_by_address += 1
        return agencies

    @staticmethod
    def create_df(agencies: dict):
        df = pd.DataFrame(agencies)
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def create_zc_column(df:pd.DataFrame):
        df['zip_code'] = df['address'].str.extract(r'\b(\d{5})\b', expand=False)

    @staticmethod
    def add_zc_equal_names(df: pd.DataFrame):
        repeated = df['name'].duplicated(keep=False)
        df.loc[repeated, 'name'] = df.loc[repeated, 'name'] + f'( {df.loc[repeated, "zip_code"]} )'
        df.drop_duplicates('name', inplace=True)

    def create_csv(self, city, df: pd.DataFrame):
        df.to_csv(f'../{self._COUNTRY}/{city.lower()}.csv', index=False)

    def agencies_in_city(self, city, zip_codes: list[str], create_file: bool = True, secondary_city_name=''):
        places = self.full_text_search_request(city=city, zip_codes=zip_codes)
        agencies = self.places_list_to_dict(places=places, city=city, sub_zones=zip_codes,
                                            secondary_city_name=secondary_city_name)
        df = self.create_df(agencies)
        self.create_zc_column(df)
        print(df.head().to_string())

        self.logger.info(f'deleted by miss match address: {self.deleted_by_address}')
        if create_file:
            self.create_csv(city=city, df=df)
            self.logger.info(f'file created with name {city}')
        return df


print(NewPlacesDriverSpain.agency_dflt_format)
print()
driver = NewPlacesDriverSpain(_PLACES_API_KEY)
zip_codes = ZipCodeScraper('Albacete', provincia_zip_code='02').get_zip_codes()
df = driver.agencies_in_city(city='Albacete', zip_codes=zip_codes)


