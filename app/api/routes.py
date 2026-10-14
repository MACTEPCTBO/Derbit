from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_session
from app import crud, schemas

router = APIRouter()

@router.get("/prices", response_model=List[schemas.PriceResponse])
async def get_all_prices(
    ticker: str = Query(..., description="Ticker symbol: BTC or ETH"),
    session: AsyncSession = Depends(get_session),
):
    return await crud.get_prices_by_ticker(session, ticker)

@router.get("/prices/latest", response_model=schemas.PriceResponse)
async def get_latest_price(
    ticker: str = Query(..., description="Ticker symbol: BTC or ETH"),
    session: AsyncSession = Depends(get_session),
):
    price = await crud.get_latest_price(session, ticker)
    if not price:
        raise HTTPException(status_code=404, detail="Price not found")
    return price

@router.get("/prices/filter", response_model=List[schemas.PriceResponse])
async def get_prices_by_date(
    ticker: str = Query(..., description="Ticker symbol: BTC or ETH"),
    start: int = Query(..., description="Start UNIX timestamp"),
    end: int = Query(..., description="End UNIX timestamp"),
    session: AsyncSession = Depends(get_session),
):
    return await crud.get_prices_by_date_range(session, ticker, start, end)