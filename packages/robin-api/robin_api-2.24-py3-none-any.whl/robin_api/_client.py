



import httpx

from ._constants import (
    DEFAULT_LIMITS,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    RAW_RESPONSE_HEADER,
    DEFAULT_HEADERS
)
from typing_extensions import Literal, override

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Type,
    Union,
    Generic,
    Mapping,
    TypeVar,
    Iterable,
    Iterator,
    Optional,
    Generator,
    AsyncIterator,
    cast,
    overload,
)

import distro

from typing import Union, Mapping
from ._streaming import Stream as Stream
import platform
from . import resources
import os
from ._exceptions import RobinError
import json
from .types import ApiResponse 
__all__ = [
    "RobinAIClient",
]

""" import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("httpx")
logger.setLevel(logging.DEBUG) """


def _merge_mappings(
    obj1,
    obj2,
):
    """Merge two mappings of the same type, removing any values that are instances of `Omit`.
    In cases with duplicate keys the second mapping takes precedence.
    """
    return {**obj1, **obj2}


Platform = Union[
    Literal[
        "MacOS",
        "Linux",
        "Windows",
        "FreeBSD",
        "OpenBSD",
        "iOS",
        "Android",
        "Unknown",
    ],
]


def get_platform() -> Platform:
    system = platform.system().lower()
    platform_name = platform.platform().lower()
    if "iphone" in platform_name or "ipad" in platform_name:
        # Tested using Python3IDE on an iPhone 11 and Pythonista on an iPad 7
        # system is Darwin and platform_name is a string like:
        # - Darwin-21.6.0-iPhone12,1-64bit
        # - Darwin-21.6.0-iPad7,11-64bit
        return "iOS"

    if system == "darwin":
        return "MacOS"

    if system == "windows":
        return "Windows"

    if "android" in platform_name:
        # Tested using Pydroid 3
        # system is Linux and platform_name is a string like 'Linux-5.10.81-android12-9-00001-geba40aecb3b7-ab8534902-aarch64-with-libc'
        return "Android"

    if system == "linux":
        # https://distro.readthedocs.io/en/latest/#distro.id
        distro_id = distro.id()
        if distro_id == "freebsd":
            return "FreeBSD"

        if distro_id == "openbsd":
            return "OpenBSD"

        return "Linux"

    if platform_name:
        return platform_name

    return "Unknown"

class OtherArch:
    def __init__(self, name: str) -> None:
        self.name = name

    @override
    def __str__(self) -> str:
        return f"other:{self.name}"
    
Arch = Union[OtherArch, Literal["x32", "x64", "arm", "arm64", "unknown"]]
def get_architecture() -> Arch:
    python_bitness, _ = platform.architecture()
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "arm64"

    # TODO: untested
    if machine == "arm":
        return "arm"

    if machine == "x86_64":
        return "x64"

    # TODO: untested
    if python_bitness == "32bit":
        return "x32"

    if machine:
        return OtherArch(machine)

    return "unknown"

class Chat:
    def __init__(self):
        self.completions = resources.Completions(self)


