"""
FonadaLabs SDK
Unified Python SDK for FonadaLabs APIs: TTS, ASR, and Denoise.

Quick Start:
    # Text-to-Speech
    from fonadalabs import TTSClient
    
    client = TTSClient(api_key="your-api-key")
    audio = client.generate_audio("Hello world", "Pravaha")
    
    # WebSocket streaming
    audio = client.generate_audio_ws("Long text here", "Shruti")
    
    # With callbacks
    def on_chunk(num, data):
        print(f"Chunk {num}: {len(data)} bytes")
    
    audio = client.generate_audio_ws(
        "Text here", 
        "Pravaha",
        on_chunk=on_chunk
    )

Features:
    - Multiple Indian voices (Pravaha, Shruti, Aabha, Svara, Vaanee)
    - HTTP POST and WebSocket streaming
    - Redis-cached authentication (100x faster)
    - Comprehensive error handling
    - Context manager support
"""

# TTS exports
from .tts.client import (
    TTSClient,
    TTSError,
    CreditsExhaustedError as TTSCreditsExhaustedError,
    RateLimitError as TTSRateLimitError
)

# ASR exports
from .asr.client import ASRClient
from .asr.ws_client import ASRWebSocketClient
from .asr.exceptions import (
    ASRSDKError,
    ConfigurationError,
    ValidationError,
    AuthenticationError,
    HTTPRequestError,
    ServerError,
    RateLimitError as ASRRateLimitError,
    TimeoutError as ASRTimeoutError,
    CreditsExhaustedError as ASRCreditsExhaustedError,
)
from .asr.languages import SUPPORTED_LANGUAGES, normalize_language, is_supported_language
from .asr.models.types import TranscribeResult, BatchResult, FailedTranscription

# Version info
__version__ = "2.0.1"
__author__ = "FonadaLabs"
__license__ = "Proprietary"

# Public API
__all__ = [
    # TTS Client
    "TTSClient",
    "TTSError",
    "TTSCreditsExhaustedError",
    "TTSRateLimitError",
    
    # ASR Clients
    "ASRClient",
    "ASRWebSocketClient",
    
    # ASR Exceptions
    "ASRSDKError",
    "ConfigurationError",
    "ValidationError",
    "AuthenticationError",
    "HTTPRequestError",
    "ServerError",
    "ASRRateLimitError",
    "ASRTimeoutError",
    "ASRCreditsExhaustedError",
    
    # ASR Language utilities
    "SUPPORTED_LANGUAGES",
    "normalize_language",
    "is_supported_language",
    
    # ASR Models
    "TranscribeResult",
    "BatchResult",
    "FailedTranscription",
]


