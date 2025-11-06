

from .._models import BaseModel
from typing import  Union
from typing_extensions import Literal
from typing import Any, Optional, cast

__all__ = ["FilesModel" , "IndexFile", "DeepLevel", "Folder", "File", "ResponseFile", ],

        
class FilesModel(BaseModel):
        file_id: str


class IndexFile(BaseModel):
        url: Optional[str]
        folder_id: Optional[Any]=None
        file_id: Optional[str]
        collection_name: Optional[str]


class DeepLevel(BaseModel):
        url: str
        folder_id: Optional[Any]=None
        deep_level:  Literal[
                1,
                2,
                3
            ]

class Folder(BaseModel):
    apiFolderId: str
    createdAt: str

class File(BaseModel):
    url: str
    tokens: Optional[int]  # Haciendo tokens opcional
    documentId: Optional[str] 
    createdAt: str

class ResponseFile(BaseModel):
        folder: Folder
        file: File
