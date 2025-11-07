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
from abc import ABC, abstractmethod
from enum import Enum
from typing import Union, List

from qami import QuantumProgram, QuantumProgramResult


class BackendAvailability(Enum):
    UNKNOWN_AVAILABILITY = 0
    AVAILABLE = 1
    UNAVAILABLE = 2
    MAINTENANCE = 3


class Backend(ABC):
    def __init__(self, provider, name: str, version: str, **kwargs):
        self.__provider = provider
        self.__name = name
        self.__version = version
        self.__additional_properties = kwargs

    def __enter__(self):
        self.allocate(self.__additional_properties)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.deallocate()
        return False

    def allocate(**kwargs) -> None:
        pass

    def deallocate() -> None:
        pass

    @abstractmethod
    def run(
        self, program: Union[QuantumProgram, List[QuantumProgram]], shots: int, **kwargs
    ) -> List[QuantumProgramResult]:
        pass

    @property
    def full_name(self) -> str:
        return self.__provider.get_full_name(self.name)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def version(self) -> str:
        return self.__version

    @property
    def max_qubit_count(self) -> int:
        pass

    @property
    def max_shots_per_run(self) -> int:
        pass

    @property
    def availability(self) -> BackendAvailability:
        pass
