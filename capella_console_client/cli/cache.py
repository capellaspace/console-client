import json
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime

from capella_console_client.logconf import logger


def _safe_load_json(file_path: Path) -> Dict[str, Any]:
    content = {}
    try:
        content = json.loads(file_path.read_text())
    except:
        pass
    return content


class CLICache:
    ROOT = Path.home() / ".capella-console-wizard"
    JWT = ROOT / "jwt.cache"
    SETTINGS = ROOT / "settings.json"
    MY_SEARCH_RESULTS = ROOT / "my-search-results.json"
    MY_SEARCH_QUERIES = ROOT / "my-search-queries.json"

    @classmethod
    def write_jwt(cls, jwt: str):
        cls.JWT.write_text(jwt)
        logger.info(f"Cached JWT to {cls.JWT}")

    @classmethod
    def load_jwt(cls) -> str:
        return cls.JWT.read_text()

    @classmethod
    def write_user_settings(cls, key: str, value: Any):
        settings = cls.load_user_settings()
        settings[key] = value
        cls.SETTINGS.write_text(json.dumps(settings))

    @classmethod
    def load_user_settings(cls) -> Dict[str, Any]:
        return _safe_load_json(cls.SETTINGS)

    @classmethod
    def add_timestamps(cls, data: Union[Dict[str, Any], List[str]], is_new: bool = False) -> Dict[str, Any]:
        now = str(datetime.now())[:-7]
        record = {
            "data": data,
            "updated_at": now,
        }
        if is_new:
            record["created_at"] = now
        return record

    @classmethod
    def write_my_search_results(cls, my_search_results: Dict[str, Any]):
        cls.MY_SEARCH_RESULTS.write_text(json.dumps(my_search_results))

    @classmethod
    def update_my_search_results(cls, search_identifier: str, stac_ids: List[str], is_new: bool = False):
        my_search_results = cls.load_my_search_results()
        my_search_results[search_identifier] = cls.add_timestamps(stac_ids, is_new)
        cls.write_my_search_results(my_search_results)

    @classmethod
    def load_my_search_results(cls) -> Dict[str, Any]:
        return _safe_load_json(cls.MY_SEARCH_RESULTS)

    @classmethod
    def write_my_search_queries(cls, my_queries: Dict[str, Any]):
        cls.MY_SEARCH_QUERIES.write_text(json.dumps(my_queries))

    @classmethod
    def update_my_search_queries(cls, search_identifier: str, search_query: Dict[str, Any], is_new: bool = False):
        my_queries = cls.load_my_search_queries()
        my_queries[search_identifier] = cls.add_timestamps(search_query, is_new)
        cls.write_my_search_queries(my_queries)

    @classmethod
    def load_my_search_queries(cls) -> Dict[str, Any]:
        return _safe_load_json(cls.MY_SEARCH_QUERIES)


CLICache.ROOT.mkdir(exist_ok=True)
