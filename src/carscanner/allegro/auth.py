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


class AuthorizationCodeAuth(allegro_pl.AllegroAuth):

    def __init__(self, cs: allegro_pl.ClientCodeStore, ts: allegro_pl.TokenStore, allow_fetch: bool = True):
        """
        :param allow_fetch: If True, when both access_token and refresh token are not present or expired, start OAuth2
            flow to get them. This will start a web server to allow the redirect from authentication server.
        """
        super().__init__(cs, ts)

        client = oauthlib.oauth2.WebApplicationClient(self._cs.client_id, access_token=self._token_store.access_token)

        self.oauth = requests_oauthlib.OAuth2Session(self._cs.client_id, client, allegro_pl.URL_TOKEN,
                                                     redirect_uri=URL_CALLBACK,
                                                     token_updater=self._token_store.access_token)
        self._allow_fetch = allow_fetch

    def fetch_token(self):
        if not self._allow_fetch:
            raise Exception('Fetching token disabled')

        super().fetch_token()
        cherrypy.tree.mount(
            WebAuth(self._cs.client_id, self._cs.client_secret, self.oauth, self._on_token_updated))

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
            token = self.oauth.refresh_token(url, auth=HTTPBasicAuth(self._cs.client_id,
                                                                     self._cs.client_secret))
            self._on_token_updated(token)
        except oauthlib.oauth2.rfc6749.errors.OAuth2Error as x:
            logger.warning('Refresh token failed', x.error)
            if x.description == 'Full authentication is required to access this resource' \
                    or x.description.startswith('Invalid refresh token: ') \
                    or x.error == 'invalid_token':
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
    def __init__(self, path: str = None):
        if path is None:
            path = carscanner.allegro.token_path
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


class YamlClientCodeStore(allegro_pl.ClientCodeStore):
    def __init__(self, path=None):
        if path is None:
            path = carscanner.allegro.codes_path
        with open(path, 'rt') as f:
            d = yaml.safe_load(f)
            super().__init__(d['client_id'], d['client_secret'])


class EnvironClientCodeStore(allegro_pl.ClientCodeStore):
    def __init__(self):
        super().__init__(os.environ['ALLEGRO_CLIENT_ID'], os.environ['ALLEGRO_CLIENT_SECRET'])
