import requests
import pandas as pd
from config import _PLACES_API_KEY

# TODO: error handling for code:400 response['error']['message'] .... 'Request contains an invalid argument.'
# TODO: delete agencies with 'holidays' or 'vacation' and such in agency name 'apartments' 'stays' 'rental'
# TODO: Delete ?utm from links (keep just base url)
class NewPlacesDriverSpain:
    _TEXT_QUERY = 'real estate agency in {0}, {1}, {2}'
    _DFLT_LANGUAGE = 'en'
    _COUNTRY = 'spain'
    _DFLT_PAGE_SIZE = 80
    _INCLUDED_TYPE = 'real_estate_agency'
    _FIELDS = ('places.displayName', 'places.formattedAddress', 'places.rating', 'places.internationalPhoneNumber',
               'places.nationalPhoneNumber', 'places.userRatingCount', 'places.websiteUri', 'nextPageToken')
    _TEXT_QUERY_BASE_URL = 'https://places.googleapis.com/v1/places:searchText'
    _DFLT_KEY_VALUES = ('name', 'address', 'international_phone_number', 'url', 'rating', 'reviews_count', 'language')
    agency_dflt_format = {key: [] for key in _DFLT_KEY_VALUES}

    def __init__(self, api_key: str, ):
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

    def text_search_request(self, zip_code: str, city: str, **kwargs) -> dict:
        """Returns a dict (json) with keys 'places' (list of dicts with place info) and 'nextPageToken'"""

        body = self.body(postal_code=zip_code, city=city, **kwargs)
        headers = self.headers()
        print(headers)
        response = requests.post(url=self._TEXT_QUERY_BASE_URL, json=body, headers=headers)
        print(response.json()['places'])
        return dict(response.json())

    def full_text_search_request(self, zip_codes, city, **kwargs) -> list[dict]:
        places = []
        token = ''
        for zip_code in zip_codes:
            while True:
                response = self.text_search_request(zip_code, city, token=token, **kwargs)
                places += response['places']
                token = response.get('nextPageToken', '')
                if not token:
                    break
                else:
                    print('token found')
        return places

    @staticmethod
    def places_list_to_dict(places:list[dict]) -> dict:
        agencies = NewPlacesDriverSpain.agency_dflt_format
        for place in places:
            agencies['name'].append(place.get('displayName').get('text'))
            agencies['address'].append(place.get('formattedAddress'))
            agencies['rating'].append(place.get('rating'))
            agencies['url'].append(place.get('websiteUri'))
            agencies['reviews_count'].append(place.get('userRatingCount'))
            agencies['international_phone_number'].append(place.get('internationalPhoneNumber'))
            agencies['language'].append(place.get('displayName').get('languageCode'))
        return agencies

    @staticmethod
    def create_df(agencies: dict):
        df = pd.DataFrame(agencies)
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def create_csv(self, city, df: pd.DataFrame):
        df.to_csv(f'../{self._COUNTRY}/{city}.csv', index=False)

    def agencies_in_city(self, city, zip_codes, create_file: bool = True):
        places = self.full_text_search_request(city=city, zip_codes=zip_codes)
        print(places)
        agencies = self.places_list_to_dict(places=places)
        print(agencies)
        df = self.create_df(agencies)
        print(df)
        if create_file:
            self.create_csv(city=city, df=df)
        return df


print(NewPlacesDriverSpain.agency_dflt_format)
driver = NewPlacesDriverSpain(_PLACES_API_KEY)
zip_codes = ['0' + str(x) for x in range(3501)]
df = driver.agencies_in_city(city='Benidorm_trying', zip_codes=zip_codes)
print(df.info())
