from pydantic import BaseModel, ValidationError, field_validator
from typing import Union


class StoreAssetRequest(BaseModel):
    folderPath: Union[str, list[str]]

    @field_validator('folderPath', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class DeleteFolderRequest(BaseModel):
    folderPath: str
