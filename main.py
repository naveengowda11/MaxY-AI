"""Run the MAXY local API and web interface."""
import uvicorn

from config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "api.server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.env == "development",
    )


if __name__ == "__main__":
    main()
