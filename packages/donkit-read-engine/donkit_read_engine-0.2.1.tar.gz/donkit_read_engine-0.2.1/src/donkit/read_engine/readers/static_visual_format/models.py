import asyncio
import base64
import hashlib
import json
import os
import sys
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, Literal, TypeVar

import requests
import google.auth
from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI, AzureOpenAI, OpenAI
from google import genai
from google.genai import types
from loguru import logger
from requests.models import Response


# Load .env file with explicit search (important for Windows)
# Try multiple locations in priority order
_env_loaded = False
for _fname in (".env.local", ".env"):
    # 1. Try current working directory
    _cwd_path = Path.cwd() / _fname
    if _cwd_path.exists():
        load_dotenv(_cwd_path, override=False)
        _env_loaded = True
    # 2. Try parent directories (walk up to 3 levels)
    _parent = Path.cwd()
    for _ in range(3):
        _parent = _parent.parent
        _parent_env = _parent / _fname
        if _parent_env.exists():
            load_dotenv(_parent_env, override=False)
            _env_loaded = True
            break
    # 3. Fallback to find_dotenv
    if not _env_loaded:
        _found = find_dotenv(filename=_fname, usecwd=True)
        if _found:
            load_dotenv(_found, override=False)
            _env_loaded = True

logger.remove()
log_level = os.getenv("RAGOPS_LOG_LEVEL", os.getenv("LOG_LEVEL", "ERROR"))
# Force INFO level if no env vars loaded to help debug
if not _env_loaded:
    log_level = "DEBUG"
logger.add(
    sys.stderr,
    level=log_level,
    enqueue=False,
    backtrace=False,
    diagnose=False,
)

# Warn if no .env was loaded
if not _env_loaded:
    logger.warning(
        "⚠️ No .env file found in current directory or parent directories. "
        "Image analysis may fail without proper credentials. "
        "Please create a .env file with RAGOPS_OPENAI_API_KEY or other provider credentials."
    )

T = TypeVar("T", bound=Callable[..., Any])


def retry_on_exception(
    max_retries: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[T], T]:
    """Decorator that retries a function when specified exceptions occur.

    Args:
        max_retries: Maximum number of retry attempts
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exceptions to catch and retry on
    """

    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break

                    wait_time = min(
                        initial_wait * (2**attempt)
                        + (0.1 * attempt),  # expo backoff with jitter
                        max_wait,
                    )
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed with error: {e!s}. "
                        f"Retrying in {wait_time:.2f} seconds..."
                    )
                    time.sleep(wait_time)

            # If we get here, all retries failed
            logger.error(
                f"All {max_retries} attempts failed. Last error: {last_exception!s}"
            )
            raise last_exception  # type: ignore

        return wrapper  # type: ignore

    return decorator


# Content type constants
CONTENT_TYPES = (
    "Charts",
    "Diagrams",
    "Flowcharts",
    "Tables",
    "Text Documents",
    "Other",
)

# Prompt constants
AGENT_PROMPT: str = (
    "Identify what is shown in the image and categorize it into one of these categories: {}. "
    "Answer options: [Charts, Diagrams, Flowcharts, Tables, Text Documents, Slides, Other]"
    "In your response, write only the category name"
).format(", ".join(CONTENT_TYPES))

