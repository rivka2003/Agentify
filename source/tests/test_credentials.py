"""Interactive credential prompting: masking + return shape (hermetic)."""

from agentify.credentials import is_secret_field, prompt_credentials


def test_is_secret_field():
    assert is_secret_field("password")
    assert is_secret_field("api_token")
    assert is_secret_field("PASSCODE")  # contains "pass"
    assert is_secret_field("otp")
    assert not is_secret_field("username")
    assert not is_secret_field("email")


def test_prompt_masks_secrets_and_returns_values():
    visible_prompts: list[str] = []
    masked_prompts: list[str] = []

    def fake_input(prompt: str) -> str:
        visible_prompts.append(prompt)
        return "alice"

    def fake_getpass(prompt: str) -> str:
        masked_prompts.append(prompt)
        return "s3cret"

    creds = prompt_credentials(
        ["username", "password"],
        tool_name="login",
        input_fn=fake_input,
        getpass_fn=fake_getpass,
        echo=lambda *a, **k: None,
    )

    assert creds == {"username": "alice", "password": "s3cret"}
    # username read visibly, password read without echo.
    assert len(visible_prompts) == 1 and "username" in visible_prompts[0]
    assert len(masked_prompts) == 1 and "password" in masked_prompts[0]


def test_prompt_preserves_field_order():
    creds = prompt_credentials(
        ["email", "password"],
        input_fn=lambda p: "x",
        getpass_fn=lambda p: "y",
        echo=lambda *a, **k: None,
    )
    assert list(creds.keys()) == ["email", "password"]
