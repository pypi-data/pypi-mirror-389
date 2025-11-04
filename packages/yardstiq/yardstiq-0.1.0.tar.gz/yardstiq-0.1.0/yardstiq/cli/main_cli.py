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

from typing import List
from pathlib import Path
from typing_extensions import Annotated

from . import backend_cli, benchmark_cli, provider_cli, dataset_cli

from ..core.plugins import load_all_plugins

LoadOption = Annotated[
    List[Path],
    typer.Option(
        "--load",
        help="Load a .py local file plugin. Can be used many times.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
]

app = typer.Typer(
    name="ys",
    help="Yardstiq: Quantum Benchmarking CLI and extensible tool.",
    no_args_is_help=True,
)

app.add_typer(benchmark_cli.app, name="benchmark")
app.add_typer(provider_cli.app, name="provider")
app.add_typer(backend_cli.app, name="backend")
app.add_typer(dataset_cli.app, name="dataset")


@app.callback()
def main_callback(load: LoadOption = None):
    """
    Callback global of the CLI.
    Executed before any command.
    This will load all plugins (installed, project, and local files).
    """
    load_all_plugins(local_files=load)
