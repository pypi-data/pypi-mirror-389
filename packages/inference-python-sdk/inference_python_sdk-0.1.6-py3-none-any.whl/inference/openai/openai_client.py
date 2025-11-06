import uuid
from enum import Enum
from pydantic import BaseModel
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional, Union, Callable, Any, AsyncGenerator, Generator, Iterable
from typing_extensions import Literal, Required, TypedDict
import httpx
from openai import OpenAI, AsyncOpenAI
from openai.pagination import SyncPage
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam
)
from openai.types.model import Model
from pyrate_limiter import Limiter, RequestRate
from tenacity import retry, stop_after_attempt
from openai.types.chat.chat_completion_content_part_image_param import ImageURL

from inference.util.base64 import encode_base64_from_content, format_base64_image, format_base64_audio


class RequestRateDuration(Enum):
    """
    RequestRateDuration
    """
    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 3600 * 24
    MONTH = 3600 * 24 * 30


class LimiterConfig(BaseModel):
    """
    LimiterConfig
    """
    # ratelimit limit, the max request number per interval
    limit: int = 5
    # ratelimit interval, with units as RequestRateDuration
    interval: int = RequestRateDuration.SECOND.value
    # ratelimit delay, if delay is True, the request will be delayed until the ratelimit is passed
    delay: bool = True
    # ratelimit max_delay, if delay is True, the request will be delayed until the ratelimit is passed,
    # but the max delay is max_delay
    max_delay: int = 60


class AudioURL(TypedDict, total=False):
    url: Required[str]


class ChatCompletionContentPartAudioParam(TypedDict, total=False):
    audio_url: Required[AudioURL]

    type: Required[Literal["audio_url"]]


class Error(Exception):
    """
    Base exception for Openai openai.
    """

    pass


class NoModelsAvailableError(Error):
    """
    Raised when no models are available.
    """

    pass


class APIError(Error):
    """
    Raised when API request fails.
    """

    pass


@contextmanager
def handle_api_errors():
    """
    Context manager for handling API errors.
    """
    try:
        yield
    except httpx.HTTPError as e:
        raise APIError(f"API request failed: {str(e)}") from e
    except Exception as e:
        raise Error(f"Unexpected error: {str(e)}") from e


