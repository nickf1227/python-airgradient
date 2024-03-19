"""Asynchronous Python client for AirGradient."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
from typing import TYPE_CHECKING, Any, Awaitable, Callable, cast

from aiohttp import ClientSession
from aiohttp.hdrs import METH_POST
from yarl import URL

from .exceptions import (
    AirGradientConnectionError, AirGradientError
)

if TYPE_CHECKING:
    from datetime import date, datetime

    from typing_extensions import Self


VERSION = metadata.version(__package__)


@dataclass
class AirGradientClient:
    """Main class for handling connections with AirGradient."""

    host: str
    session: ClientSession | None = None
    request_timeout: int = 10
    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Handle a request to AirGradient."""
        url = URL.build(
            scheme="https",
            host=self.host,
            port=443,
        ).joinpath(uri)

        headers = {
            "User-Agent": f"PythonAirGradient/{VERSION}",
            "Accept": "application/json, text/plain, */*",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    METH_POST,
                    url,
                    headers=headers,
                    data=data,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to AirGradient"
            raise AirGradientConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")

        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected response from AirGradient"
            raise AirGradientError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return await response.text()

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The AirGradientClient object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
