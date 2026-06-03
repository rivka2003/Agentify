"""`_derive_login_check`: leak-free probe that matches the real control."""

from types import SimpleNamespace as NS

from agentify.mapper import _derive_login_check


def _obs(url, elements):
    return NS(url=url, elements=[NS(role=r, name=n) for r, n in elements])


def test_logout_token_preserves_site_spelling():
    # Site uses "Logout" (no space) — the probe must store it verbatim, or
    # Playwright's substring name match won't resolve it at replay.
    check = _derive_login_check(_obs("https://x.test/home", [("link", "Logout")]))
    assert check == {
        "kind": "element_exists",
        "target": {"role": "link", "name": "Logout"},
    }


def test_logout_drops_trailing_identifier():
    check = _derive_login_check(
        _obs("https://x.test/home", [("link", "Log out (alice@x.test)")])
    )
    assert check["target"]["name"] == "Log out"
    assert "alice" not in str(check)  # no account identifier leaks


def test_falls_back_to_url_path_without_logout_control():
    check = _derive_login_check(
        _obs("https://x.test/account/dashboard", [("button", "Menu")])
    )
    assert check == {"kind": "url_contains", "value": "/account/dashboard"}


def test_empty_probe_at_root_with_no_control():
    assert _derive_login_check(_obs("https://x.test/", [])) == {}
