from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY

from architectonics.models.abstract_base_model import AbstractBaseModel
from architectonics.repositories.exceptions import (
    ForeignKeyViolationRepositoryException,
    IntegrityErrorRepositoryException,
    ObjectAlreadyExistsRepositoryException,
    ObjectNotFoundRepositoryException,
)
from architectonics.repositories.repository import AbstractBaseRepository
from architectonics.services.schemas import (
    AbstractModelCreateSchema,
    AbstractModelUpdateSchema,
)
from architectonics.services.types import ErrorsType, StatusCodeType


class AbstractBaseService:
    _repository: AbstractBaseRepository = NotImplemented

    async def validate(self, **kwargs) -> dict[str, any]:

        if not kwargs:
            return {}

        attrs = {field: value for field, value in kwargs.items() if field in self._repository.model_fields}

        return attrs

    async def _validate_values(self, **kwargs) -> tuple[dict[str, any], dict[str, list[str]]]:

        errors = {}

        for key, value in kwargs.items():
            validation_method = f"validate_{key}"

            if hasattr(self, validation_method):
                result, error = getattr(
                    self,
                    validation_method,
                )(
                    value,
                    kwargs,
                )

                if not result:
                    errors[key] = errors.get(key, []) + error

        attrs = await self.validate(
            **kwargs,
        )

        return attrs, errors

    async def create_model(
        self,
        create_schema: AbstractModelCreateSchema,
    ) -> tuple[AbstractBaseModel | None, ErrorsType, StatusCodeType]:

        schema_dict = create_schema.model_dump()

        attrs, errors = await self._validate_values(
            **schema_dict,
        )

        if errors:
            return None, errors, HTTP_422_UNPROCESSABLE_ENTITY

        try:
            model = await self._repository.create_model(
                values=attrs,
            )
        except ObjectAlreadyExistsRepositoryException:
            return None, "object_already_exist", HTTP_409_CONFLICT

        return model, None, HTTP_200_OK

    async def get_model(
        self,
        model_id: str,
    ) -> tuple[AbstractBaseModel | None, ErrorsType, StatusCodeType]:

        try:
            model = await self._repository.get_model(
                model_id=model_id,
            )
        except ObjectNotFoundRepositoryException:
            return None, "object_not_found", HTTP_404_NOT_FOUND

        return model, None, HTTP_200_OK

    async def update_model(
        self,
        model_id: str,
        update_schema: AbstractModelUpdateSchema,
    ) -> tuple[AbstractBaseModel | None, ErrorsType, StatusCodeType]:

        schema_dict = update_schema.model_dump(
            by_alias=False,
        )

        attrs, errors = await self._validate_values(
            **schema_dict,
        )

        if errors:
            return None, errors, HTTP_422_UNPROCESSABLE_ENTITY

        try:
            model = await self._repository.update_model(
                model_id=model_id,
                values=attrs,
            )
        except ForeignKeyViolationRepositoryException as e:
            return None, f"{e}", HTTP_422_UNPROCESSABLE_ENTITY
        except IntegrityErrorRepositoryException as e:
            return None, f"{e}", HTTP_404_NOT_FOUND
        except ObjectNotFoundRepositoryException:
            return None, "object_not_found", HTTP_404_NOT_FOUND

        return model, None, HTTP_200_OK

    async def delete_model(
        self,
        model_id: str,
    ) -> tuple[None, ErrorsType, StatusCodeType]:

        _, errors, status_code = await self.get_model(
            model_id=model_id,
        )

        if errors:
            return None, errors, status_code

        await self._repository.delete_model(
            model_id=model_id,
        )

        return None, None, HTTP_204_NO_CONTENT

    async def get_models_list(
        self,
    ) -> tuple[list[AbstractBaseModel], ErrorsType, StatusCodeType]:

        models = await self._repository.get_models_list()

        return models, None, HTTP_200_OK
