
from .._models import BaseModel
from typing import  Union
from typing_extensions import Literal
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from typing import Any, Optional, cast

__all__ = ["FineTuningParamsInput", "FineTuningParams", "FineTunninResponse", "ModelDataSet", "SubCategory", "DataItem", "Link", "Meta", "ResponseModel", "ResponseModelTuning"]
class FineTuningParamsInput(BaseModel):
    input_template: str

class FineTuningParams(BaseModel):
    optim: str
    learning_rate: float
    max_grad_norm: float
    num_train_epochs: int
    evaluation_strategy: str
    eval_steps: int
    warmup_ratio: float
    save_strategy: str
    group_by_length: bool
    lr_scheduler_type: str

class FineTunninResponse(BaseModel):
    FineTuningid: str


class ModelDataSet(BaseModel):
    id: str
    name: str
    description: Optional[str]

class SubCategory(BaseModel):
    id: str
    name: str
    description: Optional[str]

class DataItem(BaseModel):
    id: str
    name: str
    description: str
    label: str
    example: Optional[str]
    modelDataSets: List[ModelDataSet]
    subCategories: List[SubCategory]

class Link(BaseModel): 
    url: Optional[str]
    label: str
    active: bool

class Meta(BaseModel):
    current_page: int
    from_: Optional [int] 
    last_page: int
    links: List[Link]
    path: str
    per_page: int
    to: int
    total: int

    class Config:
        fields = {
            'from_': 'from'
        }

class ResponseModel(BaseModel):
    data: List[DataItem]
    links: dict
    meta: Meta

class FineTuningParamsInput(BaseModel):
    input_template: str

class FineTuningResponse(BaseModel):
    FineTuningid: str


class ModelDataSet(BaseModel):
    id: str
    name: str
    description: Optional[str]

class SubCategory(BaseModel):
    id: str
    name: str
    description: Optional[str]

class Task(BaseModel):
    id: str
    name: str
    description: str
    label: str
    example: Optional[str]
    modelDataSets: List[ModelDataSet]
    subCategories: List[SubCategory]

class DataMedia(BaseModel):
    id: str
    numRows: int
    colums: List[str]
    data: str
    description: Optional[str]

class MediaData(BaseModel):
    id: str
    name: str
    description: Optional[str]
    url: str
    width: Optional[int]
    height: Optional[int]
    source: str
    bytesSize: Optional[str]
    documentId: Optional[str]
    extension: str
    dueAt: Optional[str]
    createdAt: str
    parentEntity: Optional[str]
    parentEntityType: Optional[str]
    type: str
    children: List[str] = []
    userTags: List[str] = []
    dataMedia: Optional[DataMedia]


class DataItemTuning(BaseModel):
    id: str
    model: str
    subCategory: str
    description: str
    urlDataset: Optional[str]
    urlImages: Optional[str]
    trainingParameters: str
    paramsInput:Optional[str]
    progress: Optional[int] = Field(None)
    testings: List[Any]

class Link(BaseModel): 
    url: Optional[str]
    label: str
    active: bool

class Meta(BaseModel):
    current_page: int
    last_page: int
    links: List[Link]
    path: str
    from_: Optional[int] = Field(None)
    per_page: int
    to: int
    total: int

    class Config:
        fields = {
            'from_': 'from'
        }

class ResponseModelTuning(BaseModel):
    data: List[DataItemTuning]
    links: dict
    meta: Meta