import requests
import pandas as pd
from app.helpers import list_to_comma_separated_string
from config import _PLACES_API_KEY, _INCLUDED_TYPE, INCLUDE_NON_PHYSICAL_BUSINESS, _BASE_URL, _query, \
    _FIELDS, _headers, _DEFAULT_LANGUAGE
import openpyxl
import time

CITY = 'Fuerteventura'
COUNTRY = 'España'
ZIP_CODES = []


# TODO: error handling for code:400 response['error']['message'] .... 'Request contains an invalid argument.'

class NewPlacesDriverSpain:
    _TEXT_QUERY = 'agencia inmobiliaria en {0}, {1}, {2}'
    _DFLT_LANGUAGE = 'es'
    _COUNTRY = 'España'
    _DFLT_PAGE_SIZE = 60
    _INCLUDED_TYPE = 'real_estate_agency'
    _FIELDS = ['places.displayName', 'places.formattedAddress', 'places.rating', 'places.internationalPhoneNumber',
               'places.nationalPhoneNumber', 'places.userRatingCount', 'places.websiteUri', 'nextPageToken']
    _TEXT_QUERY_BASE_URL = 'https://places.googleapis.com/v1/places:searchText'
    _DFLT_KEY_VALUES = ['name', 'address', 'international_phone_number', 'url', 'rating', 'reviews_count', 'language']
    agency_dflt_format = {key: val for (key, '') in _DFLT_KEY_VALUES}

    def __init__(self, api_key: str, ):
        self._API_KEY = api_key,
        self._agency_key_values = ['name']

    @property
    def api_key(self):
        return self._API_KEY

    def _text_query(self, zip_code: str, city: str, country: str):
        return self._TEXT_QUERY.format(zip_code, city, country)

    def headers(self, content_type: str = 'application/json', fields: list[str] = self._FIELDS):
        fields = ','.join(fields)
        return {
            'Content-Type': content_type,
            'X-Goog-Api-Key': self._API_KEY,
            'X-Goog-FieldMask': fields
        }

    def body(self, postal_code: str, city: str, token: str = '', country: str = self._COUNTRY,
             text_query: str = self._TEXT_QUERY, page_size: int = self._DFLT_PAGE_SIZE,
             included_type: str = self._INCLUDED_TYPE, language: str = self._DFLT_LANGUAGE):

        body = {
            'textQuery': text_query.format(postal_code, city, country),
            'pageSize': str(page_size),
            'includePureServiceAreaBusinesses': str(include_non_physical).lower(),
            'includedType': included_type,
            'languageCode': language
        }
        if token:
            # add token to body if it exists
            body['pageToken'] = token
        return body

    def text_search_request(self, zip_code: str, city: str, **kwargs) -> dict:
        """Returns a dict (json) with keys 'places' (list of dicts with place info) and 'nextPageToken'"""

        body = self.body(postal_code=zip_code, city=city, **kwargs)
        headers = self.headers(*kwargs)
        response = requests.post(url=self._TEXT_QUERY_BASE_URL, json=body, headers=headers)
        return response.json

    def full_text_search_request(self, zip_codes, city, **kwargs):
        for zip_code in zip_codes:
            while True:
                data = self.text_search_request(zip_code, city, **kwargs)


def get_body(city: str, zip_code: str, page_size: str = '60', country: str = 'España',
             include_non_physical: bool = True,
             included_type: str = _INCLUDED_TYPE, language: str = _DEFAULT_LANGUAGE) -> dict:
    return {
        "textQuery": _query(country=country, city=city, zip_code=zip_code),
        "pageSize": page_size,
        "includePureServiceAreaBusinesses": str(include_non_physical).lower(),
        "includedType": included_type,
        'languageCode': language
    }


