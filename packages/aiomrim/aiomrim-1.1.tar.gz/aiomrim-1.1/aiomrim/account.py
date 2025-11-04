"""
'/users/register/' API implementation. Also for other methods for accounts in MRIM-Server (Renaissance)
More about that: https://github.com/fayzetwin1/aiomrim/blob/main/docs/docs.md 
"""

from .exceptions import APITimeoutError, APIConnectionError
import aiohttp
import asyncio
    
async def register_account(url: str,login: str,password:str,nickname:str,first_name:str,sex:int,
last_name = None, location = None, birthday = None, status = None):
    timeout = aiohttp.ClientTimeout(total=5)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.put(f"{url}/users/register", json=
            {
                "login": login, "passwd": password, "nick": nickname, 
                "f_name": first_name, "sex": sex, "l_name": last_name, "location": location, 
                "birthday": birthday, "status": status}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except asyncio.TimeoutError:
        raise APITimeoutError("Connection timed out")
    except aiohttp.ClientConnectorError as e:
        raise APIConnectionError(f"Connection error to url {url}/users/register: {e}")
    except aiohttp.ClientResponseError as e:
        if e.status == 400:
            raise APIConnectionError(f"400 code error for url {url}/users/register: {e.message}. Are you sure what all necessary fields are filled? Or, maybe that login already registered?")
        else:
            raise APIConnectionError(f"HTTP Error with {e.status} code for url {url}/users/register: {e.message}")
    except aiohttp.ClientError as e:
        raise APIConnectionError(f"Client error for url {url}/users/register: {e}")
    return None
    