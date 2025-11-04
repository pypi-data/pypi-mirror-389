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
import json
import typer

from typing_extensions import Annotated

from ..core.impl import benchmark_impl

app = typer.Typer(
    name="benchmark", help="Run, list and manage benchmarks.", no_args_is_help=True
)


@app.command("run")
def run(
    benchmark_name: Annotated[
        str, typer.Argument(help="Name of the benchmark (e.g., 'vqe')")
    ],
    qpu_name: Annotated[
        str, typer.Option(help="QPU to run on (e.g., 'local/qiskit-aer')")
    ],
    dataset_name: Annotated[
        str, typer.Option(help="Dataset to use (e.g., 'aqora/h2-molecule')")
    ] = None,
    params: Annotated[str, typer.Option(help="JSON string of extra params")] = "{}",
):
    """Runs a specific benchmark on a specific QPU."""

    typer.echo(f"🚀 Initializing benchmark '{benchmark_name}' on '{qpu_name}'...")

    try:
        score = benchmark_impl.run_benchmark(
            benchmark_name=benchmark_name,
            qpu_name=qpu_name,
            dataset_name=dataset_name,
            params_json=params,
        )

        typer.secho(
            f"\n✅ Benchmark '{benchmark_name}' complete.", fg=typer.colors.GREEN
        )
        typer.echo("--- Results ---")
        typer.echo(json.dumps(score, indent=2))

    except (KeyError, ValueError) as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(
            f"An unexpected error occurred during execution: {e}", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)


@app.command("ls")
def list_benchmarks():
    """Lists all discovered benchmarks."""
    typer.echo("Available Benchmarks:")

    benchmarks = benchmark_impl.list_available_benchmarks()

    if not benchmarks:
        typer.echo("  No benchmarks found.")
        return

    for name in benchmarks:
        typer.echo(f"- {name}")
