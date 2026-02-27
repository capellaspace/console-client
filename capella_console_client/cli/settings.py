import typer
import questionary
import keyring

from tabulate import tabulate

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client.cli.validate import (
    _must_be_type,
    _validate_dir_exists,
    _validate_api_key,
    _no_selection_bye,
    _at_least_one_selected,
)
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.config import (
    CLI_SUPPORTED_RESULT_HEADERS,
    CURRENT_SETTINGS,
    SearchFilterOrderOption,
)
from capella_console_client.cli.prompt_helpers import get_first_checked
from capella_console_client.logconf import logger


app = typer.Typer(help="fine tune settings")
profile_app = typer.Typer(help="manage settings profiles")


def _prompt_search_result_headers() -> list[str]:
    choices = [
        questionary.Choice(cur, checked=cur in CURRENT_SETTINGS["search_headers"])
        for cur in CLI_SUPPORTED_RESULT_HEADERS
    ]

    search_result_fields = questionary.checkbox(
        "Which STAC item fields would you like to display in the search results table ?",
        choices=choices,
        initial_choice=get_first_checked(choices),
        validate=_at_least_one_selected,
    ).ask()
    _no_selection_bye(search_result_fields, info_msg="no valid path provided")

    return search_result_fields


@app.command()
def show():
    """
    show current settings
    """
    typer.secho("Current settings:\n", underline=True)
    table_data = list(CURRENT_SETTINGS.items())
    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers=["setting", "value"]))


@app.command()
def result_table():
    """
    set fields (STAC properties) of search results table
    """
    search_result_headers = _prompt_search_result_headers()

    CLICache.write_user_settings("search_headers", search_result_headers)
    typer.echo("updated fields that to will be displayed in search results table")


@app.command()
def limit():
    """
    set default limit to be used in searches
    """
    limit = questionary.text(
        "Specify default limit to be used in searches (can be overridden at search time):",
        default=str(CURRENT_SETTINGS["limit"]),
        validate=_must_be_type(int),
    ).ask()
    _no_selection_bye(limit, info_msg="no valid limit provided")

    if int(limit) > 0:
        CLICache.write_user_settings("limit", int(limit))
        typer.echo(f"updated default search limit to {limit}")
    else:
        typer.echo("invalid limit")


@app.command()
def api_url():
    """
    set Capella API url
    """
    api_url = questionary.text(
        "API url:",
        default=CURRENT_SETTINGS.get("capella_api_url", CONSOLE_API_URL),
    ).ask()
    _no_selection_bye(api_url)

    CLICache.write_user_settings("capella_api_url", api_url)
    typer.echo("updated capella API URL")


@app.command()
def api_key():
    """
    set API key for Capella Console (for active profile)
    """
    active_profile = CLICache.get_active_profile()
    console_api_key = questionary.password(
        f"Console API key (for profile '{active_profile}'):",
        default=CURRENT_SETTINGS.get("console_api_key", ""),
        validate=_validate_api_key,
    ).ask()
    _no_selection_bye(console_api_key)

    if console_api_key:
        profile_key = CLICache._get_profile_keyring_key(active_profile)
        keyring.set_password(CLICache.KEYRING_SYSTEM_NAME, profile_key, console_api_key)
        typer.echo(f"updated API key for profile '{active_profile}'")
        return True

    return False


@app.command()
def output():
    """
    set default output location for downloads and .json STAC exports
    """
    out_path = questionary.path(
        "Specify the default location for downloads and .json STAC exports: (press <tab>)",
        default=CURRENT_SETTINGS["out_path"],
        validate=_validate_dir_exists,
    ).ask()
    _no_selection_bye(out_path)

    CLICache.write_user_settings("out_path", out_path)
    typer.echo("updated default output path for .json STAC exports")


@app.command()
def search_filter_order():
    """
    set order of search filters to be used in searches
    """
    search_filter_order = questionary.select(
        "Specify the order of search filters to be used in searches:",
        choices=list(SearchFilterOrderOption),
        default=SearchFilterOrderOption[CURRENT_SETTINGS["search_filter_order"]],
    ).ask()

    _no_selection_bye(search_filter_order, info_msg="no valid search filter order provided")
    CLICache.write_user_settings("search_filter_order", SearchFilterOrderOption(search_filter_order).name)
    typer.echo("updated order of search filters to be used in searches")


@profile_app.command("list")
def profile_list():
    """
    list all profiles
    """
    profiles = CLICache.list_profiles()
    active = CLICache.get_active_profile()

    typer.secho("\nAvailable profiles:\n", underline=True)
    for profile in profiles:
        marker = " (active)" if profile == active else ""
        typer.echo(f"  • {profile}{marker}")
    typer.echo()