CONTENT_PROMPTS: dict[str, str] = {
    "Charts": (
        "Extract and structure the chart information in JSON format. Include: "
        "1. chartType - identify the type of chart (line, bar, scatter, etc.) "
        "2. axes - detail both x and y axes with names, units, scales, and range "
        "3. dataPoints - list all visible data points with their exact values "
        "4. trends - identify key patterns, correlations, extremes, or anomalies "
        "5. legend - all items from the legend with their descriptions "
        "6. additionalText - any titles, footnotes, or annotations on the chart "
        "Be precise, concise, and avoid subjective interpretations. Format response as a JSON object."
    ),
    "Diagrams": (
        "Extract and structure all diagram information in JSON format. Include: "
        "1. diagramType - identify the specific type of diagram "
        "2. elements - list all components with their labels, values, and relative sizes "
        "3. relationships - describe all connections between elements "
        "4. colorCoding - explain any color significance "
        "5. metrics - extract all numerical data with proper context "
        "6. labelText - capture all text labels exactly as shown "
        "Be precise, concise, and avoid subjective interpretations. Format response as a JSON object."
    ),
    "Flowcharts": (
        "Extract and structure the flowchart information in JSON format. Include: "
        "1. nodes - list all blocks with their exact labels and functions "
        "2. connections - detail all arrows with their directions and any annotations "
        "3. decisionPoints - identify all branch points and their conditions "
        "4. startEnd - clearly mark starting and ending points "
        "5. processFlow - describe the complete sequence of steps "
        "6. annotations - capture any additional text or notes "
        "Be precise, concise, and avoid subjective interpretations. Format response as a JSON object."
    ),
    "Tables": (
        "Extract and structure the table information in JSON format with: "
        "1. headers - list all column and row headers exactly as shown "
        "2. data - capture all cell values preserving their exact format (text, numbers) "
        "3. relationships - identify any data relationships or patterns "
        "4. footnotes - include any table notes or references "
        "5. title - capture any table title or caption "
        "Format the table data as a proper JSON array with named fields for each column. "
        "Be precise, concise, and avoid subjective interpretations."
    ),
    "Text Documents": (
        "Extract all text content from the image and structure it in JSON format with: "
        "1. title - document title or heading if present "
        "2. sections - organize content by logical sections "
        "3. paragraphs - preserve paragraph structure "
        "4. formatting - note any emphasized text, bullet points, or numbered lists "
        "5. metadata - capture dates, page numbers, or other metadata "
        "Transcribe all text exactly as shown without adding interpretations. "
        "Format response as a JSON object."
    ),
    "Slides": (
        "Extract and structure all slide content in JSON format with the following keys: "
        '"title": extract the main slide title, '
        '"content": all body text preserving bullet points and hierarchical structure, '
        '"tables": format any tables as nested JSON arrays with column headers, '
        '"charts": describe any charts with type, data points, and trends, '
        '"images": brief descriptions of any non-chart images, '
        '"notes": any presenter notes or footnotes. '
        "Be extremely precise and concise. Avoid any commentary or subjective interpretation. "
        "Format response as a clean JSON object without line breaks or extra formatting."
    ),
    "Other": (
        "Extract and structure the image content in JSON format with: "
        '"type": identify the primary content type, '
        '"textElements": list all visible text elements exactly as shown, '
        '"visualElements": describe key visual components concisely, '
        '"data": extract any numerical data or measurements, '
        '"relationships": identify any clear relationships between elements. '
        "Be precise, concise, and avoid subjective interpretations. "
        "Format response as a clean JSON object without fluff or commentary."
    ),
}

DEFAULT_PROMPT: str = (
    "Extract and structure all content from the image in JSON format with the following structure: "
    '{"type": identify the main content type (chart, table, text, etc.), '
    '"title": extract any prominent title or heading, '
    '"textContent": transcribe all visible text maintaining structure, '
    '"dataElements": identify and extract any data points, measurements, or values, '
    '"visualElements": list key visual components objectively, '
    '"relationships": note any patterns, trends, or logical connections, '
    '"metadata": capture any dates, references, or attributions}. '
    "Be extremely precise and concise. Omit subjective interpretations, commentary, or explanations. "
    "If the image contains tables or structured data, format as nested JSON arrays. "
    "For charts, include exact values where legible. Response must be valid JSON."
)

# Cache configuration
CACHE_FILE = Path("image_cache.json")

# Type aliases
T = TypeVar("T")


# Interface definitions
class ImageCacheService(ABC):
    """Interface for image caching operations."""

    @abstractmethod
    def get(self, image_hash: str) -> str | None:
        """Get cached result for an image hash."""
        ...

    @abstractmethod
    def set(self, image_hash: str, content: str) -> None:
        """Cache result for an image hash."""
        ...

    @abstractmethod
    def get_hash(self, image_bytes: bytes) -> str:
        """Generate hash for image bytes."""
        ...


