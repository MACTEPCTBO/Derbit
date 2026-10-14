import aiohttp
from app.config import Settings

class DeribitClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def get_index_price(self, index_name: str) -> float:
        url = f"{self.base_url}/public/get_index_price"
        params = {"index_name": index_name}
        async with self._session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return float(data["result"]["index_price"])

    async def get_btc_usd_price(self) -> float:
        return await self.get_index_price("btc_usd")

    async def get_eth_usd_price(self) -> float:
        return await self.get_index_price("eth_usd")