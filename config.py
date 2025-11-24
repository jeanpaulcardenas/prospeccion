from dotenv import load_dotenv
import os

load_dotenv()
_PLACES_API_KEY = os.getenv('PLACES_NEW_API_KEY')
_OPEN_AI_PERSONAL_KEY = os.getenv('OPEN_AI_PERSONAL_KEY')
_SPIDER_API_KEY = os.getenv('SPIDER_CLOUD_KEY')
_INCLUDED_TYPE = 'real_estate_agency'
_BASE_URL = 'https://places.googleapis.com/v1/places:searchText'
INCLUDE_NON_PHYSICAL_BUSINESS = True
_CONTENT_TYPE = 'application/json'
_FIELDS = ['places.displayName', 'places.formattedAddress', 'places.rating', 'places.internationalPhoneNumber',
           'places.nationalPhoneNumber', 'places.userRatingCount', 'places.websiteUri', 'nextPageToken']
_DEFAULT_LANGUAGE = 'es'
logging_basic_config = {
    'level': 20,
    'format': '%(levelname)s %(name)s %(message)'
}
