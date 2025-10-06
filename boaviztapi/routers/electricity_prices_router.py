from typing import Annotated

import numpy as np
from fastapi import APIRouter, Query, HTTPException
from fastapi_cache.decorator import cache
from numpy import mean

from boaviztapi import factors, data_dir
from boaviztapi.service.costs_provider import get_eic_countries, get_price_for_country

electricity_prices_router = APIRouter(
    prefix='/v1/electricity',
    tags=['electricity'],
)


@cache(expire=60 * 60 * 24)
@electricity_prices_router.get('/available_countries', description="")
async def get_available_countries():
    return get_eic_countries()


@electricity_prices_router.get('/price', description="")
@cache(expire=3600)
async def get_electricity_price(
        iso3_country: Annotated[str | None, Query(example=factors["electricity"]["available_countries"])] = None):
    if iso3_country is None:
        raise HTTPException(status_code=400, detail="iso3_country cannot be empty!")
    if iso3_country not in [c["ISO3 Code"] for c in get_eic_countries()]:
        raise HTTPException(status_code=400, detail="iso3_country is not valid!")

    result = get_price_for_country(iso3_country)
    if not result:
        raise HTTPException(status_code=404, detail=f"{iso3_country} not found")
    if "Acknowledgement_MarketDocument" in result:
        # error case
        error_msg = result["Acknowledgement_MarketDocument"]["Reason"]["text"]
        raise HTTPException(status_code=404, detail=f"{error_msg} not found")
    values = result["Publication_MarketDocument"]["TimeSeries"][0]["Period"]["Point"]
    avg_price = ([float(record["price.amount"]) for record in values])
    return sum(avg_price) / len(avg_price)
