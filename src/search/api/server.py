"""FastAPI server for search API."""
import uvicorn
from ..utils.config import load_config

def run_server(host: str = None, port: int = None):
    """Run the FastAPI server.

    Args:
        host: Optional host override (defaults to config)
        port: Optional port override (defaults to config)
    """
    config = load_config()
    api_config = config.get("api", {})

    uvicorn.run(
        "search.api.search:app",
        host=host or api_config.get("host", "0.0.0.0"),
        port=port or api_config.get("port", 8080),
        workers=api_config.get("workers", 4),
        reload=True
    )

if __name__ == "__main__":
    run_server()