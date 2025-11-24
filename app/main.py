import requests
import pandas as pd
from config import _PLACES_API_KEY
from scrapers.scrapers import ZipCodeScraper
import logging
import os
import re
import unicodedata  # to make 'acento' insensitive


# TODO: error handling for code:400 response['error']['message'] .... 'Request contains an invalid argument.'
# TODO: delete agencies with 'holidays' or 'vacation' and such in agency name 'apartments' 'stays' 'rental'
# TODO: Delete ?utm from links (keep just base url)


class NewPlacesDriverSpain:
    _N_PLACES_FOUND_THEN_REPEAT = 60000
    _TEXT_QUERY = 'agencia inmobiliaria en {0}, {1}, {2}'
    _DFLT_LANGUAGE = 'es'
    _COUNTRY = 'España'
    _DFLT_PAGE_SIZE = str(20)
    _INCLUDED_TYPE = 'real_estate_agency'
    _FIELDS = ('places.displayName', 'places.formattedAddress', 'places.rating', 'places.internationalPhoneNumber',
               'places.types', 'places.nationalPhoneNumber', 'places.userRatingCount', 'places.websiteUri',
               'places.businessStatus', 'nextPageToken')
    _TEXT_QUERY_BASE_URL = 'https://places.googleapis.com/v1/places:searchText'
    _DFLT_KEY_VALUES = ('name', 'address', 'maps_phone', 'url', 'rating', 'reviews_count', 'language',
                        'comment', 'business_status', 'types')
    _BAD_FIT_NAMES = ['alquiler', 'rent ', 'renta', 'rental', 'vacacional', 'vacaciones', 'holidays', 'mobile', 'industrial',
                      'industriales', 'habitacion', 'apartamento']
    agency_dflt_format = {key: [] for key in _DFLT_KEY_VALUES}

    def __init__(self, api_key: str):
        self.deleted = {
            'by_address': 0,
            'by_name_and_zc_rp': 0,
            'by_bad_fit_name': 0,
            'by_no_maps_data': 0,
            'by_status': 0,
            'by_type': 0
        }
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
            'pageSize': page_size,
            'includePureServiceAreaBusinesses': True,
            'includedType': included_type,
            'strictTypeFiltering': strict_filtering,
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
        try:
            self.logger.info(f'{len(response.json().get("places"))} places in zip code or sub_area: {zip_code}')
        except TypeError:
            self.logger.info(f'nothng found in {zip_code}')
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
                    self.logger.info(f'found {n_places} in {zip_code}')

                    if n_places == self._N_PLACES_FOUND_THEN_REPEAT:
                        pass
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
                agencies['maps_phone'].append(place.get('internationalPhoneNumber'))
                agencies['language'].append(place.get('displayName').get('languageCode'))
                agencies['comment'].append("Google reviews: " + str(place.get('rating', '')) + '* / ' +
                                           str(place.get('userRatingCount')))
                agencies['types'].append(place.get('types'))
                agencies['business_status'].append(place.get('businessStatus'))
            else:
                print(f"deleted: {place.get('formattedAddress')}")
                self.deleted['by_address'] += 1
        return agencies

    @staticmethod
    def create_df(agencies: dict):
        df = pd.DataFrame(agencies)
        df['types'] = df['types'].apply(tuple)
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def remove_accents(s: str) -> str:
        if not isinstance(s, str):
            return s
        return ''.join(
            c for c in unicodedata.normalize('NFKD', s)
            if not unicodedata.combining(c)
        )

    @staticmethod
    def create_zc_column(df: pd.DataFrame) -> None:
        """adds a zip_code column"""
        df['zip_code'] = df['address'].str.extract(r'\b(\d{5})\b', expand=False)

    @staticmethod
    def keep_base_name(df: pd.DataFrame):
        """In-place formats name"""
        df['name'] = df['name'].apply(
            lambda x: re.split(r'[|,-]', x)[0] if (len(re.split(r'[|,-]', x)[0]) > 5 and len(x) > 30) else x)

    def add_zc_equal_names(self, df: pd.DataFrame) -> pd.DataFrame:
        size_init = df.shape[0]
        df = df.drop_duplicates(subset=['name', 'zip_code'])
        repeated = df['name'].duplicated(keep=False)
        df.loc[repeated, 'name'] = (df.loc[repeated, 'name'] + ' ( ' + df.loc[repeated, "zip_code"].astype(str) + ' )')
        self.deleted['by_name_and_zc_rp'] = size_init - df.shape[0]
        return df.drop_duplicates('name')

    def del_no_data_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        i_rows = df.shape[0]
        mask = ((df['maps_phone'].isna() | (df['maps_phone'] == '')) & (df['url'].isna() | (df['url'] == '')))
        df = df[~mask]
        self.deleted['by_no_maps_data'] = i_rows - df.shape[0]
        return df

    def del_bad_fit_names(self, df: pd.DataFrame):
        i_rows = df.shape[0]
        mask = (df['name'].apply(self.remove_accents).str.contains('|'.join(self._BAD_FIT_NAMES), case=False, na=False))
        df = df[~mask]
        self.deleted['by_bad_fit_name'] = i_rows - df.shape[0]

        return df

    def create_csv(self, city: str, df: pd.DataFrame, result_file_path: str = ''):
        if not result_file_path:
            root = os.path.dirname(os.path.abspath(__file__))
            result_file_path = os.path.join(root, self._COUNTRY, f'{city.lower()}.csv')
        df.to_csv(result_file_path, index=False)

    def del_not_operational(self, df: pd.DataFrame):
        i_rows = df.shape[0]
        maks = (df['business_status'] == 'OPERATIONAL')
        df = df[maks]
        self.deleted['by_status'] = i_rows - df.shape[0]
        return df

    def del_by_type(self, df: pd.DataFrame):
        i_rows = df.shape[0]
        mask = df['types'].apply(lambda x: isinstance(x, tuple) and x[0] == 'real_estate_agency' and
                                           'travel_agency' not in x)
        df = df[mask]
        self.deleted['by_type'] = i_rows - df.shape[0]
        return df

    def agencies_in_city(self, city, zip_codes: list[str], create_file: bool = True, secondary_city_name=''):
        places = self.full_text_search_request(city=city, zip_codes=zip_codes)
        agencies = self.places_list_to_dict(places=places, city=city, sub_zones=zip_codes,
                                            secondary_city_name=secondary_city_name)
        df = self.create_df(agencies)
        self.keep_base_name(df)
        self.create_zc_column(df)
        df = self.add_zc_equal_names(df)
        print(df.info)
        df = self.del_no_data_rows(df)
        df = self.del_by_type(df)
        df = self.del_not_operational(df)
        df = self.del_bad_fit_names(df)
        for key, val in self.deleted.items():
            self.logger.info(f'deleted by {key}: {val}')

        if create_file:
            self.create_csv(city=city, df=df)
            self.logger.info(f'file created with name {city}')
        return df


print(NewPlacesDriverSpain.agency_dflt_format)
driver = NewPlacesDriverSpain(_PLACES_API_KEY)
zip_codes = ZipCodeScraper('Illes Balears', provincia_zip_code='07').get_zip_codes()
print(f'zip codes found: {len(zip_codes)}')
my_df = driver.agencies_in_city(city='Illes Balears', zip_codes=zip_codes)
