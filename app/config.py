from dotenv import load_dotenv
from helpers import list_to_comma_separated_string
import os

load_dotenv()
_PLACES_API_KEY = os.getenv('PLACES_NEW_API_KEY')
_INCLUDED_TYPE = 'real_estate_agency'
_BASE_URL = 'https://places.googleapis.com/v1/places:searchText'
INCLUDE_NON_PHYSICAL_BUSINESS = True
_CONTENT_TYPE = 'application/json'
_FIELDS = ['places.displayName', 'places.formattedAddress', 'places.rating', 'places.internationalPhoneNumber',
           'places.nationalPhoneNumber', 'places.userRatingCount', 'places.websiteUri', 'nextPageToken']
_DEFAULT_LANGUAGE = 'es'

def _query(city: str, country: str, zip_code: str):
    return f'agencia inmobiliaria en {zip_code}, {city}, {country}'


def _headers(content_type=_CONTENT_TYPE, key: str = _PLACES_API_KEY, fields=None) -> str:
    if fields is None:
        fields = list_to_comma_separated_string(_FIELDS)
    return None