class ImageAnalysisService(ABC):
    """Interface for image analysis operations."""

    @abstractmethod
    def analyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Analyze image content based on the provided prompt."""
        pass

    @abstractmethod
    async def aanalyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Async: Analyze image content based on the provided prompt."""
        pass

    @abstractmethod
    def analyze_image_type(self, encoded_image: str) -> str:
        """Determine the type of content in the image."""
        pass

    @abstractmethod
    def analyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] | None = None,
    ) -> str:
        """Use an agent approach to first identify image type then analyze accordingly."""
        pass

    @abstractmethod
    async def aanalyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] | None = None,
    ) -> str:
        """Async: Use an agent approach to first identify image type then analyze accordingly."""
        pass

    @staticmethod
    def generate_specific_prompt(image_type: str) -> str:
        return CONTENT_PROMPTS.get(image_type, DEFAULT_PROMPT)

    @abstractmethod
    def call_text_only(self, prompt: str) -> str:
        """Call the service with a text-only prompt."""
        pass


# Implementation classes
class FileBasedImageCache:
    """File-based implementation of image caching service."""

    def __init__(self, cache_file: Path = CACHE_FILE):
        self.cache_file = cache_file
        self._cache = self._load_cache()

    def _load_cache(self) -> dict[str, str]:
        if self.cache_file.exists():
            try:
                content = self.cache_file.read_text()
                if not content.strip():
                    return {}
                return json.loads(content)
            except Exception as e:
                logger.error(
                    f"Failed to load cache: {e}. Deleting corrupted cache file."
                )
                try:
                    self.cache_file.unlink()
                except Exception as unlink_error:
                    logger.error(f"Failed to delete corrupted cache: {unlink_error}")
        return {}

    def _save_cache(self) -> None:
        try:
            self.cache_file.write_text(
                json.dumps(self._cache, indent=4, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def get_hash(self, image_bytes: bytes) -> str:
        return hashlib.md5(image_bytes).hexdigest()

    def get(self, image_hash: str) -> str | None:
        return self._cache.get(image_hash)

    def set(self, image_hash: str, content: str) -> None:
        self._cache[image_hash] = content
        self._save_cache()


class GeminiImageAnalysisService(ImageAnalysisService):
    """Implementation using Google's Gemini model for image analysis.

    This class follows the Singleton pattern to ensure only one instance exists.
    """

    _instance = None
    _initialized = False

    def __new__(cls, cache_service: ImageCacheService = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cache_service: ImageCacheService = None):
        if not self._initialized:
            self.cache_service = cache_service or FileBasedImageCache()

            # Initialize Vertex AI with various auth options
            project_env = (
                os.environ.get("VERTEXAI_PROJECT")
                or os.environ.get("VERTEX_PROJECT")
                or os.environ.get("GOOGLE_CLOUD_PROJECT")
            )
            location_env = (
                os.environ.get("VERTEXAI_LOCATION")
                or os.environ.get("GOOGLE_CLOUD_REGION")
                or "us-central1"
            )

            credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            credentials_path = os.environ.get("RAGOPS_VERTEX_CREDENTIALS")

            try:
                credentials_info = None
                auth_source = None

                # Load credentials from available sources
                if credentials_json:
                    credentials_info = json.loads(credentials_json)
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                        "/tmp/vertex_creds.json"
                    )
                    with open("/tmp/vertex_creds.json", "w") as f:
                        json.dump(credentials_info, f)
                    auth_source = "GOOGLE_CREDENTIALS_JSON"
                elif credentials_path and Path(credentials_path).exists():
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                    with open(credentials_path) as f:
                        credentials_info = json.load(f)
                    auth_source = "RAGOPS_VERTEX_CREDENTIALS"

                # Create client with service account or ADC
                if credentials_info:
                    self._client = genai.Client(
                        vertexai=True,
                        project=project_env or credentials_info.get("project_id", ""),
                        location=location_env,
                    )
                    logger.debug(
                        f"Initialized Vertex AI with service account from {auth_source}"
                    )
                else:
                    # Try Application Default Credentials (ADC)
                    creds, project_adc = google.auth.default()
                    project_final = project_env or project_adc or ""
                    if not project_final:
                        logger.warning(
                            "Vertex project not set; set VERTEXAI_PROJECT or GOOGLE_CLOUD_PROJECT for best results"
                        )
                    self._client = genai.Client(
                        vertexai=True,
                        project=project_final,
                        location=location_env,
                    )
                    logger.debug(
                        "Initialized Vertex AI with Application Default Credentials"
                    )
            except Exception as e:
                logger.warning(f"Vertex AI init failed: {e!s}")
                raise e

            self._initialized = True

    @retry_on_exception(
        max_retries=3,
        initial_wait=1.0,
        max_wait=10.0,
        exceptions=(
            Exception,  # Catch all exceptions by default
        ),
    )
    def _call_gemini_api(self, encoded_image: str, prompt: str) -> str:
        """Make the actual API call to Gemini with retry logic."""
        if not self._client:
            raise RuntimeError("Vertex AI client not initialized")

        # Decode image bytes
        image_bytes = base64.b64decode(encoded_image)

        # Create content with image and text
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                ],
            )
        ]

        config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=8192,
            system_instruction=prompt,
        )

        response = self._client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )

        # Extract text from response
        try:
            if response.candidates and len(response.candidates) > 0:
                cand = response.candidates[0]
                if cand.content and cand.content.parts:
                    text_parts = [
                        p.text
                        for p in cand.content.parts
                        if hasattr(p, "text") and p.text
                    ]
                    return "".join(text_parts)
        except AttributeError:
            pass

        return ""

    def call_text_only(self, prompt: str) -> str:
        """Make a text-only API call to Gemini (no image).

        Args:
            prompt: Text prompt to send to the model

        Returns:
            str: Model's text response
        """
        if not self._client:
            raise RuntimeError("Vertex AI client not initialized")

        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )
        ]

        config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=8192,
        )

        response = self._client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )

        # Extract text from response
        text = ""
        try:
            if response.candidates and len(response.candidates) > 0:
                cand = response.candidates[0]
                if cand.content and cand.content.parts:
                    text_parts = [
                        p.text
                        for p in cand.content.parts
                        if hasattr(p, "text") and p.text
                    ]
                    text = "".join(text_parts)
        except AttributeError:
            pass

        return text

    def analyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Analyze image using Gemini model with retry logic.

        Args:
            encoded_image: Base64 encoded image string
            prompt: Prompt to use for analysis
            **kwargs: Additional arguments (not used, kept for compatibility)

        Returns:
            str: Analysis result from Gemini

        Raises:
            Exception: If all retry attempts fail or if there's an error with the API call
        """
        # Check cache first
        if self.cache_service:
            image_hash = self.cache_service.get_hash(encoded_image.encode())
            cached_result = self.cache_service.get(image_hash)
            if cached_result and cached_result not in CONTENT_TYPES:
                logger.debug("Using cached image analysis result")
                return cached_result

        try:
            response_text = self._call_gemini_api(encoded_image, prompt)
            # Cache the result
            if self.cache_service:
                image_hash = self.cache_service.get_hash(encoded_image.encode())
                self.cache_service.set(image_hash, response_text)

            return response_text

        except Exception as e:
            logger.error(f"Failed to analyze image after retries: {e!s}")
            return "Error: Failed to analyze image"

    def analyze_image_type(self, encoded_image: str) -> str:
        """Determine the type of content in the image using Gemini."""
        return self.analyze_image(encoded_image, AGENT_PROMPT)

    def analyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] = "Other",
    ) -> str:
        """Use a two-step approach: first identify image type then analyze accordingly."""
        # uncomment image type detection if needed (need more llm calls)
        # if not image_type:
        #     image_type = self.analyze_image_type(encoded_image)
        #     logger.debug(f"Detected image type: {image_type}")

        specific_prompt = self.generate_specific_prompt(image_type)
        return self.analyze_image(encoded_image, specific_prompt)

    async def aanalyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Async: Analyze image using Gemini (delegates to sync via thread)."""
        return await asyncio.to_thread(
            self.analyze_image, encoded_image, prompt, **kwargs
        )

    async def aanalyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] = "Other",
    ) -> str:
        """Async: Use a two-step approach (delegates to sync via thread)."""
        return await asyncio.to_thread(
            self.analyze_with_agent, encoded_image, image_type
        )


