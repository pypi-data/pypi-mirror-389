from abc import ABC
from typing import Callable

from asyncpg.exceptions import ForeignKeyViolationError
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from architectonics.config.database import session
from architectonics.models.abstract_base_model import AbstractBaseModel
from architectonics.repositories.exceptions import (
    ForeignKeyViolationRepositoryException,
    IntegrityErrorRepositoryException,
    ObjectAlreadyExistsRepositoryException,
    ObjectNotFoundRepositoryException,
)


class AbstractBaseRepository(ABC):
    _model: type[AbstractBaseModel] = NotImplemented
    _session: Callable = session
    _integrity_error: type[IntegrityError] = IntegrityError

    def get_session(self) -> AsyncSession:
        return self._session()

    @property
    def model_fields(self):
        return self._model.__table__.columns

    async def create_model(
        self,
        values: dict[str, any],
    ) -> AbstractBaseModel:

        model = self._model(
            **values,
        )

        async with self.get_session() as session:

            session.add(model)

            try:
                await session.commit()
            except self._integrity_error as e:
                raise ObjectAlreadyExistsRepositoryException(e)

            return model

    async def get_model(
        self,
        model_id: str,
    ) -> AbstractBaseModel:

        statement = select(
            self._model,
        ).where(
            self._model.id == model_id,
        )

        async with self.get_session() as session:

            result = await session.execute(
                statement=statement,
            )

            model = result.scalars().first()

            if model is None:
                raise ObjectNotFoundRepositoryException()

            return model

    async def update_model(
        self,
        model_id: str,
        values: dict[str, any],
    ) -> AbstractBaseModel:

        filtered_values = {k: v for k, v in values.items() if v is not None}

        statement = (
            update(
                self._model,
            )
            .where(
                self._model.id == model_id,
            )
            .values(
                **filtered_values,
            )
            .returning(
                self._model,
            )
        )

        async with self.get_session() as session:
            try:
                result = await session.execute(
                    statement=statement,
                )
                await session.commit()
            except self._integrity_error as e:

                orig = getattr(e.orig, "__cause__", None)

                if isinstance(orig, ForeignKeyViolationError):
                    raise ForeignKeyViolationRepositoryException()

                raise IntegrityErrorRepositoryException(e)

            model = result.scalars().first()

            if model is None:
                raise ObjectNotFoundRepositoryException()

            return model

    async def delete_model(
        self,
        model_id: str,
    ) -> None:

        statement = delete(
            self._model,
        ).where(
            self._model.id == model_id,
        )

        async with self.get_session() as session:
            await session.execute(statement)
            await session.commit()

    async def get_models_list(
        self,
    ) -> list[AbstractBaseModel]:

        statement = select(
            self._model,
        )

        async with self.get_session() as session:

            result = await session.execute(
                statement=statement,
            )

            models = result.scalars().all()

            return models
