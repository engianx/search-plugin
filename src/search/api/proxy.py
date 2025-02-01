from fastapi import FastAPI, HTTPException
import httpx
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)

async def proxy_request(url: str):
    """Proxy the request and strip out security headers."""
    try:
        # Set Accept-Encoding to identity to avoid receiving compressed data.
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Accept-Encoding": "identity"},
                follow_redirects=True
            )

            # Log original headers
            logger.debug(f"Original headers for {url}: {response.headers}")

            # Create a new response without restrictive security headers
            headers = dict(response.headers)

            # Remove headers that prevent framing
            headers.pop('x-frame-options', None)
            headers.pop('X-Frame-Options', None)
            headers.pop('content-security-policy', None)
            headers.pop('Content-Security-Policy', None)

            # Remove potential Content-Encoding header to avoid confusion
            headers.pop('content-encoding', None)
            headers.pop('Content-Encoding', None)

            # Add permissive headers
            headers['Access-Control-Allow-Origin'] = '*'
            headers['Content-Security-Policy'] = "frame-ancestors *"

            # Log modified headers
            logger.debug(f"Modified headers for {url}: {headers}")

            return StreamingResponse(
                content=response.iter_bytes(),
                status_code=response.status_code,
                headers=headers,
                media_type=response.headers.get('content-type')
            )
    except Exception as e:
        logger.error(f"Proxy error for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to proxy request: {str(e)}")