class RobinAIClient():
    #completions: resources.Completions
    #completions_based_text: resources.Completions
    #upload_file: resources.Completions
    #models: resources.Models
    #fine_tuning: resources.FineTuning
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: int =  DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client. See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async ROBIN client instance.

        This automatically infers the following arguments from their corresponding environment variables if they are not provided:
        - `api_key` from `ROBIN_API_KEY`
        """

        self._init_client(api_key = api_key, 
                          base_url=base_url, 
                          timeout=timeout,
                          max_retries=max_retries, 
                          default_headers=default_headers, 
                          default_query=default_query, 
                          http_client = http_client,
                         _strict_response_validation =_strict_response_validation)



    @property
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}
    
    def close(self):
        self.http_client.close()

    def create_new_client(self):
        if self.http_client.is_closed:
            self.http_client = None
            self._init_client(api_key = self.api_key, 
                            base_url=self.base_url, 
                            timeout=self.timeout,
                            max_retries=self.max_retries, 
                            default_headers=self.default_headers, 
                            default_query=self.default_query, 
                            http_client = self.http_client,
                            _strict_response_validation = self.strict_response_validation)
    def _init_client(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: int =  DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client. See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_query = default_query
        self.strict_response_validation = _strict_response_validation
        if api_key is None:
            api_key = os.environ.get("ROBIN_API_KEY")
        if api_key is None:
            raise RobinError(
                "The api_key client option must be set either by passing api_key to the client or by setting the ROBIN_API_KEY environment variable"
            )
        if default_headers is None:
            self.default_headers = DEFAULT_HEADERS

        self.api_key = api_key

        if base_url is None:
            self.base_url = f"https://robin-ai.xyz:8443/api/api-response-service/"
            #self.base_url = f"http://localhost:8443/api/api-response-service/"

        self._default_stream_cls = Stream
        self.headers = self._build_headers()
        proxies = {
        "http://": "http://localhost:8080",
        "https://": "http://localhost:8080"
        }
        self.http_client = http_client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            verify=False,
            headers=self.headers,
            #proxies= proxies
        )

        self.completions = resources.Completions(self)
        self.files = resources.Files(self)
        self.fine_tuning = resources.FineTuning (self)
         
        #self.completions_based_text: resources.Completions
        #self.upload_file: resources.Completions
        #self.models: resources.Models
        #self.fine_tuning: resources.FineTuning


    def _build_headers(self) -> httpx.Headers:
        headers_dict = _merge_mappings(self.default_headers, self.auth_headers)
        headers_dict = _merge_mappings(headers_dict, self.platform_headers())
        #headers = httpx.Headers(headers_dict)
        return headers_dict
    
    def platform_headers(self) -> Dict[str, str]:
        return {
            "X-Stainless-Lang": "python",
            #"X-Stainless-Package-Version": self._version,
            "X-Stainless-OS": str(get_platform()),
            "X-Stainless-Arch": str(get_architecture()),
            "X-Stainless-Runtime": platform.python_implementation(),
            "X-Stainless-Runtime-Version": platform.python_version(),
        }
    
    def stream(self, end_point: str, body: json, method: str="POST"):
        self.create_new_client()
        try:
            with self.http_client.stream(
                url = end_point,

                method=method,
                json= body,
                ) as response:
                if response.status_code == 200:
                    buffer = ""
                    for data in response.iter_bytes():
                        buffer += data.decode('utf-8')
                        parts = buffer.split("\n\nevent: update\ndata: ")
                        for part in parts[:-1]:  # Process all parts except the last incomplete one
                            if part.startswith("DONE"):
                                break
                            try:
                                #json_part = data.decode('utf-8').split("data: ", 1)[1]
                                prefix = 'event: update\ndata: '
                                if part.startswith(prefix):
                                    part = part.lstrip(prefix)
                                objeto = json.loads(part)
                                yield objeto
                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON: {e}")

                        buffer = parts[-1]                 
                else:
                    err = self._make_status_error_from_response(response)
                    return err
        except Exception as e:
            print(f"An error occurred during streaming: {e}")
        finally:
            # Ensure the client is closed when streaming is done
            self.close()
            
    def stream_backup_alone(self, end_point: str, body: json, method: str="POST"):
        self.create_new_client()
        with self.http_client.stream(
            url = end_point,
            #url = "https://localhost:8443/api/api-response-service/get-response",
            method=method,
            json= body,
            ) as response:
            if response.status_code == 200:
                for data in response.iter_bytes():
                    json_part = data.decode('utf-8').split("data: ", 1)[1]
                    if json_part.startswith("DONE"):
                        break
                    #print(json_part)
                    objeto = json.loads(json_part)
                    yield objeto                   
            else:
                err = self._make_status_error_from_response(response)
                return err

            
    def post(self, end_point: str, body: json):
        try:
            self.create_new_client()
            with self.http_client as client:
                response = client.post(
                url = end_point,
                json = body,
                )
                if response.status_code == 200:
                    return ApiResponse (message=response.json(), status_code=200)
                else:
                    err = self._make_status_error_from_response(response)
                    return err
            
        except Exception as e:
            print(f"An error occurred during streaming: {e}")
            return ApiResponse(message=f"Error: {str(e)}", status_code=500)
        finally:
            # Ensure the client is closed when streaming is done
            self.close()
            
    def post_form(self, end_point: str, file, body: json = None):
        try:
            self.create_new_client()
            with self.http_client as client:
                response = client.post(
                    url = self.base_url + end_point,
                    files = file,
                    data = body
                    )
                if response.status_code == 200:
                    return ApiResponse (message=response.json(), status_code=200)
                else:
                    err = self._make_status_error_from_response(response)
                    return err

        except Exception as e:
            print(f"An error occurred during streaming: {e}")
            return ApiResponse(message=f"Error: {str(e)}", status_code=500)
        finally:
            # Ensure the client is closed when streaming is done
            self.close()
        
    def get(self, end_point: str, params: dict = None):
        try:
            self.create_new_client()
            with self.http_client as client:
                response = client.get(
                    url=end_point,
                    params=params,  # Añadir los parámetros de ruta aquí
                )
                if response.status_code == 200:
                    return ApiResponse(message=response.json(), status_code=200)
                else:
                    err = self._make_status_error_from_response(response)
                    return err
        except Exception as e:
            print(f"An error occurred during streaming: {e}")
            return ApiResponse(message=f"Error: {str(e)}", status_code=500)
        finally:
            # Ensure the client is closed when streaming is done
            self.close()

    def _make_status_error_from_response(
        self,
        response: httpx.Response,
    ) -> ApiResponse:
        if hasattr(response, 'read') and callable(getattr(response, 'read')):
            err_text = str(response.read().decode('utf-8'))
        else:
            err_text = response.text.strip()
        body = err_text
        try:
            body = json.loads(err_text)
            err_msg = f"Error code: {response.status_code} - {body}"
        except Exception:
            err_msg = err_text or f"Error code: {response.status_code}"

        return self._make_status_error(err_msg,  response=response)
    
    def _make_status_error(
        self,
        err_msg: str,
        response: httpx.Response,
    ) -> ApiResponse:

        if response.status_code == 400:
            return ApiResponse( message= err_msg , status_code = 400 )

        if response.status_code == 401:
            return ApiResponse( message= err_msg , status_code = 401 )

        if response.status_code == 403:
            return ApiResponse( message= err_msg , status_code = 403 )

        if response.status_code == 404:
            return ApiResponse( message= err_msg , status_code = 404 )

        if response.status_code == 409:
            return ApiResponse( message= err_msg , status_code = 409 )

        if response.status_code == 422:
            return ApiResponse( message= err_msg , status_code = 422 )

        if response.status_code == 429:
            return ApiResponse( message= err_msg , status_code = 429 )

        if response.status_code >= 500:
            return ApiResponse( message= err_msg , status_code = 500 )
        
        return ApiResponse( message= "Unknown error" , status_code = 500 ) 


Client = RobinAIClient