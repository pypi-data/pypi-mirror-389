"""
check server stability
"""

import aiohttp
import asyncio
from .exceptions import APITimeoutError, APIConnectionError

async def check_connection(url: str):
    
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.head(f'{url}/heartbeat') as response:
                response.raise_for_status()
    except asyncio.TimeoutError:
        raise APITimeoutError("Connection timed out")
    except aiohttp.ClientConnectorError as e:
        raise APIConnectionError(f"Connection error to url {url}/: {e}")
    except aiohttp.ClientResponseError as e:
        raise APIConnectionError(f"HTTP error {e.status} for url {url}/: {e.message}")
    except aiohttp.ClientError as e:
        raise APIConnectionError(f"Client error for url {url}/: {e}")
    return True