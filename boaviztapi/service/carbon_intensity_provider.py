import requests

from boaviztapi.application_context import get_app_context
from boaviztapi.service.base import BaseService
from boaviztapi.service.exceptions import APIAuthenticationError, APIError

class CarbonIntensityProvider(BaseService):
    @staticmethod
    def _get_api_key():
        ctx = get_app_context()
        api_token = ctx.ELECTRICITYMAPS_API_KEY
        if not api_token:
            raise APIAuthenticationError("No ElectricityMaps API key found!")
        return api_token

    @staticmethod
    def _perform_request(url: str):
        api_token = CarbonIntensityProvider._get_api_key()
        r = requests.get(url, headers={"auth-token": api_token})
        if r.status_code == 401:
            raise APIAuthenticationError("The API key is not authorized to access this resource")
        if r.status_code != 200:
            raise APIError("Could not reach the ElectricityMaps API. Please try again later or contact system administrator")
        return r.json()

    @staticmethod
    def get_carbon_intensity(zone: str, temporalGranularity: str = 'hourly'):
        url = f"https://api.electricitymaps.com/v3/carbon-intensity/latest?zone={zone}&temporalGranularity={temporalGranularity}"
        return CarbonIntensityProvider._perform_request(url)

    @staticmethod
    def get_power_breakdown(zone: str, temporalGranularity: str = 'hourly'):
        url = f"https://api.electricitymaps.com/v3/power-breakdown/latest?zone={zone}&temporalGranularity={temporalGranularity}"
        return CarbonIntensityProvider._perform_request(url)