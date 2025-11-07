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

from ..core.impl import dataset_impl

app = typer.Typer(
    name="dataset", help="Manage and list available Datasets.", no_args_is_help=True
)


@app.command("ls")
def list_datasets():
    """Lists all discovered Datasets (installed and local)."""

    typer.echo("Available Datasets:")
    datasets = dataset_impl.list_available_datasets()

    if not datasets:
        typer.echo("  No datasets found.")
        return

    for name in datasets:
        typer.echo(f"- {typer.style(name, bold=True)}")
