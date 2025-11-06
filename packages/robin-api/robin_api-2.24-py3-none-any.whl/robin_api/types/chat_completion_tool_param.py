# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations
from typing_extensions import Literal, Required, TypedDict, TypeAlias
from typing import Optional, Dict

__all__ = ["ChatCompletionToolParam", "FunctionDefinition", "FunctionParameters"]


from typing import Optional, Dict
from pydantic import BaseModel, Field, RootModel
from typing_extensions import Literal

class FunctionParameters(RootModel[Dict[str, object]]):
    # Usa el tipo `Dict` para representar los parámetros como JSON Schema
    #__root__: Dict[str, object] = Field(..., description="The parameters the function accepts, described as a JSON Schema object.")
    pass

class FunctionDefinition(BaseModel):
    name: str = Field(..., description="The name of the function to be called, Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.")
    description: str = Field(..., description="A description of what the function does.")
    parameters: Optional[FunctionParameters] = Field(None, description="The parameters the function accepts, described as a JSON Schema object.")
    strict: Optional[bool] = Field(None, description="Whether to enable strict schema adherence when generating the function call.")

class ChatCompletionToolParam(BaseModel):
    function: FunctionDefinition
    type: Literal["function"] = Field(..., description="The type of the tool. Currently, only `function` is supported.")
