import pathlib

from pyramid.request import Request
from pyramid.response import FileResponse


def index(request: Request):
    return FileResponse(pathlib.Path(__file__).parent / 'index.html', request=request)