class OpenAIImageAnalysisService(ImageAnalysisService):
    """Implementation using standard OpenAI Vision models (gpt-4o family) via official SDK.

    Environment variables:
        - OPENAI_API_KEY: API key for OpenAI
        - OPENAI_BASE_URL: Custom base URL (optional, default: https://api.openai.com/v1)
        - OPENAI_ORG: Organization ID (optional)
        - OPENAI_VISION_MODEL: Model name (optional, default: gpt-4o-mini)
    """

    def __init__(
        self,
        cache_service: ImageCacheService | None = None,
        *,
        model: str | None = None,
    ):
        self.cache_service = cache_service or FileBasedImageCache()
        self.model = model or os.getenv(
            "OPENAI_VISION_MODEL", os.getenv("RAGOPS_LLM_MODEL", "gpt-4.1-mini")
        )
        self._api_key = os.getenv("OPENAI_API_KEY", os.getenv("RAGOPS_OPENAI_API_KEY"))
        self._base_url = os.getenv(
            "OPENAI_BASE_URL",
            os.getenv("RAGOPS_OPENAI_BASE_URL", "https://api.openai.com/v1"),
        ).rstrip("/")
        self._org = os.getenv("OPENAI_ORG")
        self._local = threading.local()

        if not self._api_key:
            raise ValueError(
                "OpenAI API key not configured. "
                "Please set RAGOPS_OPENAI_API_KEY or OPENAI_API_KEY environment variable."
            )

        # Initialize async client
        self._async_client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            organization=self._org,
            timeout=60.0,
        )

        logger.debug("Initialized OpenAI service configuration")

    @property
    def _client(self) -> OpenAI:
        """Thread-local OpenAI client to avoid conflicts in multi-threading."""
        if not hasattr(self._local, "client"):
            self._local.client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                organization=self._org,
                timeout=60.0,
            )
        return self._local.client

    def _create_chat_completion(self, prompt: str, encoded_image: str) -> str:
        """Create a chat completion with image using OpenAI SDK."""
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_image}"
                            },
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()

    def analyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        # Cache first
        if self.cache_service:
            image_hash = self.cache_service.get_hash(encoded_image.encode())
            cached_result = self.cache_service.get(image_hash)
            if cached_result and cached_result not in CONTENT_TYPES:
                logger.debug("Using cached image analysis result (OpenAI)")
                return cached_result

        try:
            content = self._create_chat_completion(prompt, encoded_image)
            if self.cache_service:
                image_hash = self.cache_service.get_hash(encoded_image.encode())
                self.cache_service.set(image_hash, content)
            return content
        except Exception as e:
            logger.error(f"OpenAI analyze_image failed: {e!s}")
            return "Error: Failed to analyze image"

    def call_text_only(self, prompt: str) -> str:
        """Make a text-only API call to OpenAI (no image).

        Args:
            prompt: Text prompt to send to the model

        Returns:
            str: Model's text response
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI call_text_only failed: {e!s}")
            return "Error: Failed to process text-only request"

    def analyze_image_type(self, encoded_image: str) -> str:
        return self.analyze_image(encoded_image, AGENT_PROMPT)

    def analyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] = "Other",
    ) -> str:
        specific_prompt = self.generate_specific_prompt(image_type)
        return self.analyze_image(encoded_image, specific_prompt)

    async def _acreate_chat_completion(self, prompt: str, encoded_image: str) -> str:
        """Async: Create a chat completion with image using OpenAI SDK."""
        response = await self._async_client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_image}"
                            },
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()

    async def aanalyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Async: Analyze image using OpenAI Vision API."""
        # Cache first
        if self.cache_service:
            image_hash = self.cache_service.get_hash(encoded_image.encode())
            cached_result = self.cache_service.get(image_hash)
            if cached_result and cached_result not in CONTENT_TYPES:
                logger.debug("Using cached image analysis result (OpenAI)")
                return cached_result

        try:
            content = await self._acreate_chat_completion(prompt, encoded_image)
            if self.cache_service:
                image_hash = self.cache_service.get_hash(encoded_image.encode())
                self.cache_service.set(image_hash, content)
            return content
        except Exception as e:
            logger.error(f"OpenAI aanalyze_image failed: {e!s}")
            return "Error: Failed to analyze image"

    async def aanalyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] = "Other",
    ) -> str:
        """Async: Use a two-step approach: first identify image type then analyze accordingly."""
        specific_prompt = self.generate_specific_prompt(image_type)
        return await self.aanalyze_image(encoded_image, specific_prompt)


