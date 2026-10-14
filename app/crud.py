from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Price
from app.schemas import PriceCreate

async def create_price(session: AsyncSession, price: PriceCreate) -> Price:
    db_price = Price(**price.model_dump())
    session.add(db_price)
    await session.commit()
    await session.refresh(db_price)
    return db_price

async def get_prices_by_ticker(session: AsyncSession, ticker: str):
    stmt = (
        select(Price)
        .where(Price.ticker == ticker)
        .order_by(desc(Price.timestamp))
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_latest_price(session: AsyncSession, ticker: str):
    stmt = (
        select(Price)
        .where(Price.ticker == ticker)
        .order_by(desc(Price.timestamp))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_prices_by_date_range(
    session: AsyncSession, ticker: str, start: int, end: int
):
    stmt = (
        select(Price)
        .where(
            Price.ticker == ticker,
            Price.timestamp >= start,
            Price.timestamp <= end,
        )
        .order_by(desc(Price.timestamp))
    )
    result = await session.execute(stmt)
    return result.scalars().all()