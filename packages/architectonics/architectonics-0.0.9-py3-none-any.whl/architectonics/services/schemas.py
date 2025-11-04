from pydantic import BaseModel


class AbstractModelCreateSchema(BaseModel):
    pass


class AbstractModelCreateErrorsSchema(BaseModel):
    pass


class AbstractModelGetSchema(BaseModel):
    pass


class AbstractModelUpdateSchema(BaseModel):
    pass


class AbstractModelUpdateErrorsSchema(BaseModel):
    pass
