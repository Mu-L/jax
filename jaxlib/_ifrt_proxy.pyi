# Copyright 2024 The JAX Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from collections.abc import Callable
from typing import Any

from jaxlib import _jax

_Status = Any
Client = _jax.Client

class ClientConnectionOptions:
  on_disconnect: Callable[[_Status], None] | None = None
  on_connection_update: Callable[[str], None] | None = None
  connection_timeout_in_seconds: int | None = None

def get_client(
    proxy_server_address: str, options: ClientConnectionOptions
) -> Client: ...
