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
from importlib.metadata import entry_points

PLUGIN_ENTRY_POINT_GROUP = "yardstiq.plugins"


def load_installed_plugins():
    """
    Discovers and loads all installed plugins via entry points.
    The decorators (@provider) in the loaded files will register themselves.
    """
    print("[Yardstiq] Loading installed plugins (entry_points)...")

    try:
        discovered_entry_points = entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
    except Exception as e:
        print(f"[Yardstiq] Error reading entry points: {e}")
        return

    for ep in discovered_entry_points:
        try:
            # ep.load() simply imports the module, triggering its decorators
            plugin_module = ep.load()
            print(f"[Yardstiq] Installed plugin '{ep.name}' loaded.")
        except Exception as e:
            print(f"[Yardstiq] WARNING: Failed to load plugin '{ep.name}': {e}")
