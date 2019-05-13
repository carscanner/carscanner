import logging

import tinydb.middlewares

logger = logging.getLogger(__name__)


class ReadOnlyMiddleware(tinydb.middlewares.Middleware):
    def write(self, _):
        logger.debug('Read-only, ignoring write() call.')
