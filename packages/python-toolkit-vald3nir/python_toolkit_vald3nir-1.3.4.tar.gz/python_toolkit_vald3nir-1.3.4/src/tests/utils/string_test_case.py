import pytest

from src.toolkit.utils.string_utils import translate_text


@pytest.mark.asyncio
async def test_translate_text_success():
    result = await translate_text("Hello")
    assert result == "Olá"
