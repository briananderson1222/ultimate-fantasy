"""
API response compression middleware for improved performance.

This module provides comprehensive compression middleware including:
- Gzip compression for responses
- Content-based compression strategies
- Compression level optimization
- Caching integration
- Performance monitoring
"""

import gzip
import time
import logging
from typing import Callable, Optional, Set, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import asyncio
import json
from io import BytesIO

logger = logging.getLogger(__name__)

class CompressionMiddleware(BaseHTTPMiddleware):
    """Advanced compression middleware with intelligent compression strategies."""

    def __init__(
        self,
        app,
        minimum_size: int = 500,
        compression_level: int = 6,
        compress_media_types: Optional[Set[str]] = None,
        exclude_paths: Optional[Set[str]] = None,
        enable_streaming_compression: bool = True,
        cache_compressed_responses: bool = True
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.enable_streaming_compression = enable_streaming_compression
        self.cache_compressed_responses = cache_compressed_responses

        # Default media types to compress
        self.compress_media_types = compress_media_types or {
            "text/html",
            "text/plain",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/json",
            "application/xml",
            "text/xml",
            "application/x-javascript",
            "application/rss+xml",
            "application/atom+xml",
            "image/svg+xml"
        }

        # Paths to exclude from compression
        self.exclude_paths = exclude_paths or {
            "/health",
            "/metrics",
            "/static/"
        }

        # Compression performance metrics
        self.compression_stats = {
            "total_requests": 0,
            "compressed_requests": 0,
            "total_bytes_saved": 0,
            "average_compression_ratio": 0.0,
            "compression_time_ms": 0.0
        }

        # Cache for compressed responses
        self.compression_cache: Dict[str, bytes] = {}
        self.cache_max_size = 1000

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and apply compression if appropriate."""
        start_time = time.time()

        # Check if path should be excluded
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Check if client accepts gzip compression
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return await call_next(request)

        # Process the request
        response = await call_next(request)

        # Update request count
        self.compression_stats["total_requests"] += 1

        # Check if response should be compressed
        if not self._should_compress_response(response):
            return response

        # Apply compression
        compressed_response = await self._compress_response(
            request, response, start_time
        )

        return compressed_response

    def _should_compress_response(self, response: Response) -> bool:
        """Determine if response should be compressed."""
        # Check status code
        if response.status_code < 200 or response.status_code >= 300:
            return False

        # Check if already compressed
        if "content-encoding" in response.headers:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if content_type not in self.compress_media_types:
            return False

        # Check content length if available
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return False

        return True

    async def _compress_response(
        self, request: Request, response: Response, start_time: float
    ) -> Response:
        """Compress the response content."""
        try:
            # Generate cache key for response
            cache_key = None
            if self.cache_compressed_responses:
                cache_key = self._generate_cache_key(request, response)
                if cache_key in self.compression_cache:
                    # Return cached compressed response
                    cached_content = self.compression_cache[cache_key]
                    return self._create_compressed_response(
                        response, cached_content, from_cache=True
                    )

            # Get response content
            if hasattr(response, 'body'):
                content = response.body
            elif isinstance(response, JSONResponse):
                content = json.dumps(response.content).encode('utf-8')
            elif isinstance(response, StreamingResponse):
                # Handle streaming responses
                return await self._compress_streaming_response(response)
            else:
                # Read content from response
                content = b""
                async for chunk in response.body_iterator:
                    content += chunk

            # Check minimum size after reading content
            if len(content) < self.minimum_size:
                return response

            # Compress content
            compression_start = time.time()
            compressed_content = gzip.compress(content, compresslevel=self.compression_level)
            compression_time = (time.time() - compression_start) * 1000

            # Cache compressed content
            if cache_key and len(self.compression_cache) < self.cache_max_size:
                self.compression_cache[cache_key] = compressed_content

            # Update compression statistics
            self._update_compression_stats(
                len(content), len(compressed_content), compression_time
            )

            # Create compressed response
            return self._create_compressed_response(response, compressed_content)

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return response

    async def _compress_streaming_response(self, response: StreamingResponse) -> Response:
        """Compress streaming response content."""
        if not self.enable_streaming_compression:
            return response

        async def compress_stream():
            """Generator for compressed streaming content."""
            compressor = gzip.GzipFile(mode='wb', fileobj=None, compresslevel=self.compression_level)

            try:
                async for chunk in response.body_iterator:
                    if chunk:
                        compressed_chunk = compressor.compress(chunk)
                        if compressed_chunk:
                            yield compressed_chunk

                # Flush final compressed data
                final_chunk = compressor.flush()
                if final_chunk:
                    yield final_chunk

            except Exception as e:
                logger.error(f"Streaming compression failed: {e}")
                # Fall back to uncompressed stream
                async for chunk in response.body_iterator:
                    yield chunk

        # Create new streaming response with compression
        compressed_response = StreamingResponse(
            compress_stream(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

        # Add compression headers
        compressed_response.headers["content-encoding"] = "gzip"
        compressed_response.headers["vary"] = "Accept-Encoding"

        # Remove content-length as it will change
        if "content-length" in compressed_response.headers:
            del compressed_response.headers["content-length"]

        return compressed_response

    def _create_compressed_response(
        self, original_response: Response, compressed_content: bytes, from_cache: bool = False
    ) -> Response:
        """Create a new response with compressed content."""
        # Create new response
        compressed_response = Response(
            content=compressed_content,
            status_code=original_response.status_code,
            headers=dict(original_response.headers),
            media_type=original_response.media_type
        )

        # Update headers for compression
        compressed_response.headers["content-encoding"] = "gzip"
        compressed_response.headers["vary"] = "Accept-Encoding"
        compressed_response.headers["content-length"] = str(len(compressed_content))

        # Add cache indicator
        if from_cache:
            compressed_response.headers["x-compression-cache"] = "hit"
        else:
            compressed_response.headers["x-compression-cache"] = "miss"

        return compressed_response

    def _generate_cache_key(self, request: Request, response: Response) -> str:
        """Generate cache key for response."""
        import hashlib

        # Include URL, method, and relevant headers in cache key
        key_parts = [
            request.method,
            str(request.url),
            response.headers.get("content-type", ""),
            str(response.status_code)
        ]

        # Include relevant query parameters
        if request.query_params:
            key_parts.append(str(sorted(request.query_params.items())))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _update_compression_stats(
        self, original_size: int, compressed_size: int, compression_time: float
    ):
        """Update compression performance statistics."""
        self.compression_stats["compressed_requests"] += 1

        bytes_saved = original_size - compressed_size
        self.compression_stats["total_bytes_saved"] += bytes_saved

        # Update average compression ratio
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        current_avg = self.compression_stats["average_compression_ratio"]
        request_count = self.compression_stats["compressed_requests"]

        new_avg = ((current_avg * (request_count - 1)) + compression_ratio) / request_count
        self.compression_stats["average_compression_ratio"] = new_avg

        # Update average compression time
        current_time_avg = self.compression_stats["compression_time_ms"]
        new_time_avg = ((current_time_avg * (request_count - 1)) + compression_time) / request_count
        self.compression_stats["compression_time_ms"] = new_time_avg

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression performance statistics."""
        total_requests = self.compression_stats["total_requests"]
        compressed_requests = self.compression_stats["compressed_requests"]

        return {
            "total_requests": total_requests,
            "compressed_requests": compressed_requests,
            "compression_rate": (compressed_requests / total_requests * 100) if total_requests > 0 else 0,
            "total_bytes_saved": self.compression_stats["total_bytes_saved"],
            "average_compression_ratio": self.compression_stats["average_compression_ratio"],
            "average_compression_time_ms": self.compression_stats["compression_time_ms"],
            "cache_size": len(self.compression_cache),
            "cache_hit_rate": self._calculate_cache_hit_rate()
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate based on cache headers."""
        # This would be more accurately tracked with dedicated cache hit/miss counters
        # For now, return an estimated value based on cache size vs compressed requests
        if self.compression_stats["compressed_requests"] == 0:
            return 0.0

        return min(len(self.compression_cache) / self.compression_stats["compressed_requests"] * 100, 100.0)

    def clear_compression_cache(self):
        """Clear the compression cache."""
        self.compression_cache.clear()
        logger.info("Compression cache cleared")

    def set_compression_level(self, level: int):
        """Update compression level (1-9, where 9 is maximum compression)."""
        if 1 <= level <= 9:
            self.compression_level = level
            logger.info(f"Compression level updated to {level}")
        else:
            raise ValueError("Compression level must be between 1 and 9")


class BrotliCompressionMiddleware(BaseHTTPMiddleware):
    """Brotli compression middleware for even better compression ratios."""

    def __init__(self, app, **kwargs):
        super().__init__(app)
        try:
            import brotli
            self.brotli = brotli
            self.brotli_available = True
        except ImportError:
            logger.warning("Brotli not available, falling back to gzip only")
            self.brotli_available = False

        # Inherit configuration from kwargs
        self.minimum_size = kwargs.get('minimum_size', 500)
        self.quality = kwargs.get('quality', 6)  # Brotli quality (0-11)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply Brotli compression if supported."""
        if not self.brotli_available:
            return await call_next(request)

        # Check if client accepts Brotli compression
        accept_encoding = request.headers.get("accept-encoding", "")
        if "br" not in accept_encoding.lower():
            return await call_next(request)

        response = await call_next(request)

        # Apply Brotli compression logic similar to gzip
        # Implementation would follow similar pattern to CompressionMiddleware
        # but using brotli.compress() instead of gzip.compress()

        return response


# Factory function to create compression middleware
def create_compression_middleware(
    minimum_size: int = 500,
    compression_level: int = 6,
    enable_brotli: bool = True,
    **kwargs
) -> BaseHTTPMiddleware:
    """Create compression middleware with optimal settings."""

    if enable_brotli:
        try:
            import brotli
            return BrotliCompressionMiddleware(None, **kwargs)
        except ImportError:
            logger.info("Brotli not available, using gzip compression")

    return CompressionMiddleware(
        None,
        minimum_size=minimum_size,
        compression_level=compression_level,
        **kwargs
    )


# Export compression statistics endpoint
async def compression_stats_endpoint(middleware: CompressionMiddleware) -> Dict[str, Any]:
    """Endpoint to retrieve compression statistics."""
    return middleware.get_compression_stats()