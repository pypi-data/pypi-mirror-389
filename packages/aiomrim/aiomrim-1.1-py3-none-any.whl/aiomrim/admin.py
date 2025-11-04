"""
Admin-account API Implementation
"""


import aiohttp
import asyncio
from .exceptions import APITimeoutError, APIConnectionError

async def send_announce(url: str, message: str):
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{url}/users/announce", json={"message": message}) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except asyncio.TimeoutError:
        raise APITimeoutError("Connection timed out")
    except aiohttp.ClientConnectorError as e:
        raise APIConnectionError(f"Connection error to url {url}/users/announce: {e}")
    except aiohttp.ClientResponseError as e:
        if e.status == 400:
            raise APIConnectionError(f"Bad Request for url {url}/users/announce: {e.message}. Are you sure what admin account is enabled in config.js?")
        else:
            raise APIConnectionError(f"HTTP error {e.status} for url {url}/users/announce: {e.message}")
    except aiohttp.ClientError as e:
        raise APIConnectionError(f"Client error for url {url}/users/announce: {e}")
    return None

async def send_mail_to_all(url: str, message: str):
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{url}/users/sendMailToAll", json={"message": message}) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except asyncio.TimeoutError:
        raise APITimeoutError("Connection timed out")
    except aiohttp.ClientConnectorError as e:
        raise APIConnectionError(f"Connection error to url {url}/users/sendMailToAll: {e}")
    except aiohttp.ClientResponseError as e:
        raise APIConnectionError(f"HTTP error {e.status} for url {url}/users/sendMailToAll: {e.message}")
    return None
        