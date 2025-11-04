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
from typing import Dict, Any, Optional, Tuple, List

from ..interfaces import (
    Backend,
    Benchmark,
    Dataset,
    BackendProvider,
    DatasetProvider,
    BenchmarkProvider,
)

from ..plugins import PROVIDER_REGISTRY


def _parse_full_name(full_name: str) -> Tuple[str, str]:
    if "/" not in full_name:
        raise ValueError(
            f"Invalid name format: '{full_name}'. Expected 'provider/resource'."
        )

    provider_name, resource_name = full_name.split("/", 1)

    return provider_name, resource_name


def _get_backend(name: str) -> Backend:
    provider_name, backend_name = _parse_full_name(name)
    provider_instance = PROVIDER_REGISTRY.get(provider_name)

    if not provider_instance:
        raise KeyError(f"Backend provider not found: '{provider_name}'")

    if not isinstance(provider_instance, BackendProvider):
        raise TypeError(f"Provider '{provider_name}' is not a BackendProvider.")

    return provider_instance.get_backend(backend_name)


def _get_dataset(name: str) -> Dataset:
    provider_name, dataset_name = _parse_full_name(name)
    provider_instance = PROVIDER_REGISTRY.get(provider_name)

    if not provider_instance:
        raise KeyError(f"Dataset provider not found: '{provider_name}'")

    if not isinstance(provider_instance, DatasetProvider):
        raise TypeError(f"Provider '{provider_name}' is not a DatasetProvider.")

    return provider_instance.get_dataset(dataset_name)


def _get_benchmark(name: str) -> Benchmark:
    provider_name, benchmark_name = _parse_full_name(name)
    provider_instance = PROVIDER_REGISTRY.get(provider_name)

    if not provider_instance:
        raise KeyError(f"Benchmark provider not found: '{provider_name}'")

    if not isinstance(provider_instance, BenchmarkProvider):
        raise TypeError(f"Provider '{provider_name}' is not a BenchmarkProvider.")

    return provider_instance.get_benchmark(benchmark_name)


def list_available_benchmarks() -> List[Benchmark]:
    benchmarks = []

    for name, provider in PROVIDER_REGISTRY.items():
        if isinstance(provider, BenchmarkProvider):
            try:
                for ds_name in provider.list_benchmarks():
                    benchmarks.append(provider.get_full_name(ds_name))
            except Exception as e:
                print(
                    f"[Yardstiq] WARNING: Provider '{name}' failed to list benchmarks: {e}"
                )

    return benchmarks


def run_benchmark(
    benchmark_name: str,
    backend_name: str,
    dataset_name: Optional[str],
    **kwargs,
) -> Dict[str, Any]:
    """
    Core implementation for running a benchmark.
    This function resolves components dynamically using providers.
    """

    # try:
    #     config = json.loads(params_json)
    # except json.JSONDecodeError:
    #     raise ValueError(f"Invalid JSON parameters: {params_json}")

    benchmark = _get_benchmark(benchmark_name)
    backend = _get_backend(backend_name)

    if dataset_name:
        dataset = _get_dataset(dataset_name)
        dataset.load(kwargs)

    model = benchmark.build_model(dataset=dataset)
    results = backend.run(model=model, shots=kwargs.get("shots", 1024))
    score = benchmark.score(results)

    return score