class AzureOpenAIImageAnalysisService(ImageAnalysisService):
    """Implementation using Azure OpenAI Vision models via official SDK.

    Environment variables:
        - RAGOPS_AZURE_OPENAI_API_KEY: API key for Azure OpenAI
        - RAGOPS_AZURE_OPENAI_ENDPOINT: Azure endpoint URL (e.g., https://your-resource.openai.azure.com/)
        - RAGOPS_AZURE_OPENAI_API_VERSION: API version (optional, default: 2024-02-15-preview)
        - RAGOPS_AZURE_OPENAI_DEPLOYMENT: Deployment/model name (optional, default: gpt-4o-mini)
    """

    def __init__(
        self,
        cache_service: ImageCacheService | None = None,
        *,
        model: str | None = None,
    ):
        self.cache_service = cache_service or FileBasedImageCache()
        self.model = model or os.getenv("RAGOPS_AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self._api_key = os.getenv("RAGOPS_AZURE_OPENAI_API_KEY")
        self._azure_endpoint = os.getenv("RAGOPS_AZURE_OPENAI_ENDPOINT")
        self._api_version = os.getenv(
            "RAGOPS_AZURE_OPENAI_API_VERSION", "2024-02-15-preview"
        )
        self._local = threading.local()

        if not self._api_key or not self._azure_endpoint:
            raise ValueError(
                "Azure OpenAI credentials not configured. "
                "Please set both RAGOPS_AZURE_OPENAI_API_KEY and RAGOPS_AZURE_OPENAI_ENDPOINT environment variables."
            )

        logger.debug(
            f"Initialized Azure OpenAI service configuration with endpoint {self._azure_endpoint}"
        )

    @property
    def _client(self) -> AzureOpenAI:
        """Thread-local Azure OpenAI client to avoid conflicts in multi-threading."""
        if not hasattr(self._local, "client"):
            self._local.client = AzureOpenAI(
                api_key=self._api_key,
                azure_endpoint=self._azure_endpoint,
                api_version=self._api_version,
                timeout=60.0,
            )
        return self._local.client

    def _create_chat_completion(self, prompt: str, encoded_image: str) -> str:
        """Create a chat completion with image using Azure OpenAI SDK."""
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_image}"
                            },
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()

    def analyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        # Cache first
        if self.cache_service:
            image_hash = self.cache_service.get_hash(encoded_image.encode())
            cached_result = self.cache_service.get(image_hash)
            if cached_result and cached_result not in CONTENT_TYPES:
                logger.debug("Using cached image analysis result (Azure OpenAI)")
                return cached_result

        try:
            content = self._create_chat_completion(prompt, encoded_image)
            if self.cache_service:
                image_hash = self.cache_service.get_hash(encoded_image.encode())
                self.cache_service.set(image_hash, content)
            return content
        except Exception as e:
            logger.error(f"Azure OpenAI analyze_image failed: {e!s}")
            return "Error: Failed to analyze image"

    def call_text_only(self, prompt: str) -> str:
        """Make a text-only API call to Azure OpenAI (no image).

        Args:
            prompt: Text prompt to send to the model

        Returns:
            str: Model's text response
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Azure OpenAI call_text_only failed: {e!s}")
            return "Error: Failed to process text-only request"

    def analyze_image_type(self, encoded_image: str) -> str:
        return self.analyze_image(encoded_image, AGENT_PROMPT)

    def analyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] = "Other",
    ) -> str:
        specific_prompt = self.generate_specific_prompt(image_type)
        return self.analyze_image(encoded_image, specific_prompt)

    async def aanalyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Async: Analyze image using Azure OpenAI (delegates to sync via thread)."""
        return await asyncio.to_thread(
            self.analyze_image, encoded_image, prompt, **kwargs
        )

    async def aanalyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] = "Other",
    ) -> str:
        """Async: Use a two-step approach (delegates to sync via thread)."""
        return await asyncio.to_thread(
            self.analyze_with_agent, encoded_image, image_type
        )


