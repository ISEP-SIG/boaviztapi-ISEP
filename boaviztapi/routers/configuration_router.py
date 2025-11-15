from typing import Any, Mapping

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.params import Depends
from pymongo.asynchronous.collection import AsyncCollection

from boaviztapi.application_context import get_app_context
from boaviztapi.model.crud_models.configuration_model import ConfigurationModel, ConfigurationCollection
from boaviztapi.routers.pydantic_based_router import GenericPydanticCRUDService, validate_id

configuration_router = APIRouter(
    prefix='/v1/configurations',
    tags=['configuration']
)

@configuration_router.post("/",
                           response_description="Add a new configuration",
                           response_model=ConfigurationModel,
                           status_code=status.HTTP_201_CREATED,
                           response_model_by_alias=False,
                           )
async def create_configuration(configuration: ConfigurationModel = Body(...)):
    """
    Insert a new configuration record.

    A unique `id` will be created and provided in the response.
    """
    service = get_crud_service()
    return await service.create(configuration)


@configuration_router.get("/",
                          response_description="List all configurations",
                          response_model=ConfigurationCollection,
                          response_model_by_alias=False,
                          )
async def list_configurations():
    service = get_crud_service()
    return await service.get_all()

@configuration_router.get("/{id}",
                          response_description="Get a single configuration",
                          response_model=ConfigurationModel,
                          response_model_by_alias=False,
                          )
async def find_configuration(id: str = Depends(validate_id)):
    service = get_crud_service()
    return await service.get_by_id(id)


@configuration_router.put(
    "/{id}",
    response_description="Update a configuration",
    response_model=ConfigurationModel,
    response_model_by_alias=False,
)
async def update_configuration(id: str = Depends(validate_id), configuration: ConfigurationModel = Body(...)):
    service = get_crud_service()
    return await service.update(id, configuration)


@configuration_router.delete("/{id}", response_description="Delete a configuration")
async def delete_configuration(id: str = Depends(validate_id)):
    service = get_crud_service()
    return await service.delete(id)

def get_configuration_collection() -> AsyncCollection[Mapping[str, Any] | Any]:
    ctx = get_app_context()
    if ctx.mongodb_client is None:
        raise HTTPException(status_code=503, detail="MongoDB is not available!")

    db = ctx.mongodb_client.get_database(name="development")
    return db.get_collection(name="configurations")

def get_crud_service() -> GenericPydanticCRUDService[ConfigurationModel]:
    return GenericPydanticCRUDService(
        model_class=ConfigurationModel,
        collection_class=ConfigurationCollection,
        mongo_collection=get_configuration_collection(),
        collection_name="configurations"
    )
