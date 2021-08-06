import json
from pathlib import Path
from typing import List

import typer


class CLICachePaths:
    ROOT = Path.home() / ".capella-console-client"
    JWT = ROOT / "jwt.cache"
    SETTINGS = ROOT / "settings.json"

    @classmethod
    def write_jwt(cls, jwt: str):
        cls.JWT.parent.mkdir(exist_ok=True)
        cls.JWT.write_text(jwt)
        typer.echo(f"Cached JWT to {cls.JWT}")

    @classmethod
    def load_jwt(cls) -> str:
        return cls.JWT.read_text()

    @classmethod
    def write_user_settings(cls, key, value) -> str:
        cls.SETTINGS.parent.mkdir(exist_ok=True)
        settings = cls.safe_load_user_settings()
        settings[key] = value
        return cls.SETTINGS.write_text(json.dumps(settings))

    @classmethod
    def safe_load_user_settings(cls) -> str:
        try:
            settings = json.loads(cls.SETTINGS.read_text())
        except:
            settings = {}
        return settings