class QwenImageAnalysisService(ImageAnalysisService):
    """Implementation using Qwen2-VL-7B model for image analysis."""

    def __init__(
        self,
        model_url: str = os.getenv("QWEN2_VL_7B_MODEL_URL"),
        cache_service: ImageCacheService = None,
    ):
        if not model_url:
            raise ValueError(
                "Qwen2-VL-7B model URL not configured. "
                "Please set one of the following:\n"
                "  1. RAGOPS_OPENAI_API_KEY for OpenAI\n"
                "  2. RAGOPS_AZURE_OPENAI_ENDPOINT for Azure OpenAI\n"
                "  3. QWEN2_VL_7B_MODEL_URL for Qwen model\n"
                "  4. RAGOPS_VERTEX_CREDENTIALS for Google Vertex AI"
            )
        self.model_url = model_url
        self.cache_service = cache_service or FileBasedImageCache()

    def analyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Analyze image using Qwen model."""
        temperature = kwargs.get("temperature", 0.3)

        # Check cache first
        if self.cache_service:
            image_hash = self.cache_service.get_hash(encoded_image.encode())
            cached_result = self.cache_service.get(image_hash)
            if cached_result and cached_result not in CONTENT_TYPES:
                logger.debug("Using cached image analysis result")
                return cached_result

        request_payload: dict[str, Any] = {
            "image": encoded_image,
            "message": prompt,
            "temperature": temperature,
            "top_p": 0.9,
        }

        response: Response = requests.post(self.model_url, json=request_payload)

        try:
            content = response.json()["content"][0]

            # Cache the result
            if self.cache_service:
                image_hash = self.cache_service.get_hash(encoded_image.encode())
                self.cache_service.set(image_hash, content)

            return content
        except Exception as ex:
            logger.error(f"ERROR {ex} on image {response.json()}")
            return "<BROKEN IMAGE>"

    def call_text_only(self, prompt: str) -> str:
        """Make a text-only API call to Qwen (no image).

        Note: This may not be supported by all Qwen deployments.

        Args:
            prompt: Text prompt to send to the model

        Returns:
            str: Model's text response

        Raises:
            NotImplementedError: If the Qwen endpoint doesn't support text-only requests
        """
        # Try to send text-only request - some Qwen deployments might not support this
        request_payload: dict[str, Any] = {
            "message": prompt,
            "temperature": 0.2,
            "top_p": 0.9,
        }

        try:
            response: Response = requests.post(
                self.model_url, json=request_payload, timeout=30
            )
            response.raise_for_status()
            return response.json()["content"][0]
        except Exception as e:
            logger.warning(f"Qwen text-only call failed: {e}")
            raise NotImplementedError("Qwen service may not support text-only requests")

    def analyze_image_type(self, encoded_image: str) -> str:
        """Determine the type of content in the image using Qwen."""
        return self.analyze_image(encoded_image, AGENT_PROMPT)

    def analyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] = "Other",
    ) -> str:
        """Use a two-step approach: first identify image type then analyze accordingly."""
        # if not image_type:
        #     image_type = self.analyze_image_type(encoded_image)
        #     logger.debug(f"Detected image type: {image_type}")

        specific_prompt = self.generate_specific_prompt(image_type)
        return self.analyze_image(encoded_image, specific_prompt)

    async def aanalyze_image(
        self, encoded_image: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Async: Analyze image using Qwen (delegates to sync via thread)."""
        return await asyncio.to_thread(
            self.analyze_image, encoded_image, prompt, **kwargs
        )

    async def aanalyze_with_agent(
        self,
        encoded_image: str,
        image_type: Literal["Slides", "Other"] = "Other",
    ) -> str:
        """Async: Use a two-step approach (delegates to sync via thread)."""
        return await asyncio.to_thread(
            self.analyze_with_agent, encoded_image, image_type
        )


