


from typing import TYPE_CHECKING, List, Union, Optional, Iterator, Iterable
from ..types import (Completion, 
                     ChatCompletionChunk,
                    ChatCompletion, 
                    ApiResponse, 
                    Models, 
                    MetricsChunk, 
                    ChatCompletionToolParam,
                    Image,
                    ChatCompletionMessage,
                    ChatCompletionMessageToolCall)
from .._streaming import Stream
from typing_extensions import Literal
import httpx
from .._types import NOT_GIVEN, NotGiven
from .._resource import SyncAPIResource
from .._models import construct_type, construct_type_v2
import json
from pydantic import ValidationError
import uuid

if TYPE_CHECKING:
    from .._client import RobinAIClient

__all__ = ["Completions"]



def ensure_list(value, key):
    if key in value and not isinstance(value[key], list):
        value[key] = [value[key]]

def parse_tool_calls(content: str, tools: list= None) -> ChatCompletionMessage:
    # Si el content es simplemente un string (no se puede parsear a JSON), devolver tal cual
    if not isinstance(content, str) or (not any(char in content for char in ['{', '}', '[', ']'])) or tools == None:
         return ChatCompletionMessage(role="assistant", content=content)
    
    # Dividir el contenido en múltiples partes (si es necesario)
    content_parts = [part.strip() for part in content.split(";") if part.strip()]
    
    # Diccionario para encontrar las herramientas por nombre
    tools_dict = {tool['function']['name']: tool for tool in tools}
    
    # Lista para almacenar las llamadas válidas
    tool_calls = []
    
    # Procesar cada parte del contenido
    for part in content_parts:
        try:
            # Intentar cargar el JSON de la cadena actual
            call_data = json.loads(part)
            
            # Extraer el nombre de la función y los parámetros
            function_name = call_data.get("name")
            parameters = call_data.get("parameters", {})
            
            # Verificar si la función existe en tools
            if function_name in tools_dict:
                tool = tools_dict[function_name]
                
                # Obtener los parámetros requeridos de la tool
                required_params = tool['function']['parameters'].get('required', [])
                
                # Validar si todos los parámetros requeridos están presentes
                if all(param in parameters for param in required_params):
                    # Convertir los parámetros a JSON y crear una llamada de herramienta
                    arguments = json.dumps(parameters)
                    tool_calls.append(ChatCompletionMessageToolCall(
                        id=f"call_{uuid.uuid4().hex[:4]}",  # Genera un ID único corto
                             function={
                                        "name": function_name,
                                        "arguments": arguments,
                                    },
                                type="function",
                            )
                       )
        except (json.JSONDecodeError, TypeError):
            # Si el contenido no es JSON válido, lo ignoramos
            continue
    
    # Si no se encontraron llamadas de herramientas válidas, devolver content tal cual
    if not tool_calls:
        return ChatCompletionMessage(role="assistant", content=content)
    
    # Construir el JSON de respuesta final si hay llamadas válidas
    message = ChatCompletionMessage(
            role="assistant",
            content=None,
            function_call=None,
            tool_calls=tool_calls,
        )
    
    return message


class Completions(SyncAPIResource):
    #from .._client import RobinAIClient
    def __init__(self, client) -> None:
        super().__init__(client)


    def text_to_image(self, *, prompt: str):
        body_request = {
            "prompt": prompt
        }
        response = self._post(
            end_point="text-to-image",
            body=body_request
        )
        if response.status_code == 200:
            response_message = {
                "url": response.message
            }
            return construct_type_v2(type_=Image, value=response_message)
        else:
            return response.json()
   

    def create_stream(
        self,
        *,
        model: Models,
        conversation: Union[str, List[str], List[int], List[List[int]], None],
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        save_response: Optional[Literal[False]] | Literal[True] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,

    ) -> Completion | Stream[Completion] | Iterator[ChatCompletionChunk] | Iterator[MetricsChunk]:

        body_request= {
                    "model": model,
                    "conversation": conversation,
                    "max_new_tokens": max_tokens,
                    "stream": True,
                    "temperature": temperature,
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

    def create(
        self,
        *,
        model: Models,
        conversation: Union[str, List[str], List[int], List[List[int]], None],
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        save_response: Optional[Literal[False]] | Literal[True] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,

    ) -> ChatCompletion | ApiResponse:
        """
           tools: A list of tools the model may call. Currently, only functions are supported as a
            tool. Use this to provide a list of functions the model may generate JSON inputs
            for. A max of 128 functions are supported. 
            """
        try:
            # Intentar crear una instancia del modelo Pydantic
            if tools != None:
                for item in tools:
                    ChatCompletionToolParam(**item)
        except ValidationError as e:
            print("Error de validación:", e)
            return None
        
        body_request= {
                        "model": model,
                        "conversation": conversation,
                        "max_new_tokens": max_tokens,
                        "stream": False,
                        "temperature": temperature,
                        "save_response": save_response,
                        "tools": tools
                    }

        value : ApiResponse = self._post(
                end_point = "get-response",
                body= body_request,
                ) 
        if value.status_code == 200:
            ensure_list(value.message, 'choices')
            completion_obj : ChatCompletion = construct_type_v2(type_=ChatCompletion, value=value.message)
            #completion_obj.choices[0].message = parse_tool_calls(completion_obj.choices[0].message.content, tools)
            return completion_obj
        else:
            return value


        """return self.client.http_client._post(
            "/completions",
            body=maybe_transform(
                {
                    "model": model,
                    "conversation": conversation,
                    "best_of": best_of,
                    "echo": echo,
                    "frequency_penalty": frequency_penalty,
                    "logit_bias": logit_bias,
                    "logprobs": logprobs,
                    "max_tokens": max_tokens,
                    "n": n,
                    "presence_penalty": presence_penalty,
                    "seed": seed,
                    "stop": stop,
                    "stream": stream,
                    "suffix": suffix,
                    "temperature": temperature,
                    "top_p": top_p,
                    "user": user,
                },
                completion_create_params.CompletionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Completion,
            stream=stream or False,
            stream_cls=Stream[Completion],
        ) """




