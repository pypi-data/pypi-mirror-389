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
import keyring
import typer

_SERVICE_NAME = "yardstiq"


def set_token(provider_name: str, token: str):
    try:
        keyring.set_password(_SERVICE_NAME, provider_name, token)
        typer.secho(f"Token for '{provider_name}' registered.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Keyring error: {e}", fg=typer.colors.RED)


def get_token(provider_name: str) -> str | None:
    try:
        return keyring.get_password(_SERVICE_NAME, provider_name)
    except Exception as e:
        typer.secho(f"Keyring error: {e}", fg=typer.colors.RED)
        return None


def delete_token(provider_name: str):
    try:
        keyring.delete_password(_SERVICE_NAME, provider_name)
        typer.secho(f"Token for '{provider_name}' removed.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Keyring error: {e}", fg=typer.colors.RED)
