"""Per-site registry: load/save recipes/<slug>.tools.json, convert to OpenAI tools."""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .recipe import Recipe


DEFAULT_RECIPES_DIR = Path(__file__).resolve().parent.parent / "recipes"
DEFAULT_SESSIONS_DIR = Path(__file__).resolve().parent.parent / "sessions"


@dataclass
class AuthConfig:
    """How to authenticate to a site and where its session is cached.

    Produced at map time when a ``login`` tool is recorded. Contains NO secrets —
    only the login tool's name, a cheap success probe (``{kind, ...}``, replayed
    to test whether a session is still valid), and the relative path to the
    gitignored ``storage_state`` file.
    """

    type: str = "form_login"
    login_tool: str = ""
    check: dict = field(default_factory=dict)
    storage_state: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "login_tool": self.login_tool,
            "check": self.check,
            "storage_state": self.storage_state,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AuthConfig":
        return cls(
            type=d.get("type", "form_login"),
            login_tool=d.get("login_tool", ""),
            check=d.get("check") or {},
            storage_state=d.get("storage_state", ""),
        )


@dataclass
class SiteRegistry:
    site: str
    base_url: str
    tools: list[Recipe] = field(default_factory=list)
    mapped_at: str = ""
    auth: Optional[AuthConfig] = None

    def find(self, name: str) -> Optional[Recipe]:
        for r in self.tools:
            if r.name == name:
                return r
        return None

    def to_dict(self) -> dict:
        d = {
            "site": self.site,
            "base_url": self.base_url,
            "mapped_at": self.mapped_at or _dt.datetime.utcnow().isoformat() + "Z",
            "tools": [t.to_dict() for t in self.tools],
        }
        # Only emit `auth` for sites that actually have a login tool, so
        # auth-free registries serialize exactly as they did before.
        if self.auth is not None:
            d["auth"] = self.auth.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SiteRegistry":
        return cls(
            site=d["site"],
            base_url=d.get("base_url", ""),
            tools=[Recipe.from_dict(t) for t in d.get("tools", [])],
            mapped_at=d.get("mapped_at", ""),
            auth=AuthConfig.from_dict(d["auth"]) if d.get("auth") else None,
        )


def registry_path(slug: str, recipes_dir: Path = DEFAULT_RECIPES_DIR) -> Path:
    return recipes_dir / f"{slug}.tools.json"


def session_path(slug: str, sessions_dir: Path = DEFAULT_SESSIONS_DIR) -> Path:
    """Absolute path of the gitignored storage_state file for a site."""
    return sessions_dir / f"{slug}.json"


def load(slug: str, recipes_dir: Path = DEFAULT_RECIPES_DIR) -> SiteRegistry:
    path = registry_path(slug, recipes_dir)
    with open(path, "r", encoding="utf-8") as f:
        return SiteRegistry.from_dict(json.load(f))


def save(registry: SiteRegistry, recipes_dir: Path = DEFAULT_RECIPES_DIR) -> Path:
    recipes_dir.mkdir(parents=True, exist_ok=True)
    path = registry_path(registry.site, recipes_dir)
    if not registry.mapped_at:
        registry.mapped_at = _dt.datetime.utcnow().isoformat() + "Z"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry.to_dict(), f, indent=2)
    return path


def to_openai_tools(registry: SiteRegistry) -> list[dict]:
    """Translate each Recipe to the OpenAI function-calling tool shape."""
    return [
        {
            "type": "function",
            "function": {
                "name": r.name,
                "description": r.description,
                "parameters": r.parameters or {"type": "object", "properties": {}},
            },
        }
        for r in registry.tools
    ]
