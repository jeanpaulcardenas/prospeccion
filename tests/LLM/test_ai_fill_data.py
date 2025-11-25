import pytest
from app.LLM.ai_fill_data import clear_duplicates, format_phone_number


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



