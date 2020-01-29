import importlib_resources
import tinydb


class ResourceStorage(tinydb.JSONStorage):
    def __init__(self, package, resource, encoding=None, **kwargs):
        """
        Create a new instance.

        :param path: Where to store the JSON data.
        :type path: str

        :raise ValueError: if the file doesn't exist
        """

        super(tinydb.JSONStorage, self).__init__()

        self.kwargs = kwargs
        self._handle = importlib_resources.open_text(package, resource, encoding)
