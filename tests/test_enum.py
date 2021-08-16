import pytest

from capella_console_client.enumerations import ProductType

@pytest.mark.parametrize("p_type", ProductType)
def test_contains(p_type):
    assert p_type.name in ProductType
    assert p_type in ProductType

def test_not_contains():
    assert "NANANA" not in ProductType