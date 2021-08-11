import json
from pathlib import Path
from typing import List, Dict, Any

import typer


def _safe_load_json(file_path: Path) -> Dict[str, Any]:
    try:
        content = json.loads(file_path.read_text())
    except:
        content = {}
    return content


class CLICache:
    ROOT = Path.home() / ".capella-console-client"
    JWT = ROOT / "jwt.cache"
    SETTINGS = ROOT / "settings.json"
    MY_SEARCHES = ROOT / "my-searches.json"

    @classmethod
    def write_jwt(cls, jwt: str):
        cls.JWT.parent.mkdir(exist_ok=True)
        cls.JWT.write_text(jwt)
        typer.echo(f"Cached JWT to {cls.JWT}")

    @classmethod
    def load_jwt(cls) -> str:
        return cls.JWT.read_text()

    @classmethod
    def write_user_settings(cls, key: str, value: Any) -> str:
        cls.SETTINGS.parent.mkdir(exist_ok=True)
        settings = cls.load_user_settings()
        settings[key] = value
        cls.SETTINGS.write_text(json.dumps(settings))

    @classmethod
    def load_user_settings(cls) -> str:
        return _safe_load_json(cls.SETTINGS)

    @classmethod
    def write_my_searches(cls, my_searches: Dict[str, Any]):
        cls.MY_SEARCHES.write_text(json.dumps(my_searches))

    @classmethod
    def update_my_searches(cls, search_identifier: str, stac_ids: List[str]) -> str:
        cls.MY_SEARCHES.parent.mkdir(exist_ok=True)
        my_searches = cls.load_my_searches()
        my_searches[search_identifier] = stac_ids
        cls.write_my_searches(my_searches)

    @classmethod
    def load_my_searches(cls) -> str:
        return _safe_load_json(cls.MY_SEARCHES)
