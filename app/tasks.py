import asyncio
import time
from celery import Celery
from app.config import Settings
from app.database import async_session
from app.crud import create_price
from app.schemas import PriceCreate
from app.services.deribit_client import DeribitClient

settings = Settings()
celery_app = Celery(
    "tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

async def _fetch_and_save():
    async with DeribitClient(settings.deribit_base_url) as client:
        btc_price = await client.get_btc_usd_price()
        eth_price = await client.get_eth_usd_price()

    timestamp = int(time.time())
    async with async_session() as session:
        await create_price(
            session, PriceCreate(ticker="BTC", price=btc_price, timestamp=timestamp)
        )
        await create_price(
            session, PriceCreate(ticker="ETH", price=eth_price, timestamp=timestamp)
        )

@celery_app.task
def fetch_prices():
    asyncio.run(_fetch_and_save())

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, fetch_prices.s(), name="fetch every minute")