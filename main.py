import asyncio
import logging
import logging.handlers as handlers
import os
import sys

from aiohttp import web

import app_config


def setup_custom_logger():
    """

    :return:
    """
    global logger
    logger = logging.getLogger('HAProxy-service')
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_logging_handler = logging.handlers.TimedRotatingFileHandler(
        filename='/var/log/haproxy-service.log',
        when = 'D',
        interval=5)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    file_logging_handler.setFormatter(formatter)
    file_logging_handler.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_logging_handler)
    logger.debug("Logger Configured")
    return logger


app = web.Application()


@asyncio.coroutine
def health_check(request):
    return web.json_response({'message': 'OK', 'status': 'UP'}, status=200)


if __name__ == "__main__":

    logging = setup_custom_logger()
    # Route for health check
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)

    # Configuring the application
    asyncio.get_event_loop().run_until_complete(
        app_config.setup_application(app)
    )

    # Running the application
    if os.getenv("APP_ENV") == "development":
        web.run_app(
            app,
            host="127.0.0.1",
            port=int(os.getenv("APP_PORT", 5000)
                     )
        )
    else:
        web.run_app(
            app,
            port=int(os.getenv("APP_PORT", 5000)
                     )
        )
