from pyramid.request import Request
from pyramid.request import Response


def request_factory(environ):
    request = Request(environ)
    if request.is_xhr:
        header_list = [
            ('Access-Control-Allow-Origin', '*'),
        ]

        request.response = Response(headerlist=header_list)
    return request
