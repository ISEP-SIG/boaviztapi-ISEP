from boaviztapi.dto import BaseDTO

class GoogleJwtPayload(BaseDTO):
    iss: str = None
    azp: str = None
    aud: str = None
    sub: str = None
    email: str = None
    email_verified: bool = None
    nonce: str = None
    nbf: int = None
    name: str = None
    picture: str = None
    given_name: str = None
    family_name: str = None
    iat: int = None
    exp: int = None
    jti: str = None

