import codecs
import logging

import tinydb

logger = logging.getLogger(__name__)


class JSONStorageReadOnly(tinydb.JSONStorage):
    """
    Store the data in a JSON file.
    """

    def __init__(self, path, encoding=None):
        """
        Create a new instance.
        :param path: Where to store the JSON data.
        :type path: str
        """

        super(tinydb.JSONStorage, self).__init__()
        self._handle = codecs.open(path, 'r', encoding=encoding)

    def write(self, data):
        logger.debug('Read-only, ignoring write() call.')
