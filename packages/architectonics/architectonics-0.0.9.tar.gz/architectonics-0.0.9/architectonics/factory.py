from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from architectonics.config.base_database_settings import base_database_settings


class BaseAppFactory:
    @classmethod
    def create(cls, title) -> FastAPI:
        app = FastAPI(
            debug=base_database_settings.DEBUG,
            title=title,
            docs_url="/docs/",
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        cls._register_app_routes(app)

        return app

    @classmethod
    def _register_app_routes(cls, app: FastAPI):
        raise NotImplementedError()