def find_agencies(city: str,
                  country: str,
                  page_size: int,
                  zip_code_now: str,
                  my_df: pd.DataFrame,
                  language: str = 'es',
                  included_type: str = INCLUDED_TYPE,
                  include_non_physical_business: bool = INCLUDE_NON_PHYSICAL_BUSINESS,
                  url: str = _BASE_URL):
    fields = list_to_comma_separated_string(_FIELDS)
    print(fields)
    query = _query(city, country, zip_code_now)
    body = {
        "textQuery": query,
        "pageSize": page_size,
        "includePureServiceAreaBusinesses": include_non_physical_business,
        "includedType": included_type,
        'languageCode': language
    }
    fields = list_to_comma_separated_string(_FIELDS)
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': 'AIzaSyCy8haMZAgBxtuMfQZgdwdl9P72I50PffI',
        'X-Goog-FieldMask': fields
    }
    response = requests.post(url=url, json=body, headers=headers)
    time.sleep(2)
    data: dict = response.json()
    k = 0
    next_token = data.get('nextPageToken', None)
    while data.get('nextPageToken', None):
        if not next_token:
            break
        k += 1
        print(f'token found: {k}')
        body = {
            "textQuery": query,
            "pageSize": page_size,
            "includePureServiceAreaBusinesses": include_non_physical_business,
            "includedType": included_type,
            'languageCode': 'es',
            'strictTypeFiltering': 'true',
            "pageToken": next_token
        }
        response = requests.post(url=url, json=body, headers=headers)
        data_token = response.json()
        data['places'] = data['places'] + response.json().get('places', [])
        next_token = data_token.get('nextPageToken', None)
        if k > 5:
            raise RuntimeError('k runtime error')

    agencies = {
        'name': [],
        'address': [],
        'international_phone_number': [],
        'url': [],
        'rating': [],
        'reviews_count': [],
        'language': []
    }

    for place in data.get("places", []):
        agencies['name'].append(place.get('displayName').get('text'))
        agencies['address'].append(place.get('formattedAddress'))
        agencies['rating'].append(place.get('rating'))
        agencies['url'].append(place.get('websiteUri'))
        agencies['reviews_count'].append(place.get('userRatingCount'))
        agencies['international_phone_number'].append(place.get('internationalPhoneNumber'))
        agencies['language'].append(place.get('displayName').get('languageCode'))
    print(agencies)
    response_df = pd.DataFrame(agencies)
    df = pd.concat([response_df, my_df], ignore_index=True)
    df.drop_duplicates(inplace=True)
    df.reset_index(inplace=True, drop=True)
    print(df.head(), df.info())
    return df, next_token


# zip_codes_now = ['centro', 'Levante', 'Noroeste', 'Norte-Sierra', 'Poniente-Norte', 'Poniente-Sur', 'Sur',
#                  'Sureste', 'Periurbano Este-Campiña', 'Periurbano Oeste-Sierra'] +
zip_codes_now = [str(x) for x in [35610, 35660, 35627, 35625, 35629, 35620, 35600]]
print(zip_codes_now)
df = pd.DataFrame()
i = 0
token = None
j = 0

for zip_code in zip_codes_now:
    size = df.ndim
    times_same = 0
    i += 1
    if i > 60:
        raise RuntimeError('Muchos tokens in i')
    df, token = find_agencies(city=CITY, country=COUNTRY, page_size=60, my_df=df, zip_code_now=zip_code)
    while token:
        j += 1
        if j > 5:
            raise RuntimeError('muchos tokens en j')
        df, token = find_agencies(city=CITY, country=COUNTRY, page_size=60, my_df=df, zip_code_now=zip_code)
        if df.ndim < 41:
            break

    if size == df.ndim:
        times_same += 1
        if times_same >= 3:
            break

# df.reset_index(inplace=True, drop=True)
# df.drop_duplicates(inplace=True)
# df.to_csv(f'./spain/{CITY}.csv', index=False)
# print(df.info)
print(NewPlacesDriverSpain.agency_dflt_format)