@dataclass
class OpenAIClient:
    """
    A openai that supports both sync and async operations.
    """
    endpoint: str
    base_url: str = ""
    api_key: str = "EMPTY"
    max_retries: int = 1
    timeout_in_seconds: int = 90
    is_async: bool = False
    context: Optional[Dict[str, Any]] = None
    limiter_config: Optional[LimiterConfig] = None

    temperature: Optional[float] = 0.0
    top_p: Optional[float] = 1.0
    presence_penalty: Optional[float] = 0.6
    frequency_penalty: Optional[float] = 0.6
    repetition_penalty: Optional[float] = 1.2

    # Private attributes initialized in post_init
    _identifier: str = field(init=False)
    _openai_client: Union[OpenAI, AsyncOpenAI] = field(init=False)
    _http_client: Union[httpx.Client, httpx.AsyncClient] = field(init=False)
    _limiter: Optional[Limiter] = field(init=False)
    _limiter_delay: Optional[float] = field(init=False)
    _limiter_max_delay: Optional[float] = field(init=False)

    def __post_init__(self):
        """
        Initialize additional attributes after dataclass initialization.
        """
        self._identifier = str(uuid.uuid4())
        self._setup_endpoint()
        self._setup_limiter()
        self._setup_clients()

    def _setup_endpoint(self) -> None:
        """
        Setup API endpoint.
        """
        if self.base_url == "":
            self.base_url = "v1"
        self.endpoint = f"{self.endpoint.rstrip('/')}/{self.base_url.strip('/')}/"

    def _setup_limiter(self) -> None:
        """
        Setup rate limiter if config.yaml provided.
        """
        self._limiter = None
        self._limiter_delay = None
        self._limiter_max_delay = None

        if isinstance(self.limiter_config, LimiterConfig):
            self._limiter = Limiter(
                RequestRate(self.limiter_config.limit, self.limiter_config.interval)
            )
            self._limiter_delay = self.limiter_config.delay
            self._limiter_max_delay = self.limiter_config.max_delay

    def _setup_clients(self) -> None:
        """
        Setup OpenAI and HTTP clients.
        """
        if self.is_async:
            self._setup_async_clients()
        else:
            self._setup_sync_clients()

    def _setup_async_clients(self) -> None:
        """Setup async clients."""
        self._openai_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.endpoint,
            max_retries=self.max_retries,
            timeout=self.timeout_in_seconds
        )

        self._http_client = httpx.AsyncClient(base_url=self.endpoint, timeout=self.timeout_in_seconds)

    def _setup_sync_clients(self) -> None:
        """Setup sync clients."""
        self._openai_client = OpenAI(
            api_key=self.api_key,
            base_url=self.endpoint,
            max_retries=self.max_retries,
            timeout=self.timeout_in_seconds
        )

        self._http_client = httpx.Client(base_url=self.endpoint, timeout=self.timeout_in_seconds)

    def _create_completion_params(self, **kwargs) -> Dict[str, Any]:
        """
        Create standardized completion parameters.
        """
        params = {
            "messages": kwargs["messages"],
            "model": kwargs.get("model", None) if kwargs.get("model", None) is not None else self.models().data[0].id,
            "n": kwargs.get("n", 1),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
            "presence_penalty": kwargs.get(
                "presence_penalty", self.presence_penalty
            ),
            "frequency_penalty": kwargs.get(
                "frequency_penalty", self.frequency_penalty
            ),
            # "stream": kwargs.get("stream", False),
            "extra_body": {
                "repetition_penalty": kwargs.get(
                    "repetition_penalty", self.repetition_penalty
                )
            }
        }

        if "max_completion_tokens" in kwargs:
            params["max_completion_tokens"] = kwargs["max_completion_tokens"]
        if "response_format" in kwargs:
            params["response_format"] = kwargs["response_format"]
        if "stop" in kwargs:
            params["stop"] = kwargs["stop"]

        return params

    async def _execute_with_rate_limit(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with rate limiting if configured.
        """
        if self._limiter is not None:
            async with self._limiter.ratelimit(
                    self._identifier,
                    delay=self._limiter_delay,
                    max_delay=self._limiter_max_delay,
            ):
                return await func(*args, **kwargs)
        return await func(*args, **kwargs)

    @lru_cache(maxsize=128)
    async def async_models(self) -> SyncPage[Model]:
        """
        Get available models with caching.
        """
        return await self._openai_client.models.list()

    def models(self) -> SyncPage[Model]:
        """
        Get available models.
        """
        return self._openai_client.models.list()

    async def async_available_models(self) -> str:
        """
        Get first available model asynchronously.
        """
        models = await self.async_models()
        if not models.data:
            raise NoModelsAvailableError("No available models")
        return models.data[0].id

    def available_models(self) -> str:
        """
        Get first available model synchronously.
        """
        models = self.models()
        if not models.data:
            raise NoModelsAvailableError("No available models")
        return models.data[0].id

    async def chat_acompletion(
            self, request: List[ChatCompletionMessageParam], **kwargs
    ) -> Union[ChatCompletion, AsyncGenerator[ChatCompletionChunk, None]]:
        """
        Async chat completion.
        """
        params = self._create_completion_params(messages=request, **kwargs)
        request_interface = self._openai_client.chat.completions.create
        if "response_format" in params:
            request_interface = self._openai_client.chat.completions.parse

        return await self._execute_with_rate_limit(request_interface, **params)

    def chat_completion(
            self, request: List[ChatCompletionMessageParam], **kwargs
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Sync chat completion.
        """
        params = self._create_completion_params(messages=request, **kwargs)

        request_interface = self._openai_client.chat.completions.create
        if "response_format" in params:
            request_interface = self._openai_client.chat.completions.parse

        if self._limiter is not None:
            with self._limiter.ratelimit(
                    self._identifier,
                    delay=self._limiter_delay,
                    max_delay=self._limiter_max_delay,
            ):
                response = request_interface(**params)
                return response

        response = request_interface(**params)
        return response

    @retry(stop=stop_after_attempt(max_retries), reraise=True)
    async def batch_chat_acompletion(
            self,
            request: List[List[ChatCompletionMessageParam]], **kwargs) \
            -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Async batch chat completion with retry.
        """
        params = {**{"messages": [item.model_dump() for item in request]}, **kwargs}
        params = self._create_completion_params(**params)

        with handle_api_errors():
            response = await self._execute_with_rate_limit(
                self._http_client.post,
                url="chat/batch_completions",
                json=params,
            )
            await response.aclose()
            response.raise_for_status()
            return ChatCompletion.model_validate(response.json())

    @retry(stop=stop_after_attempt(max_retries), reraise=True)
    def batch_chat_completion(
            self,
            request: List[List[ChatCompletionMessageParam]], **kwargs) \
            -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Sync batch chat completion with retry.
        """
        params = {**{"messages": [item.model_dump() for item in request]}, **kwargs}
        params = self._create_completion_params(**params)

        with handle_api_errors():
            if self._limiter is not None:
                with self._limiter.ratelimit(
                        self._identifier,
                        delay=self._limiter_delay,
                        max_delay=self._limiter_max_delay,
                ):
                    return self._execute_batch_request(params)
            return ChatCompletion.model_validate(self._execute_batch_request(params))

    def _execute_batch_request(self, request: Dict, url: str = "chat/batch_completions"):
        """
        Execute batch request.
        """
        response = self._http_client.post(url=url, json=request.model_dump(mode="json"))
        response.close()
        response.raise_for_status()
        return response.json()
