import pytest

from capella_console_client.assets import (
    _derive_stac_id,
)


def test_derive_stac_id():
    STAC_ID = "CAPELLA_C05_SM_GEO_HH_20210727091736_20210727091740"
    assert _derive_stac_id({"HH": {"href": STAC_ID}}) == STAC_ID


def test_derive_stac_id_invalid():
    with pytest.raises(ValueError):
        _derive_stac_id({"HH": {"href": "THIS_AINT_A_STAC_ID"}})
