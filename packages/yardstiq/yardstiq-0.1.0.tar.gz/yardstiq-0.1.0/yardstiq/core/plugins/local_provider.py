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
from typing import Dict, Type, List

from ..interfaces import (
    Backend,
    Benchmark,
    Dataset,
    BackendProvider,
    BenchmarkProvider,
    DatasetProvider,
)


class LocalProvider(BackendProvider, BenchmarkProvider, DatasetProvider):
    """
    A built-in singleton provider that holds all implementations
    loaded from local files (via --load or pyproject.toml).
    """

    def __init__(self):
        super().__init__(name="local")

        # Internal registries for locally-defined classes
        self.__backends: Dict[str, Type[Backend]] = {}
        self.__benchmarks: Dict[str, Type[Benchmark]] = {}
        self.__datasets: Dict[str, Type[Dataset]] = {}

    def add_backend(self, backend: Backend, name: str):
        self.__backends[name] = backend

    def list_backends(self) -> List[Backend]:
        return list(self.__backends.keys())

    def get_backend(self, name: str) -> Backend:
        try:
            return self.__backends[name]
        except KeyError:
            raise KeyError(f"Local backend '{name}' not found.")

    def add_benchmark(self, benchmark: Benchmark, name: str):
        self.__benchmarks[name] = benchmark

    def list_benchmarks(self) -> List[Benchmark]:
        return list(self.__benchmarks.keys())

    def get_benchmark(self, name: str) -> Benchmark:
        try:
            return self.__benchmarks[name]
        except KeyError:
            raise KeyError(f"Local benchmark '{name}' not found.")

    def add_dataset(self, dataset: Dataset, name: str):
        self.__datasets[name] = dataset

    def list_datasets(self) -> List[Dataset]:
        return list(self.__datasets.keys())

    def get_dataset(self, name: str) -> Dataset:
        try:
            return self.__datasets[name]
        except KeyError:
            raise KeyError(f"Local dataset '{name}' not found.")
