
import pytest

from src.hentailib.core import ApiKeyError
from tests.conftest import api_client

def test_get_page_by_id(api_client):
    result = api_client.get_title(15220657)
    result = result.url
    assert result == "https://api-cdn.rule34.xxx/images/2259/8ec226d8ba2cfa26e953016f434cf156.png"

def test_get_random_page(api_client):
    result = api_client.utils.get_random_page("hu_tao")
    result = result.url
    assert result is not None
def test_autocomplete_single_tag(api_client):
    result = api_client.utils.autocomplete_single_tag("hu_tao")
    assert result == "hu_tao_(genshin_impact)"

def test_autocomplete_multiple_tags(api_client):
    result = api_client.utils.autocomplete_multiple_tags("hu_tao genshin_impact")
    assert result == "hu_tao_(genshin_impact) genshin_impact"

def test_negate_single_tag_autocomplete(api_client):
    result = api_client.utils.autocomplete_multiple_tags("-hu_tao")
    assert result == "-hu_tao_(genshin_impact)"

def test_negate_multiple_tag_autocomplete(api_client):
    result = api_client.utils.autocomplete_multiple_tags("-hu_tao -trap")
    assert result == "-hu_tao_(genshin_impact) -trap"
