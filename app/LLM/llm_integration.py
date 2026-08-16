import logging
from openai import OpenAI
from config import _OPEN_AI_PERSONAL_KEY, _SPIDER_API_KEY
import requests
import json
client = OpenAI(api_key=_OPEN_AI_PERSONAL_KEY)
SPIDER_SCRAPE_URL = 'https://api.spider.cloud/scrape'

open_ai_empty_return = {
    'phone_1': '',
    'phone_2': '',
    'e-mail_1': '',
    'e-mail_2': '',
    'message': 'error:no webpage'
}

spider_headers = {
    'Authorization': f'Bearer {_SPIDER_API_KEY}',
    'Contenty-type': 'application/json'
}
GET_SA_AI_SYSTEM_CONTENT = """You are my scraper assistant. I just need you to find the name of a 'sociedad' or 'razón social'
                       for web pages or the name of the legal representative. sociedades will have a 'S.L.' or 'SL' (can be capital or lowercase) 
                       at the end of it. return must be a dict as follows
                       {'owner': , 'sociedad': , 'message':}
                       if owner is not empty sociedad must be empty and vice-versa. owner is returned if you find the 
                       name of a person as representative. sociedad if you find a sl or s.l. and in case you do find it 
                       do not include sl nor s.l."""

GET_CONTACTS_AI_SYSTEM_CONTENT = f"""You are my scraper assistant. You will receive the content of a webpage as a markdown string (inside JSON)
Your task is to extract contact information.

You must ALWAYS return a Python dictionary with EXACTLY these keys:

{{
  "phone_1": "",
  "phone_2": "",
  "e-mail_1": "",
  "e-mail_2": "",
  "message": ""
}}

IMPORTANT RULES (follow strictly):

1. ALWAYS return ALL 5 keys above, even if the values are empty.
   - NEVER change key names.
   - NEVER omit keys.
   - NEVER rename keys.
   - An empty value must be an empty string "".

2. PHONE AND EMAIL EXTRACTION:
   - If you find one or more phone numbers, put the first one in "phone_1" and the second one in "phone_2".
   - If you find one or more emails, put the first one in "e-mail_1" and the second one in "e-mail_2".
   - If fewer than two values exist, leave the rest as empty strings "".

3. SUCCESS CASE:
   - If at least ONE phone OR email is found, fill them normally and set:
       "message": "success"

4. NO CONTACT INFO CASE:
   - If NO phones AND NO emails are found, return:
       {{
         "phone_1": "",
         "phone_2": "",
         "e-mail_1": "",
         "e-mail_2": "",
         "message": "error:no contact info found"
       }}

5. TOO MANY OFFICES CASE:
   - If the page contains multiple offices/branches and it is ambiguous which contact info belongs to which:
       - DO NOT return any phones or emails.
       - Leave all fields empty strings "".
       - Set:
           "message": "error:too many offices, not giving contacts to avoid misunderstanding"

6. OUTPUT FORMAT REQUIREMENTS:
   - Output MUST be a valid JSON-like Python dictionary.
   - Do NOT add extra fields.
   - Do NOT add explanations outside the dictionary.
   - Do NOT include notes, comments, markdown, or prose.
   - Only return the dictionary.
"""


def get_contacts_ai_user_content(markdown: str) -> str:
    return f"""Read {markdown} and get back contact info (phone numbers and e-mail directions). 
               must be a max of 2 phone numbers and 2 e-mails'"""


def get_sa_ai_user_content(markdown: str) -> str:
    return f"""Read {markdown} and get the name of the sociedad or representative"""


def spider_json_data(url: str)-> dict:
    return {'return_format': 'markdown',
            'url': url}


def open_ai_request(system_content: str, user_content: str | None, model: str = 'gpt-4o-mini') -> dict:
    try:
        if not user_content:
            return open_ai_empty_return
        response = client.chat.completions.create(
            model=model,
            response_format={'type': 'json_object'},
            messages=[{'role': 'system',
                       'content': system_content},
                      {'role': 'user',
                       'content': user_content}]
        )
        values = response.choices[0].message.content
        values = json.loads(values)
        print(values)
        return values
    except Exception as e:
        print(f'ERROR OPEN AI REQUEST: {e}')
        return open_ai_empty_return


def make_md(url: str) -> str | None:
    if not url:
        return None
    json_data = spider_json_data(url)

    response = requests.post(url=SPIDER_SCRAPE_URL, headers=spider_headers, json=json_data)
    if response.status_code == 200:
        print(f'response for {url} correct')
        return response.json()
    else:
        print(f'response for {url} not 200')
        return None


if __name__ == '__main__':
    mark_down = make_md('http://www.apiaranda.com/')
    gpt_response = open_ai_request(mark_down)
    print(gpt_response)
    with open('gpt_response.txt', mode='w') as f:
        f.write(str(gpt_response))
    pass
    # resp = {'response': []}
    # for url in ['https://aldebre.com/contacto/']:
    #
    #     print(type(response), '\n', response)
    #     print(response.json())
    #     answer = my_response(response.json())
    #
    #     resp['response'].append(answer)
    #     print(resp)
    #
    # with open('./gpt_response.txt', mode='w') as f:
    #     f.write(str(resp))
    #
    # with open('./spider_markdown.md', mode='w') as f:
    #     f.write(response.json()[0])
