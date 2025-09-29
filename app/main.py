    import requests
    import pandas as pd
    from app.helpers import list_to_comma_separated_string
    from config import _PLACES_API_KEY, _INCLUDED_TYPE, INCLUDE_NON_PHYSICAL_BUSINESS, _BASE_URL, _query,\
        _FIELDS, _headers, _DEFAULT_LANGUAGE
    import openpyxl
    import time

    CITY = 'Fuerteventura'
    COUNTRY = 'España'
    ZIP_CODES = []


    # TODO: error handling for code:400 response['error']['message'] .... 'Request contains an invalid argument.'

    class NEW_PLACES_DRIVER:
        def __init__(self, api_key: str):
            self._API_KEY = api_key,

        @property
        def api_key(self):
            return self._API_KEY



    def get_body(city: str, zip_code: str, page_size: str = '60', country: str = 'España', include_non_physical: bool = True,
                 included_type: str = _INCLUDED_TYPE, language: str = _DEFAULT_LANGUAGE) -> dict:
        return {
            "textQuery": _query(country=country, city= city, zip_code=zip_code),
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
            'Content-Type': 'real_estate_agency',
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

    df.reset_index(inplace=True, drop=True)
    df.drop_duplicates(inplace=True)
    df.to_csv(f'./spain/{CITY}.csv', index=False)
    print(df.info)
