"""`_coerce_login_type`: deterministic login tagging, signup excluded."""

from agentify.mapper import ToolProposal, _coerce_login_type


def _mk(name, params, *, tool_type="action", desc="", url=""):
    return ToolProposal(
        name=name,
        description=desc,
        parameters={"type": "object", "properties": {p: {"type": "string"} for p in params}},
        tool_type=tool_type,
        start_url=url,
    )


def test_signin_with_password_is_coerced():
    p = _mk("login", ["email", "password"], desc="Sign in to your account", url="https://x/login")
    _coerce_login_type([p])
    assert p.tool_type == "login"


def test_pure_signup_on_login_page_is_not_coerced():
    # Shares the /login URL and has a password field, but only creates an account.
    p = _mk("signup", ["name", "email", "password"], desc="Create a new account", url="https://x/login")
    _coerce_login_type([p])
    assert p.tool_type == "action"


def test_merged_signup_login_is_coerced():
    # A combined tool can still sign in (its name carries "login").
    p = _mk("signup_login", ["email", "password"], desc="Sign up or log in", url="https://x/login")
    _coerce_login_type([p])
    assert p.tool_type == "login"


def test_password_change_without_signin_signal_stays_action():
    p = _mk("change_password", ["old_password", "new_password"], desc="Update your password", url="https://x/settings")
    _coerce_login_type([p])
    assert p.tool_type == "action"


def test_login_words_without_secret_field_not_coerced():
    p = _mk("search", ["query"], desc="Sign in required to search", url="https://x/login")
    _coerce_login_type([p])
    assert p.tool_type == "action"


def test_existing_login_label_preserved():
    p = _mk("login", ["username", "password"], tool_type="login")
    _coerce_login_type([p])
    assert p.tool_type == "login"
