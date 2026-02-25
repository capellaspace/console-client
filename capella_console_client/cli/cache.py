import json
from pathlib import Path
from typing import Any
from datetime import datetime
import keyring


def _safe_load_json(file_path: Path) -> dict[str, Any]:
    content = {}
    try:
        content = json.loads(file_path.read_text())
    except:
        pass
    return content


class CLICache:
    ROOT = Path.home() / ".capella-console-wizard"
    SETTINGS = ROOT / "settings.json"
    MY_SEARCH_RESULTS = ROOT / "my-search-results.json"
    MY_SEARCH_QUERIES = ROOT / "my-search-queries.json"
    KEYRING_SYSTEM_NAME = "capella-console-wizard"
    KEYRING_USERNAME = "console-api-key"

    @classmethod
    def write_user_settings(cls, key: str, value: Any):
        settings = cls.load_user_settings()
        settings[key] = value
        cls.SETTINGS.write_text(json.dumps(settings))

    @classmethod
    def load_user_settings(cls) -> dict[str, Any]:
        settings = _safe_load_json(cls.SETTINGS)
        if "console_api_key" in settings:
            cls._migrate_api_key_to_keychain(settings)

        settings["console_api_key"] = keyring.get_password(cls.KEYRING_SYSTEM_NAME, cls.KEYRING_USERNAME) or ""

        return settings

    @classmethod
    def add_timestamps(cls, data: dict[str, Any] | list[str], is_new: bool = False) -> dict[str, Any]:
        now = str(datetime.now())[:-7]
        record = {
            "data": data,
            "updated_at": now,
        }
        if is_new:
            record["created_at"] = now
        return record

    @classmethod
    def write_my_search_results(cls, my_search_results: dict[str, Any]):
        cls.MY_SEARCH_RESULTS.write_text(json.dumps(my_search_results))

    @classmethod
    def update_my_search_results(cls, search_identifier: str, stac_ids: list[str], is_new: bool = False):
        my_search_results = cls.load_my_search_results()
        my_search_results[search_identifier] = cls.add_timestamps(stac_ids, is_new)
        cls.write_my_search_results(my_search_results)

    @classmethod
    def load_my_search_results(cls) -> dict[str, Any]:
        return _safe_load_json(cls.MY_SEARCH_RESULTS)

    @classmethod
    def write_my_search_queries(cls, my_queries: dict[str, Any]):
        cls.MY_SEARCH_QUERIES.write_text(json.dumps(my_queries))

    @classmethod
    def update_my_search_queries(cls, search_identifier: str, search_query: dict[str, Any], is_new: bool = False):
        my_queries = cls.load_my_search_queries()
        my_queries[search_identifier] = cls.add_timestamps(search_query, is_new)
        cls.write_my_search_queries(my_queries)

    @classmethod
    def load_my_search_queries(cls) -> dict[str, Any]:
        return _safe_load_json(cls.MY_SEARCH_QUERIES)

    @classmethod
    def _migrate_api_key_to_keychain(cls, settings: dict[str, Any]):
        api_key = settings.pop("console_api_key")

        # store in system secure storage rather than plain text file
        keyring.set_password(cls.KEYRING_SYSTEM_NAME, cls.KEYRING_USERNAME, api_key)
        # rewrite settings without api key
        cls.SETTINGS.write_text(json.dumps(settings))


CLICache.ROOT.mkdir(exist_ok=True)
