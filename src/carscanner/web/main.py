from pyramid.config import Configurator
from waitress import serve
import os

if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('gather', '/gather')
        config.scan('carscanner.web.views')
        app = config.make_wsgi_app()
    serve(app, host='0.0.0.0', port=os.environ['PORT'])
