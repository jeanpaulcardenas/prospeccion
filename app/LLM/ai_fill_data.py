import pandas as pd
from llm_integration import open_ai_request, make_md, GET_CONTACTS_AI_SYSTEM_CONTENT, GET_SA_AI_SYSTEM_CONTENT, \
    get_contacts_ai_user_content, get_sa_ai_user_content
from app.scrapers.scrapers import get_contacts_url, default_options
from selenium import webdriver
from email_validator import validate_email, EmailNotValidError


def clear_duplicates(df: pd.DataFrame) -> None:

    phone_0 = 'maps_phone'
    cols = [phone_0, 'phone_1', 'phone_2']
    df[cols] = df[cols].astype(str)
    df[cols] = df[cols].map(format_phone_number)
    mask = (df[phone_0] == df['phone_1']) | (df[phone_0] == df['phone_2'])
    df.loc[mask, phone_0] = ''


def validate_emails(email: str) -> bool:
    if type(email) != str:
        return False
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        print(f'EMAIL NOT VALID: {email}')
        return False


def validate_df_emails(df: pd.DataFrame, column: str) -> None:
    mask = ~df[column].apply(validate_emails)
    df.loc[mask, column] = ''


def format_phone_number(number:str | int | float) -> str:
    if not number or number == 'nan':
        return ''
    number = number.strip().replace(' ', '').replace('(', '').replace(')', '')
    if number[0] != '+':
        number = '+34' + number
    return number


def fill_data(csv_filepath: str,  file_name: str, from_row: int = None, to_row: int = None):
    driver = webdriver.Chrome(options=default_options())
    if csv_filepath[-4:] != '.csv':
        raise TypeError(f'{csv_filepath} is not a csv file')
    df = pd.read_csv(filepath_or_buffer=csv_filepath)
    if 'url' not in df.columns:
        raise ValueError('No url column in the csv')
    if type(to_row) == int and type(from_row) == int:
        df_2 = df.iloc[from_row:to_row].copy()

    else:
        df_2 = df

    chunk_size = 5
    for start in range(0, len(df_2), chunk_size):
        end = start + chunk_size
        new_cols = df_2['url'][start:end].apply(lambda url: pd.Series(
            open_ai_request(system_content=GET_CONTACTS_AI_SYSTEM_CONTENT, user_content=get_contacts_ai_user_content(
                make_md(get_contacts_url(driver=driver, base_url=url))))))
        print(new_cols)
        # Add new columns into df_2 (only for this chunk)
        df_2.loc[start:end - 1, new_cols.columns] = new_cols.values

        # Save intermediate result
        df_2.to_csv(
            f'C:/Users/Jean/Desktop/prospeccion/app/LLM/results/{file_name}.csv',
            index=False
        )

        # Remove duplicates in-place
        clear_duplicates(df_2)

        df_2.to_csv(
            f'C:/Users/Jean/Desktop/prospeccion/app/LLM/phone_duplicates_cleared/{file_name}.csv',
            index=False
        )
    return df_2


if __name__ == '__main__':
    # fill_data('C:/Users/Jean/Desktop/prospeccion/España/albacete.csv', file_name='albacete')


    df = pd.read_csv('./phone_duplicates_cleared/araba.csv')
    validate_df_emails(df, 'e-mail_1')
    validate_df_emails(df, 'e-mail_2')
    print(df.to_string())
    df.to_csv('C:/Users/Jean/Desktop/prospeccion/app/LLM/phone_duplicates_cleared/araba_1.1.csv')