class ImageAnalysisFactory:
    """Factory for creating appropriate image analysis service instances.

    Provider selection priority:
    1. IMAGE_ANALYSIS_PROVIDER env variable (explicit choice)
    2. Auto-detection based on available credentials

    Supported IMAGE_ANALYSIS_PROVIDER values:
    - 'vertex' or 'gemini': Google Vertex AI Gemini
    - 'azure_openai' or 'azure': Azure OpenAI
    - 'openai': Standard OpenAI
    - 'qwen': Qwen2-VL-7B
    """

    @staticmethod
    def create_service(
        cache_service: ImageCacheService | None = None,
    ) -> ImageAnalysisService:
        """Create an appropriate image analysis service based on available credentials."""
        if cache_service is None:
            cache_service = FileBasedImageCache()
        # Check for explicit provider selection first
        provider = os.environ.get(
            "RAGOPS_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "")
        ).lower()
        logger.info(f"🔍 Image analysis provider: {provider or 'auto-detect'}")
        if provider in ("vertex", "vertexai"):
            logger.debug("Using Vertex AI Gemini service (explicit)")
            return GeminiImageAnalysisService(cache_service=cache_service)
        elif provider in ("azure_openai", "azure"):
            logger.debug("Using Azure OpenAI Vision service (explicit)")
            return AzureOpenAIImageAnalysisService(cache_service=cache_service)
        elif provider == "openai":
            logger.debug("Using OpenAI Vision service (explicit)")
            return OpenAIImageAnalysisService(cache_service=cache_service)
        elif provider:
            logger.warning(
                f"Unknown IMAGE_ANALYSIS_PROVIDER: {provider}. "
                "Supported values: vertex, gemini, azure_openai, azure, openai"
                "Falling back to auto-detection."
            )
        # Check for Azure OpenAI
        azure_endpoint = os.environ.get("RAGOPS_AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.environ.get("RAGOPS_AZURE_OPENAI_API_KEY")

        if azure_endpoint or azure_api_key:
            logger.debug("Using Azure OpenAI Vision service (auto-detected)")
            return AzureOpenAIImageAnalysisService(cache_service=cache_service)

        # Auto-detect based on available credentials
        # Detect Vertex availability via multiple signals
        if any(
            [
                os.environ.get("GOOGLE_CREDENTIALS_JSON"),
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
                os.environ.get("VERTEXAI_PROJECT"),
                os.environ.get("VERTEX_PROJECT"),
                os.environ.get("GOOGLE_CLOUD_PROJECT"),
                os.environ.get("RAGOPS_VERTEX_CREDENTIALS"),
            ]
        ):
            logger.debug("Using Vertex AI Gemini service (auto-detected)")
            return GeminiImageAnalysisService(cache_service=cache_service)

        # Check for standard OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            logger.debug("Using OpenAI Vision service (auto-detected)")
            return OpenAIImageAnalysisService(cache_service=cache_service)

        logger.debug("Using Qwen2-VL-7B model service (fallback)")
        return QwenImageAnalysisService(cache_service=cache_service)


# Factory function to get the appropriate implementation
def get_image_analysis_service(
    cache_service: ImageCacheService | None = None,
) -> ImageAnalysisService:
    """Get the appropriate image analysis service implementation."""
    return ImageAnalysisFactory.create_service(cache_service)


# Backward compatibility functions
def analyze_image_type(encoded_image: str) -> str:
    """Analyzes the image to determine its type (e.g., chart, flowchart, table, diagram, or scanned document).

    :param encoded_image: The base64-encoded image string.
    :return: The type of data found in the image.
    """
    service = get_image_analysis_service()
    return service.analyze_image_type(encoded_image)


def generate_specific_prompt(image_type: str) -> str:
    """Generates a specific prompt based on the type of image.

    :param image_type: The type of data found in the image.
    :return: The generated specific prompt for the image type.
    """
    service = get_image_analysis_service()
    return service.generate_specific_prompt(image_type)


def qwen2_vl_7b_model_agent(
    encoded_image: str, image_type: Literal["Slides", "Other"] | None = None
) -> str:
    """The agent first identifies the type of data in the image and then sends a specific prompt for further analysis.

    :param encoded_image: The base64-encoded image string.
    :param image_type: Input image type.
    :return: The final detailed analysis based on the image type.
    """
    service = get_image_analysis_service()
    return service.analyze_with_agent(encoded_image, image_type)
