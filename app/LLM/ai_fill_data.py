import pandas as pd
from llm_integration import open_ai_request, make_md, GET_CONTACTS_AI_SYSTEM_CONTENT, GET_SA_AI_SYSTEM_CONTENT, \
    get_contacts_ai_user_content, get_sa_ai_user_content
from app.scrapers.scrapers import get_contacts_url, default_options
from selenium import webdriver


def clear_duplicates(df: pd.DataFrame) -> None:

    phone_0 = 'international_phone_number'
    cols = [phone_0, 'phone_1', 'phone_2']
    df[cols] = df[cols].astype(str)
    df[cols] = df[cols].map(format_phone_number)
    mask = (df[phone_0] == df['phone_1']) | (df[phone_0] == df['phone_2'])
    df.loc[mask, phone_0] = ''


def format_phone_number(number:str | int | float) -> str:
    if not number or number == 'nan':
        return ''
    number = number.strip().replace(' ', '').replace('(', '').replace(')', '')
    if number[0] != '+':
        number = '+34' + number
    return number


def fill_data(csv_filepath: str,  file_name: str, from_row: int = 0, to_row: int = 0):
    driver = webdriver.Chrome(options=default_options())
    if csv_filepath[-4:] != '.csv':
        raise TypeError(f'{csv_filepath} is not a csv file')
    df = pd.read_csv(filepath_or_buffer=csv_filepath)
    if 'url' not in df.columns:
        raise ValueError('No url column in the csv')
    if to_row and from_row:
        df_2 = df.iloc[from_row:to_row].copy()

    else:
        df_2 = df
    new_cols = df_2['url'].apply(lambda url: pd.Series(
        open_ai_request(system_content=GET_CONTACTS_AI_SYSTEM_CONTENT, user_content=get_contacts_ai_user_content(
            make_md(get_contacts_url(driver=driver, base_url=url))))))

    print(new_cols)
    df_2 = pd.concat([df_2, new_cols], axis=1)
    print(df_2)
    df_2.to_csv(f'C:/Users/Jean/Desktop/prospeccion/app/LLM/results/{file_name}.csv', index=False)
    clear_duplicates(df_2)
    df_2.to_csv(f'C:/Users/Jean/Desktop/prospeccion/app/LLM/phone_duplicates_cleared/{file_name}.csv', index=False)
    return df_2


if __name__ == '__main__':
    fill_data('C:/Users/Jean/Desktop/prospeccion/España/albacete.csv', file_name='albacete')


# df = pd.read_csv('./results/Araba.csv')
# clear_duplicates(df)
# df.to_csv('C:/Users/Jean/Desktop/prospeccion/app/LLM/phone_duplicates_cleared/araba.csv')
