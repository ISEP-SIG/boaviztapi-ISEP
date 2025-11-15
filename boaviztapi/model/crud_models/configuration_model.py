from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId

from boaviztapi.model.crud_models.basemodel import BaseCRUDCollection, BaseCRUDModel, PyObjectId


class ConfigurationModel(BaseCRUDModel):
    cpu_cores: int = Field(...)
    name: str = Field(...)
    ram: int = Field(...)
    storage: int = Field(...)
    gpu: str = Field(...)
    user_id: Optional[str] = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "Development",
                "cpu_cores": 4,
                "ram": 16,
                "storage": 1000,
                "user_id": "1234567890",
                "gpu": "NVIDIA RTX A2000",
            }
        }
    )

class UpdateConfigurationModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database.
    """
    cpu_cores: Optional[int] = None
    name: Optional[str] = None
    ram: Optional[int] = None
    storage: Optional[int] = None
    gpu: Optional[str] = None
    user_id: Optional[str] = None
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "name": "Development",
                "cpu_cores": 4,
                "ram": 16,
                "storage": 1000,
                "user_id": "1234567890",
                "gpu": "NVIDIA RTX A2000",
            }
        }
    )

class ConfigurationCollection(BaseCRUDCollection[ConfigurationModel]):
    """
    A container holding a list of `ConfigurationModel` objects.
    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """