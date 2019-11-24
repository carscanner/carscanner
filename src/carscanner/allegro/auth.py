import logging
import os
import pathlib
import typing

import allegro_pl
import cherrypy
import oauthlib.oauth2
import requests_oauthlib
import yaml

URL_CALLBACK = 'http://localhost:8080/callback'

logger = logging.getLogger(__name__)


class CarScannerCodeAuth(allegro_pl.AuthorizationCodeAuth):
    def __init__(self, cs: allegro_pl.ClientCodeStore, ts: allegro_pl.TokenStore, allow_fetch: bool = True):
        """
        :param allow_fetch: If True, when both access_token and refresh token are not present or expired, start OAuth2
            flow to get them. This will start a web server to allow the redirect from authentication server.
        """
        super().__init__(cs, ts, URL_CALLBACK)
        self._allow_fetch = allow_fetch

    def fetch_token(self):
        logger.debug('Fetch token')
        if not self._allow_fetch:
            raise allegro_pl.TokenError('Fetching token disabled')

        cherrypy.tree.mount(
            WebAuth(self._cs.client_secret, self._oauth, allegro_pl.URL_AUTHORIZE, allegro_pl.URL_TOKEN,
                    self._on_token_updated))

        cherrypy.engine.start()
        cherrypy.engine.block()

    def _on_token_updated(self, token):
        super()._on_token_updated(token)
        states = cherrypy.engine.states
        if cherrypy.engine.state not in [states.STOPPED, states.STOPPING, states.EXITING]:
            cherrypy.engine.exit()


class WebAuth:
    def __init__(self, client_secret: str, oauth: requests_oauthlib.OAuth2Session, authorize_uri: str, token_url: str,
                 callback: typing.Callable[[dict], None] = None):
        self._client_secret = client_secret
        self._oauth_session = oauth
        self._authorize_uri = authorize_uri
        self._token_url = token_url
        self._callback = callback
        self._state: typing.Optional[str] = None

    @cherrypy.expose
    def index(self):
        authorization_url, state = self._oauth_session.authorization_url(self._authorize_uri)
        self._oauth_session._state = state
        raise cherrypy.HTTPRedirect(authorization_url)

    @cherrypy.expose
    def callback(self, code, state):
        url = cherrypy.url(qs=cherrypy.request.query_string).replace('http:', 'https:', 1)

        try:
            token: dict = self._oauth_session.fetch_token(self._token_url, authorization_response=url,
                                                          client_secret=self._client_secret)
            self._callback(token)
        except oauthlib.oauth2.rfc6749.errors.OAuth2Error as x:
            return 'error' + str(x)

        return 'OK'


class InsecureTokenStore(allegro_pl.TokenStore):
    def __init__(self, path: pathlib.Path):
        super().__init__()
        self._path = path
        try:
            with open(path, 'rt') as f:
                self.update_from_dict(yaml.safe_load(f))
        except FileNotFoundError as x:
            logger.debug('%s %s', x.strerror, x.filename)
        except OSError as x:
            logger.debug('Could not read token file', x)

    def save(self):
        logger.debug('Save tokens')
        with open(self._path, 'wt') as f:
            yaml.safe_dump(self.to_dict(), f)


class YamlClientCodeStore(allegro_pl.ClientCodeStore):
    def __init__(self, path: pathlib.Path = pathlib.Path('~/.carscanner/allegro.yaml').expanduser()):
        with open(path, 'rt') as f:
            d = yaml.safe_load(f)
            super().__init__(d['client_id'], d['client_secret'])


class EnvironClientCodeStore(allegro_pl.ClientCodeStore):
    KEY_CLIENT_ID = 'ALLEGRO_CLIENT_ID'
    KEY_CLIENT_SECRET = 'ALLEGRO_CLIENT_SECRET'

    def __init__(self):
        super().__init__(os.environ[EnvironClientCodeStore.KEY_CLIENT_ID],
                         os.environ[EnvironClientCodeStore.KEY_CLIENT_SECRET])
