from typing import List, Optional
from pydantic import BaseModel, HttpUrl

# Define the model for the metadata
class Metadata(BaseModel):
    document_id: Optional[str] = None
    file_name: Optional[str] = None
    page_label: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    url: Optional[HttpUrl] = None
    element_id: Optional[str] = None
    doc_id: Optional[str] = None

# Define the model for the individual object
class Document(BaseModel):
    sentence: str
    metadata: Metadata

# Define the model for the array of objects
class Documents(BaseModel):
    docs: List[Document]
    count: int

# Define the model for the individual object
class DocumentWithScore(BaseModel):
    sentence: str
    metadata: Metadata
    score: float

# Define the model for the array of objects
class DocumentsWithScore(BaseModel):
    sentences: List[DocumentWithScore]


