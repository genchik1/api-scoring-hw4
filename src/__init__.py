from http.server import HTTPServer
from src.api import MainHTTPHandler
from src.settings import get_logger

logger = get_logger(__name__)


def start_app(port: int) -> None:
    server = HTTPServer(("localhost", port), MainHTTPHandler)
    logger.info("Starting server at %s" % port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
