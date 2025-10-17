import logging
import os
from datetime import datetime, timezone, timedelta

import pandas as pd
import requests
import xmltodict

from boaviztapi import data_dir
from boaviztapi.application_context import get_app_context
from boaviztapi.dto.electricity.electricity import Country
from boaviztapi.service.base import BaseService
from boaviztapi.service.exceptions import APIError, APIAuthenticationError, APIMissingValueError, \
    APIResponseParsingError

_logger = logging.getLogger(__name__)

df = pd.read_csv(os.path.join(data_dir, 'electricity/electricity_zones.csv'))
df.fillna(value='', inplace=True)

class ElectricityCostsProvider(BaseService):
    """
    Provides functionality to retrieve and process electricity-costs-related data from one or more external APIs.
    """
    @staticmethod
    def get_eic_countries() -> list[Country]:
        """
        Get the list of EIC codes and their countries and return it as a dict
        """
        records = df.to_dict(orient='records')
        return [Country(**record) for record in records]

    @staticmethod
    def get_EIC_for_country(iso3_country: str) -> str:
        """
        Get the EIC code for a country.
        """
        return df.query(f"alpha_3 == '{iso3_country}' ")["EIC_code"].iloc[0]

    @staticmethod
    def get_price_for_country(alpha3: str) -> dict | None:
        """
        Get a timeseries of electricity prices for a country. The default granularity is hourly.

        Args:
            alpha3: ISO 3166-1 alpha-3 country code

        Returns:
            An XML response from the ENTSO-E API, converted to a Python dictionary

        Raises:
            APIAuthenticationError: When no ENTSOE API key is found in the application context
            APIError: When the API returns an unexpected response status code
        """
        ctx = get_app_context()
        security_token = ctx.ENTSOE_API_KEY
        eic_code = ElectricityCostsProvider.get_EIC_for_country(alpha3)
        if not security_token:
            raise APIAuthenticationError("No ENTSOE API key found!")

        periodStart = datetime.now(timezone.utc).replace(hour=0, minute=0)
        periodEnd = periodStart + timedelta(days=1)

        periodStart = periodStart.strftime("%Y%m%d%H%M")  # YYYYMMDDHHMM e.g. 202509061200
        periodEnd = periodEnd.strftime("%Y%m%d%H%M")

        url = (f"https://web-api.tp.entsoe.eu/api?documentType=A44&periodStart={periodStart}&periodEnd={periodEnd}"
               f"&out_Domain={eic_code}&in_Domain={eic_code}&securityToken={security_token}")
        r = requests.get(url)
        if r.status_code != 200:
            raise APIError("An error occurred while retrieving the price data from ENTSOE")

        return xmltodict.parse(r.content)

    @staticmethod
    def get_average_price_for_country(alpha3: str) -> float:
        """
        Get average electricity price for a country.
        
        Args:
            alpha3: ISO 3166-1 alpha-3 country code
            
        Returns:
            Average electricity price as float
            
        Raises:
            APIError: When API is unreachable
            APIResponseParsingError: When the API response cannot be parsed
            APIMissingValueError: When no price data is available for the country
        """
        result = ElectricityCostsProvider.get_price_for_country(alpha3)

        if not result:
            raise APIError(
                "Could not reach the ENTSO-E API. Please try again later or contact system administrator"
            )

        # Check for API error response
        if "Acknowledgement_MarketDocument" in result:
            try:
                error_msg = result["Acknowledgement_MarketDocument"]["Reason"]["text"]
                raise APIError(f"{error_msg} not found")
            except KeyError:
                raise APIResponseParsingError("Unexpected error response format from the API")

        # Extract and calculate average price
        try:
            timeseries = result["Publication_MarketDocument"]["TimeSeries"]

            # Normalize timeseries to dict if it's a list
            if isinstance(timeseries, list):
                if not timeseries or len(timeseries) == 0:
                    raise APIMissingValueError(
                        f"No electricity prices found for {alpha3}"
                    )
                timeseries = timeseries[0]

            values = timeseries["Period"]["Point"]
            if not values:
                raise APIMissingValueError(
                    f"No electricity prices found for {alpha3}"
                )

            prices = [float(record["price.amount"]) for record in values]
            if not prices:
                raise APIMissingValueError(
                    f"No electricity prices found for {alpha3}"
                )

            return sum(prices) / len(prices)

        except KeyError as e:
            raise APIResponseParsingError("Unexpected error response format from the API") from e
        except (ValueError, TypeError) as e:
            raise APIResponseParsingError("Error parsing price data") from e
