import logging
import os

import pytel
from pyramid.config import Configurator
from waitress import serve

from carscanner.utils import configure_logging
from carscanner.web.views import index, gather, search_vehicles as search
from carscanner.context import Config, Context
from carscanner.web.heroku_context import HerokuContext

log = logging.getLogger(__name__)

if __name__ == '__main__':
    configure_logging()
    log.info('starting...')
    configurators = [
        Context(),
        HerokuContext(),
        {
            'config': Config(),
            'gather': gather,
            'search': search,
        }
    ]
    with pytel.Pytel(configurators) as context:
        with Configurator() as config:
            config.include('pyramid_debugtoolbar')

            config.add_route('gather', '/gather')
            config.add_view(context.gather, route_name='gather')

            config.add_route('index', '/hello')
            config.add_view(index, route_name='index')

            config.add_route('search', '/search')
            config.add_view(context.search, route_name='search', renderer='json')

            config.registry

            app = config.make_wsgi_app()
        serve(app, host='0.0.0.0', port=os.environ.get('PORT', '5000'))