@profile_app.command("show")
def profile_show(profile_name: str | None = None):
    """
    show settings for a specific profile
    """
    if not profile_name:
        profile_name = CLICache.get_active_profile()

    if profile_name not in CLICache.list_profiles():
        typer.secho(f"Profile '{profile_name}' does not exist", fg="red")
        raise typer.Exit(1)

    settings = CLICache._load_profile_settings(profile_name)
    profile_key = CLICache._get_profile_keyring_key(profile_name)
    api_key_set = bool(keyring.get_password(CLICache.KEYRING_SYSTEM_NAME, profile_key))

    settings_display = {**settings, "console_api_key": "***" if api_key_set else "(not set)"}

    typer.secho(f"\nSettings for profile '{profile_name}':\n", underline=True)
    table_data = list(settings_display.items())
    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers=["setting", "value"]))


@profile_app.command("create")
def profile_create(
    profile_name: str | None = typer.Argument(None, help="Name of the new profile"),
    copy_from: str | None = typer.Option(None, "--copy-from", help="Copy settings from this profile"),
):
    """
    create a new profile
    """
    # Prompt for profile name if not provided
    if not profile_name:
        profile_name = questionary.text(
            "Profile name:", validate=lambda text: True if text.strip() else "Profile name cannot be empty"
        ).ask()

        if not profile_name:
            typer.echo("Profile creation cancelled")
            return

    try:
        if copy_from and copy_from not in CLICache.list_profiles():
            typer.secho(f"Source profile '{copy_from}' does not exist", fg="red")
            raise typer.Exit(1)

        CLICache.create_profile(profile_name, copy_from=copy_from)

        if copy_from:
            typer.secho(f"Created profile '{profile_name}' (copied from '{copy_from}')", fg="green")
        else:
            typer.secho(f"Created profile '{profile_name}'", fg="green")

        # Always prompt to configure after creation
        if questionary.confirm(f"Would you like to configure profile '{profile_name}' now?").ask():
            # Save current active profile
            original_profile = CLICache.get_active_profile()

            # Switch to new profile
            CLICache.set_active_profile(profile_name)
            typer.secho(f"\nConfiguring profile '{profile_name}'...\n", fg="cyan")

            try:
                configure()
            except (KeyboardInterrupt, Exception):
                # Restore original profile on error or Ctrl+C
                CLICache.set_active_profile(original_profile)
                typer.secho(f"\nConfiguration interrupted. Switched back to '{original_profile}'", fg="yellow")
                return

            # Ask if they want to keep new profile active
            typer.echo()
            if questionary.confirm(f"Keep '{profile_name}' as active profile?").ask():
                typer.secho(f"Profile '{profile_name}' is now active", fg="green")
            else:
                CLICache.set_active_profile(original_profile)
                typer.secho(f"Switched back to '{original_profile}'", fg="green")

    except ValueError as e:
        typer.secho(str(e), fg="red")
        raise typer.Exit(1)


@profile_app.command("switch")
def profile_switch(profile_name: str = typer.Argument(..., help="Name of the profile to activate")):
    """
    switch to a different profile
    """
    try:
        CLICache.set_active_profile(profile_name)
        typer.secho(f"Switched to profile '{profile_name}'", fg="green")
    except ValueError as e:
        typer.secho(str(e), fg="red")
        raise typer.Exit(1)


@profile_app.command("delete")
def profile_delete(profile_name: str = typer.Argument(..., help="Name of the profile to delete")):
    """
    delete a profile
    """
    # Confirm deletion
    if not questionary.confirm(
        f"Are you sure you want to delete profile '{profile_name}'? This cannot be undone."
    ).ask():
        typer.echo("Deletion cancelled")
        return

    try:
        CLICache.delete_profile(profile_name)
        typer.secho(f"Deleted profile '{profile_name}'", fg="green")
    except ValueError as e:
        typer.secho(str(e), fg="red")
        raise typer.Exit(1)


@profile_app.command("copy")
def profile_copy(
    source: str = typer.Argument(..., help="Source profile name"),
    destination: str = typer.Argument(..., help="Destination profile name"),
):
    """
    copy a profile to a new profile
    """
    try:
        if source not in CLICache.list_profiles():
            typer.secho(f"Source profile '{source}' does not exist", fg="red")
            raise typer.Exit(1)

        CLICache.create_profile(destination, copy_from=source)
        typer.secho(f"Copied profile '{source}' to '{destination}'", fg="green")
    except ValueError as e:
        typer.secho(str(e), fg="red")
        raise typer.Exit(1)


# Mount profile commands to main app
app.add_typer(profile_app, name="profile")


def configure():
    active_profile = CLICache.get_active_profile()
    logger.info(
        typer.style(f"let's get you all setup using capella-console-wizard (profile: {active_profile}):", bold=True)
    )
    logger.info("\t\tPress Ctrl + C anytime to quit\n")
    api_url()
    # Don't prompt for user if there is an api key
    api_key()
    output()
    search_filter_order()
    result_table()
    limit()
