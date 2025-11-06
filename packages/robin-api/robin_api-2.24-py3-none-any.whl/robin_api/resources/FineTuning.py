


from typing import TYPE_CHECKING
from .._resource import SyncAPIResource
from .._models import construct_type_v2
from ..types import ApiResponse
from typing import TYPE_CHECKING, Iterator
from ..types import  ChatCompletionChunk, ChatCompletion, FilesModel, Models, DeepLevel, IndexFile, MetricsChunk,FineTunninResponse, ResponseModel,ResponseModelTuning, DataItemTuning,DataMedia,MediaData
import validators
from typing import Union, Dict
from typing_extensions import Literal
from .._models import BaseModel
from typing import  Optional
from typing import List, Union, Dict,Tuple
import csv
import json
import pandas as pd
if TYPE_CHECKING:
    from .._client import RobinAIClient

__all__ = ["FineTuning"]


def ensure_list(value, key):
    if key in value and not isinstance(value[key], list):
        value[key] = [value[key]]



class CLIFileCreateArgs(BaseModel):
    file: str
    purpose: str


class FineTuning(SyncAPIResource):
    #from .._client import RobinAIClient
    def __init__(self, client) -> None:
        super().__init__(client)


    def upload_local_file(self, file:str, purpose:str, description:str) -> FilesModel | ApiResponse:
        args = CLIFileCreateArgs(file=file,purpose=purpose)
        source = "DATASET"
        df = pd.read_csv(file)
        num_rows = df.shape[0]
        if not description:
            raise ValueError("description is required")     
        data= self.get_data_file(file)
        columns = data[1]
        columns = ",".join(columns)
        numRows = num_rows
        data = data[2]
       



        with open(args.file, 'rb') as file:
            files = {'file': (args.file, file)}
            value : ApiResponse = self._post_form(
                    end_point = "fine-tuning/upload-data-set",
                    file= files,
                    body = {"purpose": args.purpose, "description": description, "source": source,
                    "numRows": numRows,
                    "colums": columns, 
                    "data": data,             
                    }

                    ) 
            if value.status_code == 200:
                response_data = value.message
    
                # Asegúrate de que response_data sea un diccionario
                if isinstance(response_data, list):
                    if len(response_data) == 1:
                        response_data = response_data[0]
                    else:
                        raise TypeError("Expected a single dict but got a list")

                return construct_type_v2(type_=MediaData, value=response_data)
            else:
                return value

    def get_data_file(self, file: str) -> Union[ApiResponse, Dict[str, Union[str, int, bool]]]:


        if not file.endswith('.csv'):
            return {}

        columns = []

        example_records = []

        num_records = 0



        with open(file, 'r') as csvfile: 
            csvreader = csv.DictReader(csvfile)
            columns = csvreader.fieldnames
            for row in csvreader:
                num_records += 1
                example_records.append(row)
                if num_records >= 10:
                    break

        json_strings = [json.dumps(obj) for obj in example_records]

        # Unir las cadenas sin corchetes y sin comas al final
        output = ",".join(json_strings)


        return num_records, columns, output
        


    def star_fine_tuning(self,
                        model: str,
                        task: str,
                        sub_category: str,
                        media_id: str,
                        description: str,
                        params: dict,
                        params_input: dict,
                        params_output: str,
                        extension: str):
        body_request = {
            "model": model,
            "task": task,
            "subCategory": sub_category,
            "mediaId": media_id,
            "description": description,
            "params": params,
            "paramsInput": params_input,
            "paramsOutput": params_output,
            "extension": extension,
        }
        allowed_tasks = ["classification-text", "language-modeling", "text-to-images"]
        if task not in allowed_tasks:
            raise ValueError("Task must be one of the following: 'classification-text', 'language-modeling' or 'text-to-images'")

        if task == "classification-text":
            required_params = {
                "num_train_epochs": int,
                "per_device_train_batch_size": int,
                "per_device_eval_batch_size": int,
                "warmup_steps": int,
                "weight_decay": float,
                "logging_strategy": str,
                "logging_steps": int,
                "evaluation_strategy": str,
                "eval_steps": int,
                "save_strategy": str,
                "fp16": bool,
                "load_best_model_at_end": bool
            }
        elif task == "language-modeling":
            required_params = {
                "optim": str,
                "learning_rate": float,
                "max_grad_norm": float,
                "num_train_epochs": int,
                "evaluation_strategy": str,
                "eval_steps": int,
                "warmup_ratio": float,
                "save_strategy": str,
                "group_by_length": bool,
                "lr_scheduler_type": str
            }
        else:
            required_params = {}

        for param, expected_type in required_params.items():
            if param not in params:
                raise ValueError(f"Parameter '{param}' is required for task '{task}'")
            if not isinstance(params[param], expected_type):
                raise ValueError(f"Parameter '{param}' must be of type '{expected_type.__name__}'")

        value: ApiResponse = self._post(
            end_point="fine-tuning",
            body=body_request
        )
        if value.status_code == 200:
            return construct_type_v2(type_=FineTunninResponse, value=value.message)
        else:
            return value


    def fine_tuning_file_test(self, link_data:str ,fine_tuning_id:str) :
        if not link_data or not fine_tuning_id:
            raise ValueError("Both 'link_data' and 'fine_tuning_id' are required.")
        body_request = {
            "linkDataSet": link_data,
            "fineTuningId": fine_tuning_id
        }
        value: ApiResponse = self._post(
            end_point="fine-tuning/fie-test",
            body=body_request
        )
        if value.status_code == 200:
            return value.message
        else:
            return value

    

    def fine_tuning_test(self , input :dict, fine_tuning_id:str, temperature:float, max_tokens:int=512):
        if not 0 <= temperature <= 1:
            raise ValueError("Temperature must be a float value between 0 and 1")
        body_request = {
            "paramsInput": input,
            "fineTuningId": fine_tuning_id,
            "maxTokens": max_tokens,
            "temperature": temperature
        }
        value: ApiResponse = self._post(
            end_point="fine-tuning/test",
            body=body_request
        )
        if value.status_code == 200:
            return value.message
        else:
            return value


    def get_fine_tuning_results(self, page: int = 1, limit: int = 10) -> Union[ApiResponse, Dict[str, Union[str, int, bool]]]:
        params = {'page': page, 'limit': limit}
        value: ApiResponse = self._get(
            end_point="fine-tuning/",
            params=params
        )
        if value.status_code == 200:
            return construct_type_v2(type_=ResponseModelTuning, value=value.message)
        else:
            return value

    def get_fine_tuning_detail(self, fine_tuning_id: str):
        end_point = f"fine-tuning/{fine_tuning_id}"
        value: ApiResponse = self._get(
            end_point=end_point
        )
        if value.status_code == 200:
            return construct_type_v2(type_=DataItemTuning, value=value.message)
        else:
            return value


