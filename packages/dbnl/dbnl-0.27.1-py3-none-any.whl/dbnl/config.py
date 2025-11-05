import json
import os
import re
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Literal, Optional
from urllib.parse import ParseResult, urlparse, urlunparse

from dbnl.errors import DBNLConfigurationError

DBNL_DIR = Path.home() / ".dbnl"
DBNL_CONFIG_FILE = DBNL_DIR / "config.json"


@dataclass
class _Config:
    api_token: str = field(
        metadata={
            "env": "DBNL_API_TOKEN",
            "required": True,
        }
    )
    api_url: str = field(
        metadata={
            "env": "DBNL_API_URL",
            "required": True,
        }
    )
    app_url: str = field(
        metadata={
            "env": "DBNL_APP_URL",
        }
    )
    namespace_id: Optional[str] = field(
        default=None,
        metadata={
            "env": "DBNL_NAMESPACE_ID",
        },
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"] = field(
        default="WARNING",
        metadata={
            "env": "DBNL_LOG_LEVEL",
        },
    )

    @classmethod
    def load(cls, **kwargs: Any) -> "_Config":
        """
        Load config with the following precedence (highest to lowest):

            1. kwargs
            2. environment variables
            3. config file
        """
        # Load from file.
        config = cls._load_file()
        # Override with environment variables.
        for f in fields(_Config):
            env = f.metadata.get("env")
            if env is None:
                raise ValueError(f"Field {f.name} is missing `env` metadata.")
            if env in os.environ:
                config[f.name] = os.environ[env]
        # Override with arguments.
        for f in fields(_Config):
            if f.name in kwargs:
                config[f.name] = kwargs[f.name]
        # Check required fields.
        for f in fields(_Config):
            if f.metadata.get("required") and f.name not in config:
                raise DBNLConfigurationError(f"Missing required config field: {f.name}.")
        # Infer app_url from api_url if not set.
        if not "app_url" in config:
            config["app_url"] = cls._infer_app_url_from_api_url(config["api_url"])
        return _Config(**config)

    @classmethod
    def _load_file(cls) -> dict[str, Any]:
        if Path.exists(DBNL_CONFIG_FILE):
            with open(DBNL_CONFIG_FILE) as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise DBNLConfigurationError(f"Invalid config file: {DBNL_CONFIG_FILE}. Expected a JSON object.")
                return data
        return {}

    @classmethod
    def _infer_app_url_from_api_url(cls, api_url: str) -> str:
        parsed = urlparse(api_url)
        dbnl_domain_re = re.compile(r"^api(|-.*|\..*)\.dbnl\.com(|:.*)$")
        if dbnl_domain_re.search(parsed.netloc):
            app_netloc = "app" + parsed.netloc[len("api") :]
            path = parsed.path
        else:
            app_netloc = parsed.netloc
            # assume that the root is the app
            path = ""
        if not path.endswith("/"):
            path += "/"
        return urlunparse(
            ParseResult(
                scheme=parsed.scheme,
                netloc=app_netloc,
                path=path,
                params="",
                query="",
                fragment="",
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_token": self.api_token,
            "api_url": self.api_url,
            "app_url": self.app_url,
            "namespace_id": self.namespace_id,
            "log_level": self.log_level,
        }

    def to_json(self, indent: Optional[int]) -> str:
        return json.dumps(self.to_dict(), indent=indent)


_CONFIG: Optional[_Config] = None


def load(
    api_token: Optional[str] = None,
    api_url: Optional[str] = None,
    app_url: Optional[str] = None,
    namespace_id: Optional[str] = None,
    log_level: Optional[str] = None,
) -> None:
    global _CONFIG  # noqa: PLW0603
    kwargs = {}
    if api_token is not None:
        kwargs["api_token"] = api_token
    if api_url is not None:
        kwargs["api_url"] = api_url
    if app_url is not None:
        kwargs["app_url"] = app_url
    if namespace_id is not None:
        kwargs["namespace_id"] = namespace_id
    if log_level is not None:
        kwargs["log_level"] = log_level
    _CONFIG = _Config.load(**kwargs)


def save() -> None:
    if _CONFIG is None:
        raise DBNLConfigurationError("Config not loaded.")
    DBNL_DIR.mkdir(parents=True, exist_ok=True)
    with open(DBNL_CONFIG_FILE, "w") as f:
        f.write(_CONFIG.to_json(indent=2))


def loaded() -> bool:
    return _CONFIG is not None


def reset(delete: bool = False) -> None:
    global _CONFIG  # noqa: PLW0603
    _CONFIG = None
    if delete and DBNL_CONFIG_FILE.exists():
        DBNL_CONFIG_FILE.unlink()


def api_token() -> str:
    if _CONFIG is None:
        raise DBNLConfigurationError("Config not loaded.")
    return _CONFIG.api_token


def api_url() -> str:
    if _CONFIG is None:
        raise DBNLConfigurationError("Config not loaded.")
    return _CONFIG.api_url


def app_url() -> str:
    if _CONFIG is None:
        raise DBNLConfigurationError("Config not loaded.")
    return _CONFIG.app_url


def namespace_id() -> Optional[str]:
    if _CONFIG is None:
        raise DBNLConfigurationError("Config not loaded.")
    return _CONFIG.namespace_id


def log_level() -> Literal["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"]:
    if _CONFIG is None:
        raise DBNLConfigurationError("Config not loaded.")
    return _CONFIG.log_level
