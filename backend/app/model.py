from pydantic import BaseModel, ValidationError

class StoreAssetRequest(BaseModel):
    folderPath: str