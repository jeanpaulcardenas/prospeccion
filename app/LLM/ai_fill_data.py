import pandas as pd
from config import logging_basic_config
from app.LLM.llm_integration import open_ai_request, make_md, GET_CONTACTS_AI_SYSTEM_CONTENT, GET_SA_AI_SYSTEM_CONTENT, \
    get_contacts_ai_user_content, get_sa_ai_user_content
from app.scrapers.scrapers import get_contacts_url, default_options
from selenium import webdriver
from email_validator import validate_email, EmailNotValidError
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(**logging_basic_config)

def clear_duplicates(df: pd.DataFrame) -> None:

    phone_0 = 'maps_phone'
    phones = [phone_0, 'phone_1', 'phone_2']
    if all(phone in df.columns for phone in phones):
        cols = [phone_0, 'phone_1', 'phone_2']
        df[cols] = df[cols].apply(lambda col: col.map(format_phone_number))
        mask_1 = (df[phone_0] == df['phone_1']) | (df[phone_0] == df['phone_2'])
        df.loc[mask_1, phone_0] = ''
    else:
        logger.warning('Not able to clear phone duplicates. Column names in dataframe dont match expected')


def validate_emails(email: str) -> bool:
    if type(email) != str:
        return False
    if email == '':
        return False
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        print(f'EMAIL NOT VALID: {email}')
        return False


def validate_df_emails(df: pd.DataFrame, column: str) -> None:
    """checks in all emails in a dataframe column are in-place"""
    mask = ~df[column].apply(validate_emails)
    df.loc[mask, column] = ''


def format_phone_number(number: str | int | float) -> str:
    if not number or number == 'nan':
        return ''
    number = number.strip().replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
    if not(str(number[0]) == '+' or str(number[:2]) == '00'):
        number = '+34' + number
    return number


def fill_data(csv_filepath: str,  file_name: str, from_row: int = 0, to_row: int = None):
    driver = webdriver.Chrome(options=default_options())

    if csv_filepath[-4:] != '.csv':
        raise TypeError(f'{csv_filepath} is not a csv file')
    df = pd.read_csv(filepath_or_buffer=csv_filepath)
    if not to_row:
        to_row = df.shape[0]
    if 'url' not in df.columns:
        raise ValueError('No url column in the csv')

    df_2 = df

    required = ['maps_phone', "phone_1", "phone_2", "e-mail_1", "e-mail_2", "message"]

    for col in required:
        if col not in df_2.columns:
            df_2[col] = ""
    chunk_size = 5
    df_2[required] = df_2[required].astype(str)
    # Make emails lowercase
    df_2[['e-mail_1', 'e-mail_1']] = df_2[['e-mail_1', 'e-mail_2']].apply(lambda x: x.str.lower())

    for start in range(from_row, to_row, chunk_size):
        end = start + chunk_size
        new_cols = df_2['url'][start:end].apply(lambda url: pd.Series(
            open_ai_request(system_content=GET_CONTACTS_AI_SYSTEM_CONTENT, user_content=get_contacts_ai_user_content(
                make_md(get_contacts_url(driver=driver, base_url=url))))))
        # Add new columns into df_2 (only for this chunk)
        df_2.loc[start:end - 1, new_cols.columns] = new_cols.values
        # Save intermediate result
        # df_2.to_csv(
        #     f'C:/Users/Jean/Desktop/prospeccion/app/LLM/enriched_dfs/{file_name}_3.csv',
        #     index=False
        # )
        # Remove phone duplicates in-place


        # validate emails

        df_2.to_csv(
            f'C:/Users/Jean/Desktop/prospeccion/app/LLM/phone_duplicates_cleared/{file_name}_4.csv',
            index=False
        )

    clear_duplicates(df_2)
    validate_df_emails(df_2, 'e-mail_1')
    validate_df_emails(df_2, 'e-mail_2')
    df_2.to_csv(
        f'C:/Users/Jean/Desktop/prospeccion/app/LLM/phone_duplicates_cleared/{file_name}_4.csv',
        index=False
    )
    return df_2


if __name__ == '__main__':
    print('ran np')
    # fill_data('C:/Users/Jean/Desktop/prospeccion/España/illes balears.csv', file_name='baleares_team')

    # df = pd.read_csv('./enriched_dfs/araba.csv')
    # validate_df_emails(df, 'e-mail_1')
    # validate_df_emails(df, 'e-mail_2')
    # df.to_csv('C:/Users/Jean/Desktop/prospeccion/app/LLM/enriched_dfs/araba_1.1.csv')
