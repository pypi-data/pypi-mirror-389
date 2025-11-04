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

from ..core.impl import backend_impl

app = typer.Typer(
    name="backend", help="Manage and list available backends.", no_args_is_help=True
)


@app.command("ls")
def list_backends():
    """Lists all discovered backend (installed and local)."""

    typer.echo("Available backends:")
    backends = backend_impl.list_available_backends()

    if not backends:
        typer.echo("  No backend found.")
        return

    for name in backends:
        typer.echo(f"- {typer.style(name, bold=True)}")
