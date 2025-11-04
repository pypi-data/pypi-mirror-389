"""
(GET) /users/online method implementation.
"""

import aiohttp
import asyncio
from .exceptions import APITimeoutError, APIConnectionError

async def get_online(url: str):
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{url}/users/online") as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except asyncio.TimeoutError:
        raise APITimeoutError("Connection timed out")
    except aiohttp.ClientConnectorError as e:
        raise APIConnectionError(f"Connection error to url {url}/users/online: {e}")
    except aiohttp.ClientResponseError as e:
        raise APIConnectionError(f"HTTP error {e.status} for url {url}/users/online: {e.message}")
    except aiohttp.ClientError as e:
        raise APIConnectionError(f"Client error for url {url}/users/online: {e}")
    return None

async def get_raw_online(url: str):
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{url}/users/rawOnline") as response:
                response.raise_for_status()
                data = await response.text()
                return data
    except asyncio.TimeoutError:
        raise APITimeoutError("Connection timed out")
    except aiohttp.ClientConnectorError as e:
        raise APIConnectionError(f"Connection error to url {url}/users/rawOnline: {e}")
    except aiohttp.ClientResponseError as e:
        raise APIConnectionError(f"HTTP error {e.status} for url {url}/users/rawOnline: {e.message}")
    except aiohttp.ClientError as e:
        raise APIConnectionError(f"Client error for url {url}/users/rawOnline: {e}")
    return None