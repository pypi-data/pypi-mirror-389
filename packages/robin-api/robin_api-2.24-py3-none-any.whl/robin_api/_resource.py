# File generated from our OpenAPI spec by Stainless.

from __future__ import annotations

import time
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._client import RobinAIClient


class SyncAPIResource:
    _client: RobinAIClient

    def __init__(self, client: RobinAIClient) -> None:
        self._client = client
        self._stream = client.stream
        self._post = client.post
        self._get= client.get
        self._post_form = client.post_form

    def _sleep(self, seconds: float) -> None:
        time.sleep(seconds)

#TODO
class AsyncAPIResource:
    _client: AsyncRobinAIClient

    def __init__(self, client: AsyncRobinAIClient) -> None:
        self._client = client
        self._get = client.get
        self._post = client.post
        self._patch = client.patch
        self._put = client.put
        self._delete = client.delete
        self._get_api_list = client.get_api_list

    async def _sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
