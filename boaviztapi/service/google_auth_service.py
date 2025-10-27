from google.auth.exceptions import GoogleAuthError
from google.oauth2.id_token import verify_oauth2_token
from google.auth.transport import requests

from boaviztapi.application_context import get_app_context
from boaviztapi.dto.auth.google_dto import GoogleJwtPayload
from boaviztapi.service.base import BaseService


class GoogleAuthService(BaseService):

    _base_url = "https://www.googleapis.com/oauth2"
    jwk_url = f"{_base_url}/v3/certs"
    pem_url = f"{_base_url}/v1/certs"

    @staticmethod
    def _get_client_credentials():
        ctx = get_app_context()
        _client_id = ctx.GOOGLE_CLIENT_ID
        _client_secret = ctx.GOOGLE_CLIENT_SECRET
        if not _client_id or not _client_secret:
            raise ValueError("No Google client ID or secret found!")
        return _client_id, _client_secret

    @staticmethod
    def verify_jwt(token: str) -> GoogleJwtPayload:
        _client_id, _ = GoogleAuthService._get_client_credentials()
        try:
            decoded_token = verify_oauth2_token(id_token = token,
                                                request = requests.Request(),
                                                audience = _client_id)
        except GoogleAuthError:
            raise ValueError("The issuer of the token is invalid or expired.")
        return GoogleJwtPayload(**decoded_token)