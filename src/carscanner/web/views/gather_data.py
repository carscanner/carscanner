import logging
from asyncio import Future

import allegro_pl
import pytel
from pyramid.request import Request
from pyramid.response import Response

from carscanner.context import Config, Context
from carscanner.web.heroku_context import HerokuContext

log = logging.getLogger(__name__)


class DataGatherService:
    def __init__(self):
        self._running = False

    def run(self, context, request: Request):
        if self._running:
            return Response('<body>Already running</body>', content_type='text/html')

        self._running = True

        ctx = pytel.Pytel([Context(), HerokuContext(), {'config': Config()}])

        def update():
            log.info('update called')
            try:
                ctx.vehicle_updater_svc.update()
            except allegro_pl.TokenError:
                log.error('Invalid token, fetch disabled. Exiting.', exc_info=True)
            except BaseException:
                log.error("Error occurred", exc_info=True)
            finally:
                self._running = False
                ctx.close()

        f: Future = ctx.executor.submit(update)

        if f.done():
            if e := f.exception():
                return Response('<body>' + str(e) + '</body>', content_type='text/html')
            else:
                return Response('<body>finished (?)</body>', content_type='text/html')

        else:
            return Response('<body>Started</body>', content_type='text/html')
