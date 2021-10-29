import asyncio
import logging
import os

from TransportLayer import Constants
from TransportLayer.BaseListener import BaseListener
from TransportLayer.TransportUtil import *

import helper
import service

logger = logging.getLogger('HAProxy-service')


class SslConfirmationListener(BaseListener):
    """

    """

    def __init__(self):
        """

        """
        # message queue configuration
        self.channel = os.environ.get("QUEUE_SSL_CONFIRMATION") + "." + helper.get_private_ip()
        self.destination_type = Constants.QUEUE_DESTINATION_TYPE
        self.destination = create_subscriber_destination(self.channel)

        # message processor initialize
        self.service = service.Service()
        super().__init__(self.destination_type, self.channel, self.destination)
        logger.info(
            '[SSL Confirmation Listener] Running [ %s ]' %self.destination_type
        )

    @asyncio.coroutine
    def message_listener(self, headers, body):
        """

        :param headers:
        :param body:
        :return:
        """
        logger.debug("[SSL Confirmation Listener] TL process message")
        yield from self.service.process_ssl_confirmation(body)
