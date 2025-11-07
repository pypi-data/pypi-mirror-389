# Copyright 2025 Scaleway, Aqora, Quantum Commons
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import typer

from typing_extensions import Annotated

from ..core.impl import provider_impl

app = typer.Typer(
    name="provider", help="Manage Yardstiq provider plugins.", no_args_is_help=True
)


@app.command("add")
def add_provider(
    provider_name: Annotated[
        str,
        typer.Argument(help="Provider name from the catalog (e.g., 'scaleway-qpu')"),
    ]
):
    """Installs a provider from the official catalog via pip."""

    typer.echo(f"Installing provider '{provider_name}'...")
    try:
        # Call the business logic
        result = provider_impl.add_provider(provider_name)

        # Print the result
        typer.secho(
            f"✅ Successfully installed '{result['package']}'.", fg=typer.colors.GREEN
        )
    except (KeyError, RuntimeError) as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("rm")
def remove_provider(
    provider_name: Annotated[
        str,
        typer.Argument(help="Provider name from the catalog (e.g., 'scaleway-qpu')"),
    ]
):
    """Uninstalls a provider via pip."""

    typer.echo(f"Uninstalling provider '{provider_name}'...")
    try:
        # Call the business logic
        result = provider_impl.remove_provider(provider_name)

        # Print the result
        typer.secho(
            f"✅ Successfully uninstalled '{result['package']}'.", fg=typer.colors.GREEN
        )
    except (KeyError, RuntimeError) as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("ls")
def list_providers():
    """Lists all official providers from the catalog."""

    typer.echo("Known provider catalog:")

    catalog = provider_impl.list_known_providers()

    if not catalog:
        typer.echo("  Catalog is empty or could not be loaded.")
        return

    for name, info in catalog.items():
        typer.echo(f"- {typer.style(name, bold=True)} ({info['package_name']})")
        typer.echo(f"  {info['description']}\n")
