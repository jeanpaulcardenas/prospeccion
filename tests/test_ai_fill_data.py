import pytest
from app.LLM.ai_fill_data import clear_duplicates, format_phone_number

def test_format_phone_number():
    assert format_phone_number('963-633-455') == '+34963633455'


