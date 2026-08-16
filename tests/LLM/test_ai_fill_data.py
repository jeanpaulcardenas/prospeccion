from app.LLM.ai_fill_data import clear_duplicates, format_phone_number, validate_df_emails
from pandas.testing import assert_series_equal
import pytest
import pandas as pd

@pytest.mark.parametrize(
    'phone, sol',
    [
        ('966-666-666 ', '+34966666666'),
        ('644 221 221', '+34644221221'),
        ('+34955555555', '+34955555555'),
        ('  (+34) 655 555 555', '+34655555555')
    ]
)
def test_format_phone_number(phone, sol):
    assert format_phone_number(phone) == sol


data = pd.DataFrame({
    'emails': ['jeanpaul9712@gmail.com', 'debe dar errado', 'esválido@hotmail.com',
               'tampoco@@gmail.com', 'sinarroba.es', 'sin@puntoes'],
    'col_2': [x for x in range(6)]
})


def test_validate_df_emails():

    result = validate_df_emails(data.copy(), 'emails')
    expected = pd.Series(['jeanpaul9712@gmail.com', '', 'esválido@hotmail.com', '', '', ''], name='emails')
    assert_series_equal(result, expected)
