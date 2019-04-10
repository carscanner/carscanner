import logging
import os
import pprint
import typing
from urllib.parse import urlencode

import allegro_pl
import cherrypy
import oauthlib.oauth2
import requests_oauthlib
import yaml
from requests.auth import HTTPBasicAuth

import carscanner
import carscanner.allegro

_REFRESH_TOKEN = 'refresh_token'
URL_CALLBACK = 'http://127.0.0.1:8080/callback'
URL_AUTHORIZE = 'https://allegro.pl/auth/oauth/authorize'

logger = logging.getLogger(__name__)


def get_codes() -> dict:
    with open(carscanner.allegro.codes_path, 'rt') as f:
        return yaml.safe_load(f)


class AuthorizationCodeAuth(allegro_pl.AllegroAuth):

    def __init__(self, client_id, client_secret, ts: allegro_pl.TokenStore):
        super().__init__(client_id, client_secret, ts)

        client = oauthlib.oauth2.WebApplicationClient(self.client_id, access_token=self._token_store.access_token)

        self.oauth = requests_oauthlib.OAuth2Session(self.client_id, client, allegro_pl.URL_TOKEN,
                                                     redirect_uri=URL_CALLBACK,
                                                     token_updater=self._token_store.access_token)

    def fetch_token(self):
        super().fetch_token()
        cherrypy.tree.mount(WebAuth(self.client_id, self.client_secret, self.oauth, self._on_token_updated))

        cherrypy.engine.start()
        cherrypy.engine.block()

    def _on_token_updated(self, token):
        super()._on_token_updated(token)
        if cherrypy.engine.state != cherrypy.engine.states.STOPPED:
            cherrypy.engine.exit()

    def refresh_token(self):
        logger.debug('refreshing token')
        try:
            # OAuth2 takes data in the body, but allegro expects it in the query
            url = allegro_pl.URL_TOKEN + '?' + urlencode(
                {'grant_type': 'refresh_token',
                 'refresh_token': self.token_store.refresh_token,
                 'redirect_uri': URL_CALLBACK
                 })
            token = self.oauth.refresh_token(url, auth=HTTPBasicAuth(self.client_id,
                                                                     self.client_secret))
            self._on_token_updated(token)
        except oauthlib.oauth2.rfc6749.errors.OAuth2Error as x:
            logger.warn('Refresh token failed')
            if x.description == 'Full authentication is required to access this resource' \
                    or x.description.startswith('Invalid refresh token: '):
                self.fetch_token()
            else:
                raise


class WebAuth:
    def __init__(self, client_id, client_secret, oauth: requests_oauthlib.OAuth2Session,
                 callback: typing.Callable[[dict], None] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self._oauth_session = oauth
        self._callback = callback
        self._state: typing.Optional[str] = None

    @cherrypy.expose
    def index(self):
        authorization_url, state = self._oauth_session.authorization_url(URL_AUTHORIZE)
        self._oauth_session._state = state
        raise cherrypy.HTTPRedirect(authorization_url)

    @cherrypy.expose
    def callback(self, code, state):
        url = cherrypy.url(qs=cherrypy.request.query_string).replace('http:', 'https:', 1)

        try:
            token: dict = self._oauth_session.fetch_token(allegro_pl.URL_TOKEN,
                                                          authorization_response=url,
                                                          client_secret=self.client_secret)
            self._callback(token)
        except oauthlib.oauth2.rfc6749.errors.OAuth2Error as x:
            pprint.pprint(x)
            return 'error' + str(x)

        return 'OK'


class InsecureTokenStore(allegro_pl.TokenStore):
    def __init__(self, path: str = 'insecure-tokens.yaml'):
        super().__init__()
        self._path = path
        with open(path, 'rt') as f:
            self.update_from_dict(yaml.safe_load(f))

    def save(self):
        super().save()
        with open(self._path, 'wt') as f:
            yaml.safe_dump(self.to_dict(), f)


class TravisTokenStore(allegro_pl.TokenStore):
    KEY_REFRESH_TOKEN = 'ALLEGRO_REFRESH_TOKEN'

    def __init__(self):
        super().__init__()
        self.refresh_token = os.environ.get(TravisTokenStore.KEY_REFRESH_TOKEN)

    def save(self):
        """ encrypt token and store it in .travis.yml file"""
        raise NotImplementedError
