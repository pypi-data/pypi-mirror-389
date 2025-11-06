


from typing import TYPE_CHECKING, List, Union
from .._resource import SyncAPIResource
from .._models import construct_type_v2
from ..types import ApiResponse
from typing import TYPE_CHECKING, Iterator
from ..types import  (ChatCompletionChunk, 
                      ChatCompletion, 
                      FilesModel, 
                      Models,
                      DeepLevel, 
                      IndexFile, 
                      MetricsChunk,
                      ResponseFile, 
                      Documents,
                      DocumentsWithScore)
import validators
from typing_extensions import Literal
from .._models import BaseModel
from typing import  Optional

if TYPE_CHECKING:
    from .._client import RobinAIClient

__all__ = ["Files"]


def ensure_list(value, key):
    if key in value and not isinstance(value[key], list):
        value[key] = [value[key]]



class CLIFileCreateArgs(BaseModel):
    file: str
    purpose: str


class Files(SyncAPIResource):
    #from .._client import RobinAIClient
    def __init__(self, client) -> None:
        super().__init__(client)

    #def upload_web_page_information(self, args: DeepLevel):

    def upload_file(self, *,
        url: Optional[str] = None,
        file_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        collection_name: str) -> FilesModel | ApiResponse:
        # Verifica que 'url' y 'file_id' no existan ambos al mismo tiempo
        if url and file_id:
            raise ValueError("Only 'url' or 'file_id' but no both.")
 
        if not url and not file_id:
            raise ValueError("You must provide either 'url' or 'file_id'. At least one is required.")
    
        args = IndexFile(url=url,file_id=file_id,folder_id=folder_id, collection_name=collection_name)
        body_request = {}
        if args.url != None:
            if not validators.url(args.url):
                raise ValueError("url is not valid")
            body_request = {"fileUrl": args.url}
        else:
            body_request = {"fileId": args.file_id}

        if args.folder_id is not None:
            body_request["apiFolderId"]= args.folder_id
            
        # collection_name is always required
        body_request["collectionName"] = args.collection_name

        value : ApiResponse = self._post(  # pyright: ignore[reportAssignmentType]
                end_point = "folders",
                body= body_request,
                ) 

        if value.status_code == 200:
            return construct_type_v2(type_=ResponseFile, value=value.message)
        else:
            return value
            
    def upload_local_file(self, file:str, purpose:str) -> FilesModel | ApiResponse:
        args = CLIFileCreateArgs(file=file,purpose=purpose)
        with open(args.file, 'rb') as file:
            files = {'file': (args.file, file)}
            value : ApiResponse = self._post_form(
                    end_point = "upload-file",
                    file= files,
                    )
            file_id = value.message['file_id']

            body_request = {"fileId": file_id}

            value  = self._post(
                end_point = "folders",
                body= body_request,
                ) 
            if value.status_code == 200:
                return construct_type_v2(type_=FilesModel, value=value.message)
            else:
                return value
    

    def upload_web_page_information(self, *, url: str, deep_level: Literal[1, 2, 3] = 1 , folder_id=None, max_links=20):
        args = DeepLevel(url=url, deep_level=deep_level, folder_id=folder_id)  
        #if not isinstance(deep_level, DeepLevel):
        #    raise ValueError("deep_level must have values between 1 and 3")

        if not validators.url(url):
            raise ValueError("url is not valid")
        
        if folder_id == None:
            body_request=  {
                            "webUrl": url,
                            "deep_level": deep_level,
                            "max_links": max_links
                            }
        else:
            body_request=  {
                            "webUrl": url,
                            "deep_level": deep_level,
                            "apiFolderId": folder_id,
                            "max_links": max_links
                            }

        value : ApiResponse = self._post(
                end_point = "folders/add-web-url",
                body= body_request,
                ) 
        if value.status_code == 200:
            return construct_type_v2(type_=ResponseFile, value=value.message)
        else:
            return value
        
    def get_similar_sentences(self, *, query:str, api_folder_id:str, top: int = 10, similarity_threshold: float = 0.4, collection_name: Optional[str] = None)  -> DocumentsWithScore:
        body_request= { 
            "query" : query,
            "top": top,
            "apiFolderId": api_folder_id,
            "similarity_threshold": similarity_threshold
        }

        if collection_name is not None:
            body_request["collectionName"] = collection_name

        value : ApiResponse = self._post(
                end_point = "folders/get-similar-sentences",
                body= body_request,
                ) 
        if value.status_code == 200:
            return construct_type_v2(type_=DocumentsWithScore, value=value.message)
        else:
            return value
        
    def get_response_similar_sentences(self, *,
                                       conversation:Union[str, List[str], List[int], List[List[int]], None], 
                                       api_folder_id:str, 
                                       model:Models,
                                       only_with_context: bool, 
                                       top: int = 10, 
                                       similarity_threshold: 
                                       float = 0.4, 
                                       max_new_tokens: 512,
                                       save_response: bool = False) -> ChatCompletion | ApiResponse:
        body_request= { 
            "max_new_tokens": max_new_tokens,
            "stream" : False,
            "model" : model,
            "conversation" : conversation,
            "top": top,
            "folder_id": api_folder_id,
            "similarity_threshold": similarity_threshold,
            "only_with_context": only_with_context,
            "save_response": save_response
        }

        value = self._post(
                end_point = "get-response",
                body= body_request,
                ) 
        if value.status_code == 200:
            return  construct_type_v2(type_=ChatCompletion, value=value.message )
        else:
            return value
            
    def get_response_similar_sentences_stream(self, *,
                                       conversation:str, 
                                       api_folder_id:str, 
                                       model:Models,
                                       only_with_context: bool, 
                                       top: int = 10, 
                                       similarity_threshold: float = 0.4, 
                                       max_new_tokens: 512,
                                       save_response: bool = False) -> Iterator[ChatCompletion] | Iterator[MetricsChunk]:
        body_request= { 
            "max_new_tokens": max_new_tokens,
            "stream" : True,
            "model" : model,
            "conversation" : conversation,
            "top": top,
            "folder_id": api_folder_id,
            "similarity_threshold": similarity_threshold,
            "only_with_context": only_with_context,
            "save_response": save_response
        }

        response = self._stream(
        end_point = "get-response",
        body= body_request,
        )
        for data in response:
            ensure_list(data, 'choices')
            if not ('details' in data.keys()):
                completion_obj = construct_type_v2(type_=ChatCompletionChunk, value=data)
                yield completion_obj
            else:
                completion_obj = construct_type_v2(type_=MetricsChunk, value=data)
                yield completion_obj

            

    def get_folder_files(self, *, api_folder_id:str, collection_name: Optional[str] = None) -> Documents:
        body_request= { 
            "apiFolderId" : api_folder_id,
        }

        if collection_name is not None:
            body_request["collectionName"] = collection_name

        value : ApiResponse = self._post(
                end_point = "folders/get-folder-files",
                body= body_request,
                ) 
        if value.status_code == 200:
          
            return construct_type_v2(type_=Documents, value=value.message )
        else:
            return value
        
    def delete_all_documents(self, *, folder_id: str, collection_name: str) -> ApiResponse:
        """
        Elimina todos los documentos de un collection específico del vector DB.
        """
        body_request = {
            "folder_id": folder_id,
            "collection_name": collection_name
        }

        value : ApiResponse = self._post(
                end_point = "folders/delete-collection",
                body= body_request,
                ) 
        return value

    def delete_element(self, *, folder_id: str, collection_name: str, element_id: str) -> ApiResponse:
        """
        Elimina un elemento específico de un collection del vector DB.
        """
        body_request = {
            "folder_id": folder_id,
            "collection_name": collection_name,
            "element_id": element_id
        }

        value : ApiResponse = self._post(
                end_point = "folders/delete-by-element-id",
                body= body_request,
                ) 
        return value




