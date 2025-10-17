from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi_cache.decorator import cache
from pydantic import AfterValidator

from boaviztapi.dto.electricity.electricity import Country
from boaviztapi.routers.openapi_doc.descriptions import electricity_available_countries, electricity_price, \
    carbon_intensity, power_breakdown
from boaviztapi.routers.openapi_doc.examples import electricity_carbon_intensity, electricity_power_breakdown
from boaviztapi.service.carbon_intensity_provider import CarbonIntensityProvider
from boaviztapi.service.costs_provider import ElectricityCostsProvider
from boaviztapi.service.exceptions import APIMissingValueError, APIError, APIAuthenticationError
from boaviztapi.utils.validators import check_alpha3_in_electricity_prices, check_zone_code_in_electricity_maps

electricity_prices_router = APIRouter(
    prefix='/v1/electricity',
    tags=['electricity'],
)


@electricity_prices_router.get('/available_countries', description=electricity_available_countries,
                               response_model=list[Country])
@cache(expire=60 * 60 * 24)  # 1 day
async def get_available_countries():
    return ElectricityCostsProvider.get_eic_countries()


@electricity_prices_router.get('/price', description=electricity_price, response_model=float)
@cache(expire=3600)
async def get_electricity_price(
        alpha3: Annotated[str, AfterValidator(check_alpha3_in_electricity_prices)] = Query(
            description="ISO 3166-1 alpha-3 country code",
            default="FRA"
        )):
    try:
        return ElectricityCostsProvider.get_average_price_for_country(alpha3)
    except APIMissingValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@electricity_prices_router.get('/carbon_intensity', description=carbon_intensity,
                               responses={200: {
                                   "description": "Successful Response",
                                   "content": {"application/json": {"example": electricity_carbon_intensity}}
                               }})
@cache(expire=3600)
async def get_carbon_intensity(zone: Annotated[str, AfterValidator(check_zone_code_in_electricity_maps)] = Query(
    description="Zone code as defined in the ElectricityMaps API",
    default="AT"
),
        temporalGranularity: str = Query(examples=["5_minutes", "15_minutes", "hourly"], default="hourly")):
    try:
        return CarbonIntensityProvider.get_carbon_intensity(zone, temporalGranularity)
    except APIAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@electricity_prices_router.get('/power_breakdown', description=power_breakdown,
                               responses={200: {
                                   "description": "Successful Response",
                                   "content": {"application/json": {"example": electricity_power_breakdown}}
                               }})
@cache(expire=3600)
async def get_power_breakdown(zone: Annotated[str, AfterValidator(check_zone_code_in_electricity_maps)] = Query(
    description="Zone code as defined in the ElectricityMaps API",
    default="AT"
),
        temporalGranularity: str = Query(examples=["5_minutes", "15_minutes", "hourly"], default="hourly")):
    try:
        return CarbonIntensityProvider.get_power_breakdown(zone, temporalGranularity)
    except APIAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
