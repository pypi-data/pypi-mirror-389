# fonadalabs/ws_client.py
import asyncio
import json
import os
import ssl
from pathlib import Path
from typing import Optional

from loguru import logger

class ASRWebSocketClient:
    """
    Fonada ASR WebSocket client.
    - Supports secure (wss) and insecure (ws) connections
    - Requires authentication token for all connections
    - Streams audio in chunks (real-time simulation)
    - Logs progress, buffering, and final results
    """

    def __init__(self, url: str = "wss://kb.fonada.ai/v1/asr/stream", token: Optional[str] = None, use_ssl: bool = True, verify_ssl: bool = True):
        self.url = url
        self.token = token or os.getenv("FONADALABS_API_KEY")
        
        # Validate that token is provided (required for authentication)
        if not self.token:
            raise ValueError(
                "Authentication token is required. Please provide it via:\n"
                "1. ASRWebSocketClient(token='your-api-key')\n"
                "2. Environment variable: export FONADALABS_API_KEY='your-api-key'\n"
                "3. .env file with FONADALABS_API_KEY='your-api-key'"
            )
        
        # Configure SSL context for wss:// connections
        if use_ssl and url.startswith("wss://"):
            self.ssl_context = ssl.create_default_context()
            if not verify_ssl:
                # Disable SSL verification for self-signed certificates
                self.ssl_context.check_hostname = False
                self.ssl_context.verify_mode = ssl.CERT_NONE
        else:
            self.ssl_context = None

    async def transcribe_file(self, file_path: str, language_id: str = "hi") -> dict:
        """
        Stream an audio file to the ASR backend over WebSocket and return the final transcription.
        """
        try:
            import websockets  # type: ignore
            from websockets.exceptions import WebSocketException
        except ImportError as exc:
            raise ImportError(
                "websockets is required for ASRWebSocketClient. Install the SDK with the 'ws' extra: "
                "pip install fonadalabs-sdk[ws]"
            ) from exc

        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            # Try both parameter names for compatibility with different websockets versions
            try:
                # websockets >= 10.0 uses extra_headers
                async with websockets.connect(self.url, ssl=self.ssl_context, max_size=None, extra_headers=headers) as ws:
                    return await self._handle_transcription(ws, file_path, language_id)
            except TypeError as e:
                if "extra_headers" in str(e):
                    # websockets < 10.0 uses additional_headers
                    async with websockets.connect(self.url, ssl=self.ssl_context, max_size=None, additional_headers=headers) as ws:
                        return await self._handle_transcription(ws, file_path, language_id)
                else:
                    raise

        except WebSocketException as e:
            logger.exception(f"WebSocket error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.exception(f"WebSocket error: {e}")
            return {"error": str(e)}

    async def _handle_transcription(self, ws, file_path: str, language_id: str) -> dict:
        """Handle the WebSocket transcription logic"""
        logger.info(f" Connected to {self.url}")

        # Set language
        await ws.send(f"LANG:{language_id}")
        logger.info(f" Language set to: {language_id}")

        # Load audio bytes (keep container headers intact for backend decoders)
        audio_bytes = Path(file_path).read_bytes()
        total = len(audio_bytes)
        logger.debug(f"Streaming {total} bytes from {file_path}")

        # Stream in chunks (simulate live streaming)
        chunk_size = 8192
        for offset in range(0, total, chunk_size):
            await ws.send(audio_bytes[offset:offset + chunk_size])
            await asyncio.sleep(0.005)  # adjust for real-time pacing if needed

        # Signal end of audio
        await ws.send("__END__")
        logger.info(" Sent end of stream signal")

        # Collect responses
        final_result = None
        async for msg in ws:
            message = json.loads(msg)
            event = message.get("event")

            if event in ("progress", "buffering"):
                logger.info(f" Received: {message}")
            elif event == "final":
                final_result = message
                logger.success(f" Transcription complete: {message.get('text')}")
                break
            elif event == "error":
                logger.error(f" Error: {message.get('message')}")
                break

        return final_result or {"error": "No final result received"}

    def transcribe(self, file_path: str, language_id: str = "hi"):
        """
        Synchronous wrapper (for convenience in scripts).
        """
        return asyncio.run(self.transcribe_file(file_path, language_id))
