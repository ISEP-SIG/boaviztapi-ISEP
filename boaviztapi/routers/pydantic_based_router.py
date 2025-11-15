from typing import Any, Mapping, TypeVar, Generic, Type

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Body, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection

from boaviztapi.application_context import get_app_context
from boaviztapi.model.crud_models.basemodel import BaseCRUDCollection

TModel = TypeVar("TModel", bound=BaseModel)

max_count = 1000

def validate_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

class GenericPydanticCRUDService(Generic[TModel]):
    def __init__(
            self,
            model_class: Type[TModel],
            collection_class: Type[BaseCRUDCollection[TModel]],
            mongo_collection: AsyncCollection[Mapping[str, Any] | Any],
            collection_name: str
    ):
        self.model_class = model_class
        self.collection_class = collection_class
        self.mongo_collection = mongo_collection
        self.collection_name = collection_name
        self.app_context = get_app_context()

    async def create(self, item: TModel = Body(...)):
        """
        List all the record collection data in the database.
        The response is unpaginated and limited to 1000 results.
        """
        new_item = item.model_dump(by_alias=True, exclude={"id"})
        result = await self.mongo_collection.insert_one(new_item)
        new_item["_id"] = result.inserted_id

        return new_item

    async def get_all(self) -> BaseCRUDCollection[TModel]:
        return self.collection_class(items = await self.mongo_collection.find().to_list(max_count))

    async def get_by_id(self, id: str) -> TModel:
        """
        Get the record for a specific `id`.
        """
        if (
            item := await self.mongo_collection.find_one({"_id": ObjectId(id)})
        ) is not None:
            return item

        raise HTTPException(status_code=404, detail=f"Item from collection '{self.collection_name}' with id={id} was not found")

    async def update(self, id: str, item: TModel = Body(...)) -> TModel:
        """
        Update individual fields of an existing record.

        Only the provided fields will be updated.
        Any missing or `null` fields will be ignored.
        """
        item = {
            k: v for k, v in item.model_dump(by_alias=True).items() if v is not None
        }

        if len(item) >= 1:
            update_result = await self.mongo_collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": item},
                return_document=ReturnDocument.AFTER,
            )
            if update_result is not None:
                return update_result
            else:
                raise HTTPException(status_code=404, detail=f"Item from collection '{self.collection_name}' with id={id} was not found")

        # The update is empty, but we should still return the matching document:
        if (existing_configuration := await self.mongo_collection.find_one({"_id": ObjectId(id)})) is not None:
            return existing_configuration

        raise HTTPException(status_code=404, detail=f"Item from collection '{self.collection_name}' with id={id} was not found")

    async def delete(self, id: str) -> Response:
        """
        Remove a single record from the database.
        """
        delete_result = await self.mongo_collection.delete_one({"_id": ObjectId(id)})

        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(status_code=404, detail=f"Item from collection '{self.collection_name}' with id={id} was not found")
