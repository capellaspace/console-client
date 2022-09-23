from typing import List
import questionary


def get_first_checked(choices: List[questionary.Choice], prev_search=None) -> questionary.Choice:
    first_checked = choices[0]
    if prev_search:
        first_checked = next(c for c in choices if c.checked)
    return first_checked
