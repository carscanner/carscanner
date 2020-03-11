import os

from pyramid.config import Configurator
from waitress import serve

from carscanner.utils import configure_logging
from carscanner.web.views import index, DataGatherService

if __name__ == '__main__':
    configure_logging()
    with Configurator() as config:
        config.include('pyramid_debugtoolbar')
        config.add_route('gather', '/gather')
        config.add_view(DataGatherService().run, route_name='gather')

        config.add_route('index', '/hello')
        config.add_view(index, route_name='index')

        app = config.make_wsgi_app()
    serve(app, host='0.0.0.0', port=os.environ['PORT'])
