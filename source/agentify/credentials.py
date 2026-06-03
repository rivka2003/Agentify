"""Interactive credential prompting for login recipes.

Used at MAP time only, to drive a site's sign-in form and create a reusable
session. Credentials are returned in memory to the caller and are NEVER written
to disk, logged, or stored in any recipe/registry — only the resulting browser
``storage_state`` (cookies/localStorage) is persisted, to a gitignored path.

The prompt functions are injectable (``input_fn``/``getpass_fn``/``echo``) so the
behaviour is unit-testable without a real terminal.
"""

from __future__ import annotations

import getpass
import re
from typing import Callable, Iterable

# Field names that look like secrets are read without terminal echo.
_SECRET_RE = re.compile(r"pass|secret|token|otp|pin|key|code", re.IGNORECASE)


def is_secret_field(name: str) -> bool:
    """True if a credential field's name suggests it holds a secret."""
    return bool(_SECRET_RE.search(name or ""))


def prompt_credentials(
    fields: Iterable[str],
    *,
    tool_name: str = "",
    input_fn: Callable[[str], str] = input,
    getpass_fn: Callable[[str], str] = getpass.getpass,
    echo: Callable[..., None] = print,
) -> dict[str, str]:
    """Prompt the user for each credential field; return ``{field: value}``.

    Secret-looking fields (password/secret/token/…) are read without echo via
    ``getpass``; the rest are read with a visible prompt. Nothing is persisted —
    the returned values live only as long as the caller keeps them.
    """
    if tool_name:
        echo(
            f"Enter credentials for {tool_name!r} "
            "(used only to record the login and create a session; never saved to disk):"
        )
    creds: dict[str, str] = {}
    for field in fields:
        prompt = f"  {field}: "
        creds[field] = getpass_fn(prompt) if is_secret_field(field) else input_fn(prompt)
    return creds
