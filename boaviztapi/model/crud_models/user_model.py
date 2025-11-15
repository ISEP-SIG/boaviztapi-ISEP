from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import Field, ConfigDict

from boaviztapi.model.crud_models.basemodel import BaseCRUDModel, BaseCRUDUpdateModel, BaseCRUDCollection


class UserModel(BaseCRUDModel):
    email: str = Field(...)
    email_verified: bool = Field(...)
    name: str = Field(...)
    picture: str = Field(...)
    given_name: str = Field(...)
    family_name: str = Field(...)
    sub: str = Field(...)
    registration_date: datetime = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "email": "johndoe@mail.com",
                "email_verified": True,
                "name": "John Doe",
                "picture": "https://example.com/user.png",
                "given_name": "John",
                "family_name": "Doe",
                "sub": "1234567890",
                "registration_date": "2023-01-01T00:00:00.000Z"
            }
        }
    )


class UpdateUserModel(BaseCRUDUpdateModel):
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    sub: Optional[str] = None
    registration_date: Optional[datetime] = None
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "email": "johndoe@mail.com",
                "email_verified": True,
                "name": "John Doe",
                "picture": "https://example.com/user.png",
                "given_name": "John",
                "family_name": "Doe",
                "sub": "1234567890",
                "registration_date": "2023-01-01T00:00:00.000Z"
            }
        }
    )

class UserCollection(BaseCRUDCollection[UserModel]):
    """
    A container holding a list of `UserModel` objects.
    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """