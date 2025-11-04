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
import toml

from pathlib import Path

from .local_manual_plugins import load_local_plugin


def find_config_file() -> Path | None:
    current_dir = Path.cwd()

    for parent in [current_dir] + list(current_dir.parents):
        config_path = parent / "pyproject.toml"
        if config_path.exists():
            return config_path

    return None


def load_project_plugins():
    """
    Loads local plugins declared in a pyproject.toml [tool.yardstiq] section.
    """
    config_file = find_config_file()
    if not config_file:
        return

    try:
        config = toml.load(config_file)
        plugin_paths = (
            config.get("tool", {}).get("yardstiq", {}).get("local_plugins", [])
        )

        if not plugin_paths:
            return

        print(f"[Yardstiq] Loading project plugins from {config_file.name}...")
        base_dir = config_file.parent

        for rel_path_str in plugin_paths:
            abs_path = base_dir / rel_path_str
            load_local_plugin(abs_path)

    except Exception as e:
        print(f"[Yardstiq] WARNING: Failed to load from pyproject.toml: {e}")
