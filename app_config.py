import asyncio
import logging
import os

import TransportLayer.TLInit as TLInit
from bugsnag.handlers import BugsnagHandler

import challenge_listener
import main_listener
import ssl_confirmation_listener

logger = logging.getLogger('HAProxy-service')


@asyncio.coroutine
def setup_application(app):
    """

    :param app:
    :return:
    """
    logger.info("Application setup: STARTED")

    # Initializing bugsnag from within TL library
    TLInit.initialize_bugsnag(
        os.getenv('BUGSNAG_KEY'),
        os.getcwd(),
        os.getenv(
            'APP_ENV',
            'development'
        ),
        'development',
        'test',
        'staging',
        'production'
    )

    # Initializing TL library queues connection ping
    TLInit.initialize_tl("")

    # Bugsnag Handlers
    bugsnag_handler = BugsnagHandler()
    bugsnag_handler.setLevel(logging.ERROR)

    # Startup TL listeners for subscription
    logger.info("Starting TL Subscriptions setup")
    configure_tl_listeners()


def configure_tl_listeners():
    """

    :return:
    """
    main_listener.MainListener()
    challenge_listener.ChallengeListener()
    ssl_confirmation_listener.SslConfirmationListener()
