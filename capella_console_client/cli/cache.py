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
    SETTINGS = ROOT / "settings.json"  # LEGACY - for migration
    PROFILES_DIR = ROOT / "profiles"
    PROFILES_META = ROOT / "profiles.json"
    MY_SEARCH_RESULTS = ROOT / "my-search-results.json"
    MY_SEARCH_QUERIES = ROOT / "my-search-queries.json"
    KEYRING_SYSTEM_NAME = "capella-console-wizard"
    KEYRING_USERNAME = "console-api-key"  # LEGACY - for migration
    DEFAULT_PROFILE = "default"

    @classmethod
    def _get_profile_path(cls, profile_name: str) -> Path:
        """Get the settings file path for a specific profile."""
        return cls.PROFILES_DIR / f"{profile_name}.json"

    @classmethod
    def _get_profile_keyring_key(cls, profile_name: str) -> str:
        """Get the keyring username for a specific profile."""
        return f"{cls.KEYRING_USERNAME}-{profile_name}"

    @classmethod
    def _load_profiles_meta(cls) -> dict[str, Any]:
        """Load profiles metadata (active profile and list of profiles)."""
        if not cls.PROFILES_META.exists():
            return {"active": cls.DEFAULT_PROFILE, "profiles": [cls.DEFAULT_PROFILE]}
        return _safe_load_json(cls.PROFILES_META)

    @classmethod
    def _save_profiles_meta(cls, meta: dict[str, Any]):
        """Save profiles metadata."""
        cls.PROFILES_META.write_text(json.dumps(meta, indent=2))

    @classmethod
    def get_active_profile(cls) -> str:
        """Get the name of the currently active profile."""
        meta = cls._load_profiles_meta()
        return meta.get("active", cls.DEFAULT_PROFILE)

    @classmethod
    def set_active_profile(cls, profile_name: str):
        """Set the active profile."""
        meta = cls._load_profiles_meta()
        if profile_name not in meta["profiles"]:
            raise ValueError(f"Profile '{profile_name}' does not exist")
        meta["active"] = profile_name
        cls._save_profiles_meta(meta)

    @classmethod
    def list_profiles(cls) -> list[str]:
        """List all available profiles."""
        meta = cls._load_profiles_meta()
        return meta.get("profiles", [cls.DEFAULT_PROFILE])

    @classmethod
    def create_profile(cls, profile_name: str, copy_from: str | None = None):
        """Create a new profile, optionally copying settings from another profile."""
        meta = cls._load_profiles_meta()

        if profile_name in meta["profiles"]:
            raise ValueError(f"Profile '{profile_name}' already exists")

        # Create profiles directory if it doesn't exist
        cls.PROFILES_DIR.mkdir(exist_ok=True, parents=True)

        profile_path = cls._get_profile_path(profile_name)

        if copy_from:
            # Copy settings from another profile
            source_settings = cls._load_profile_settings(copy_from)
            profile_path.write_text(json.dumps(source_settings, indent=2))

            # Copy API key from source profile
            source_key = keyring.get_password(cls.KEYRING_SYSTEM_NAME, cls._get_profile_keyring_key(copy_from))
            if source_key:
                keyring.set_password(cls.KEYRING_SYSTEM_NAME, cls._get_profile_keyring_key(profile_name), source_key)
        else:
            # Create empty profile
            profile_path.write_text(json.dumps({}, indent=2))

        # Add to profiles list
        meta["profiles"].append(profile_name)
        cls._save_profiles_meta(meta)

    @classmethod
    def delete_profile(cls, profile_name: str):
        """Delete a profile."""
        if profile_name == cls.DEFAULT_PROFILE:
            raise ValueError("Cannot delete the default profile")

        meta = cls._load_profiles_meta()

        if profile_name not in meta["profiles"]:
            raise ValueError(f"Profile '{profile_name}' does not exist")

        # If deleting active profile, switch to default
        if meta["active"] == profile_name:
            meta["active"] = cls.DEFAULT_PROFILE

        # Remove profile file
        profile_path = cls._get_profile_path(profile_name)
        if profile_path.exists():
            profile_path.unlink()

        # Remove API key from keyring
        try:
            keyring.delete_password(cls.KEYRING_SYSTEM_NAME, cls._get_profile_keyring_key(profile_name))
        except:
            pass  # Key might not exist

        # Remove from profiles list
        meta["profiles"].remove(profile_name)
        cls._save_profiles_meta(meta)

    @classmethod
    def _migrate_legacy_settings(cls):
        """Migrate legacy settings.json to default profile."""
        # Create profiles directory
        cls.PROFILES_DIR.mkdir(exist_ok=True, parents=True)

        # Load legacy settings
        legacy_settings = {}
        if cls.SETTINGS.exists():
            legacy_settings = _safe_load_json(cls.SETTINGS)
            # Remove api_key if present (should have been migrated to keyring already)
            legacy_settings.pop("console_api_key", None)

        # Save to default profile
        default_profile_path = cls._get_profile_path(cls.DEFAULT_PROFILE)
        default_profile_path.write_text(json.dumps(legacy_settings, indent=2))

        # Migrate API key from legacy keyring location
        legacy_key = keyring.get_password(cls.KEYRING_SYSTEM_NAME, cls.KEYRING_USERNAME)
        if legacy_key:
            keyring.set_password(cls.KEYRING_SYSTEM_NAME, cls._get_profile_keyring_key(cls.DEFAULT_PROFILE), legacy_key)

        # Create profiles metadata
        meta = {"active": cls.DEFAULT_PROFILE, "profiles": [cls.DEFAULT_PROFILE]}
        cls._save_profiles_meta(meta)

    @classmethod
    def _load_profile_settings(cls, profile_name: str) -> dict[str, Any]:
        """Load settings for a specific profile."""
        profile_path = cls._get_profile_path(profile_name)
        if not profile_path.exists():
            return {}
        return _safe_load_json(profile_path)

    @classmethod
    def write_user_settings(cls, key: str, value: Any):
        """Write a setting to the active profile."""
        # Ensure migration has happened
        if not cls.PROFILES_META.exists():
            cls._migrate_legacy_settings()

        active_profile = cls.get_active_profile()
        settings = cls._load_profile_settings(active_profile)
        settings[key] = value

        profile_path = cls._get_profile_path(active_profile)
        profile_path.write_text(json.dumps(settings, indent=2))

    @classmethod
    def load_user_settings(cls) -> dict[str, Any]:
        """Load settings from the active profile."""
        # Check if we need to migrate from legacy settings
        if not cls.PROFILES_META.exists():
            # First time using profiles - migrate legacy settings
            cls._migrate_legacy_settings()

        # Get active profile
        active_profile = cls.get_active_profile()

        # Load profile settings
        settings = cls._load_profile_settings(active_profile)

        # Load API key from keyring for this profile
        profile_key = cls._get_profile_keyring_key(active_profile)
        settings["console_api_key"] = keyring.get_password(cls.KEYRING_SYSTEM_NAME, profile_key) or ""

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
