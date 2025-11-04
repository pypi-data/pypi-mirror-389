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
from typing import List

from ..interfaces import BackendProvider, Backend
from ..plugins import PROVIDER_REGISTRY


def list_available_backends() -> List[Backend]:
    """Returns a list of all discoverable QPU names."""
    backends = []

    for name, provider in PROVIDER_REGISTRY.items():
        if isinstance(provider, BackendProvider):
            try:
                for qpu_name in provider.list_backends():
                    backends.append(provider.get_full_name(qpu_name))
            except Exception as e:
                print(
                    f"[Yardstiq] WARNING: Provider '{name}' failed to list backends: {e}"
                )

    return backends
