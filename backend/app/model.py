from pydantic import BaseModel, field_validator
from typing import Union, List, Optional


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


class ExecuteActionRequest(BaseModel):
    action: str
    params: dict


class MoveFilesRequest(BaseModel):
    filePaths: List[str]
    targetDirectory: str


class ConvertFilesRequest(BaseModel):
    filePaths: List[str]
    targetExtension: str


class RenameFilesRequest(BaseModel):
    filePaths: List[str]
    newNames: List[str]


class TagFilesRequest(BaseModel):
    filePaths: List[str]
    tag: str
    color: Optional[int] = 0


class GetFilesWithTagRequest(BaseModel):
    directory: str
    tag: str


class SearchByPatternRequest(BaseModel):
    directory: str
    pattern: str


class SearchByTagsRequest(BaseModel):
    directory: str
    tagKey: str
    tagValue: str


class FilterByDateRequest(BaseModel):
    directory: str
    startDate: float
    endDate: float


class FilterBySizeRequest(BaseModel):
    directory: str
    minSize: int
    maxSize: int


class FilterByTypeRequest(BaseModel):
    directory: str
    fileExtension: str


class CopyFilesRequest(BaseModel):
    filePaths: List[str]
    targetDirectory: str


class CopyDirectoryRequest(BaseModel):
    sourceDirectory: str
    targetDirectory: str


class RecentFilesRequest(BaseModel):
    directory: str
    count: int


class AgentRequest(BaseModel):
    prompt: str
    match_count: Optional[int] = 10


class SummarizeFileRequest(BaseModel):
    fileName: str
    filePath: Optional[str] = None
    content: Optional[str] = None
