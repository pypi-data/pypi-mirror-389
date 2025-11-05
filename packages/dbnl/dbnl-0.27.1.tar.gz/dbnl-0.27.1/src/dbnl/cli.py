from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar

import click
import yaml
from click import ClickException

from dbnl import __version__, config
from dbnl.api import get_spec
from dbnl.errors import DBNLError
from dbnl.sandbox import (
    SandboxError,
    default_base_url,
    default_registry,
    default_version,
    sandbox_delete,
    sandbox_exec,
    sandbox_logs,
    sandbox_start,
    sandbox_status,
    sandbox_stop,
)
from dbnl.sdk.core import login as core_login

if TYPE_CHECKING:
    from typing_extensions import ParamSpec
else:
    # Stub ParamSpec.
    class ParamSpec:
        def __init__(*args: Any, **kwargs: Any):
            pass


P = ParamSpec("P")
T = TypeVar("T")


def login_required(fn: Callable[P, T]) -> Callable[P, T]:
    """
    Require login before executing command. Tries to login using the config file. On login fail, exits with error code.
    """

    @wraps(fn)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        # Try to login.
        try:
            core_login(verify=True)
        except DBNLError as exc:
            raise ClickException(str(exc)) from exc
        # Call command.
        return fn(*args, **kwargs)

    return wrapped


@click.group()
@click.version_option()
def cli() -> None:
    """The dbnl CLI."""
    pass


@cli.command()
@click.argument("api_token", envvar="DBNL_API_TOKEN")
@click.option("--api-url", envvar="DBNL_API_URL", default="https://api.dbnl.com/", help="API url")
@click.option("--app-url", envvar="DBNL_APP_URL", default=None, help="App url")
@click.option("--namespace-id", envvar="DBNL_NAMESPACE_ID", default=None, help="Namespace id")
def login(api_token: str, api_url: str, app_url: Optional[str], namespace_id: Optional[str]) -> None:
    """Login to dbnl."""
    # Try to login.
    try:
        core_login(api_token=api_token, api_url=api_url, app_url=app_url, namespace_id=namespace_id)
    except DBNLError as exc:
        raise ClickException(str(exc)) from exc
    # Write config to file.
    config.save()
    click.echo("Login Succeeded")


@cli.command()
def logout() -> None:
    """Logout of dbnl."""
    config.reset(delete=True)
    click.echo("Logout Succeeded")


@cli.command()
@login_required
def info() -> None:
    """Info about SDK and API."""
    spec = get_spec()
    info = {
        "sdk": {
            "version": __version__,
        },
        "api": {
            "version": spec["info"]["version"],
            "url": config.api_url(),
        },
    }
    click.echo(yaml.dump(info, sort_keys=False))


@cli.group()
def sandbox() -> None:
    """Subcommand to interact with the sandbox."""
    pass


class NotEmpty(click.ParamType):
    """A parameter type that is not empty."""

    name = "not_empty"

    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> str:
        if not value:
            if param is None:
                self.fail("Parameter must not be empty")
            self.fail(f"{param.name} must not be empty", param=param)
        return value


@sandbox.command()
@click.option("-u", "--registry-username", help="Registry username")
@click.option("-p", "--registry-password", hide_input=True, help="Registry password", type=NotEmpty())
@click.option("--registry", help="Registry")
@click.option("--version", default=default_version(), help="Sandbox version", show_default=True)
@click.option("--base-url", default=default_base_url(), help="Sandbox base url", show_default=True)
def start(
    registry_username: Optional[str],
    registry_password: Optional[str],
    registry: Optional[str],
    version: str,
    base_url: str,
) -> None:
    """Start the sandbox."""
    if registry is None:
        registry = default_registry(version)
    try:
        sandbox_start(registry_username, registry_password, registry, version, base_url)
    except SandboxError as exc:
        raise ClickException(exc.message) from exc
    click.echo("Sandbox starting. To see progress run: dbnl sandbox logs")


@sandbox.command()
def logs() -> None:
    """Tail the sandbox logs."""
    try:
        sandbox_logs()
    except SandboxError as exc:
        raise ClickException(exc.message) from exc


@sandbox.command()
@click.argument("command", nargs=-1)
def exec(command: tuple[str, ...]) -> None:
    """Exec a command on the sandbox."""
    try:
        sandbox_exec(list(command))
    except SandboxError as exc:
        raise ClickException(exc.message) from exc


@sandbox.command()
def stop() -> None:
    """Stop the sandbox."""
    try:
        sandbox_stop()
    except SandboxError as exc:
        raise ClickException(exc.message) from exc
    click.echo("Sandbox stopped.")


@sandbox.command()
def status() -> None:
    """Get sandbox status."""
    try:
        click.echo(sandbox_status())
    except SandboxError as exc:
        raise ClickException(exc.message) from exc


@sandbox.command()
@click.option("--force", "-f", is_flag=True, help="Force delete")
def delete(force: bool) -> None:
    """Delete sandbox data."""
    if not force:
        click.confirm("Are you sure you want to delete the sandbox data?", abort=True)
    try:
        sandbox_delete()
    except SandboxError as exc:
        raise ClickException(exc.message) from exc
    click.echo("Sandbox data deleted.")


if __name__ == "__main__":
    cli()
