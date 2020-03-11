from asyncio import Future

import allegro_pl
from pyramid.request import Request
from pyramid.response import Response

from carscanner.web.heroku_context import HerokuContext


class DataGatherService:
    def __init__(self):
        self._running = False

    def run(self, context, request: Request):
        if self._running:
            return Response('<body>Already running</body>', content_type='text/html')

        self._running = True

        ctx = HerokuContext()

        def update():
            try:
                ctx.executor().submit(ctx.vehicle_updater().update)
            except allegro_pl.TokenError as x:
                print('Invalid token, fetch disabled. Exiting', x.args)
                raise
            ctx.close()
            self._running = False

        f: Future = ctx.executor().submit(update)

        if f.done():
            return Response('<body>Probably failed</body>', content_type='text/html')
        else:
            return Response('<body>Started</body>', content_type='text/html')
