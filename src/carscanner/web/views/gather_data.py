import logging
import typing
from asyncio import Future
from concurrent import futures

import allegro_pl
from pyramid.response import Response

from carscanner.service import VehicleUpdaterService

log = logging.getLogger(__name__)


def gather(
        executor: futures.ThreadPoolExecutor,
        vehicle_updater_svc: VehicleUpdaterService,
) -> typing.Callable:
    _running = False

    def run(*_):
        nonlocal _running
        if _running:
            return Response('<body>Already running</body>', content_type='text/html')

        _running = True

        def update():
            log.info('update called')
            try:
                vehicle_updater_svc.update()
            except allegro_pl.TokenError:
                log.error('Invalid token, fetch disabled. Exiting.', exc_info=True)
            except BaseException:
                log.error("Error occurred", exc_info=True)
            finally:
                nonlocal _running
                _running = False

        f: Future = executor.submit(update)

        if f.done():
            if e := f.exception():
                return Response('<body>' + str(e) + '</body>', content_type='text/html')
            else:
                return Response('<body>finished (?)</body>', content_type='text/html')

        else:
            return Response('<body>Started</body>', content_type='text/html')

    return run
