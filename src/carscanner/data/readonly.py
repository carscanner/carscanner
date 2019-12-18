import logging

import tinydb.middlewares

logger = logging.getLogger(__name__)


class ReadOnlyMiddleware(tinydb.middlewares.Middleware):
    def __init__(self, storage_cls=tinydb.TinyDB.DEFAULT_STORAGE):
        super(ReadOnlyMiddleware, self).__init__(storage_cls)

    def write(self, _):
        logger.debug('Read-only, ignoring write() call.')
