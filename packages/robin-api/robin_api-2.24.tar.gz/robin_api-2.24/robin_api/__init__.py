import os as _os
from typing_extensions import override
import httpx
from . import types
#from ._types import NoneType, Transport, ProxiesTypes
from ._client import (
    Client,
    RobinAIClient,
    Stream,
)

__all__ = [
    "types",
    "__version__",
    "__title__",
    "Client"
    "RobinAIClient",
    "Stream",

]

from ._client import DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES

import typing as _t

api_key: str | None = None

organization: str | None = None

base_url: str | None = None

timeout: float  | None = DEFAULT_TIMEOUT

max_retries: int = DEFAULT_MAX_RETRIES

default_headers: _t.Mapping[str, str] | None = None

default_query: _t.Mapping[str, object] | None = None

http_client: httpx.Client | None = None


_client: RobinAIClient | None = None

