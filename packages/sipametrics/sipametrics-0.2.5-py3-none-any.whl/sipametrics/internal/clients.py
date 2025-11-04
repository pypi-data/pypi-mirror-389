import asyncio
import aiohttp
import logging
import sipametrics.constants as CONSTANTS
import sipametrics.internal.endpoints as endpoints


class BaseClient:
    def __init__(self, api_key: str, api_secret: str):
        self._session = aiohttp.ClientSession()
        self._api_key = api_key
        self._api_secret = api_secret

    async def close(self):
        await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, tb):
        await self._session.close()

    async def _get(self, path, **kwargs):
        return await self._request("GET", path, **kwargs)

    async def _post(self, path, **kwargs) -> dict:
        return await self._request("POST", path, **kwargs)

    def _generate_authorization_headers(self, method) -> dict:
        if method == "GET":
            return {
                "X-API-KEY": self._api_key,
                "X-API-SECRET": self._api_secret,
                "X-Source": f"{endpoints.SOURCE}",
                "X-Version": f"{endpoints.VERSION}"
            }
        elif method == "POST":
            return {
                "X-API-KEY": self._api_key,
                "X-API-SECRET": self._api_secret,
                "X-Source": f"{endpoints.SOURCE}",
                "X-Version": f"{endpoints.VERSION}",
                "Content-Type": "application/json",
            }
        else:
            return {}

    async def _request(self, method: str, uri: str, **kwargs) -> dict:
        headers = {}

        if method in ["POST", "GET"]:
            headers.update(self._generate_authorization_headers(method))

        logging.debug(f"{CONSTANTS.IDENTIFIER}: {method}; {uri}; {kwargs}")

        query_params = kwargs.pop("params", None)

        async with getattr(self._session, method.lower())(
            uri,
            params=query_params,
            headers=headers,
            json=kwargs.get("data"),
        ) as response:
            return await self._handle_response(response)

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict:
        """
        Handles retries for transient errors and processes API responses.
        """
        retries = 3
        delay = 2
        for _ in range(retries):
            if response.status == 200:
                try:
                    return await response.json()
                except aiohttp.ContentTypeError as e:
                    raise ValueError("Invalid JSON response") from e
            elif response.status in [500, 502, 503, 504]:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                response.raise_for_status()

        raise Exception(f"Failed to process response after {retries} retries. Status: {response.status}")
