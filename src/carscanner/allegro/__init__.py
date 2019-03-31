import os

import allegro_pl

from .auth import AuthorizationCodeAuth, InsecureTokenStore, get_codes


def get_root():
    root_var = '~/.allegro'
    root = os.path.expanduser(root_var)
    auth_dir = os.path.join(root, 'auth')
    if not os.path.exists(root):
        os.mkdir(root, 0o700)
        os.mkdir(auth_dir)
    return root, auth_dir


root, auth_dir = get_root()
codes_path = os.path.join(auth_dir, 'allegro.yaml')
token_path = os.path.join(auth_dir, 'insecure-tokens.yaml')


def get_client() -> allegro_pl.Allegro:
    client_id = os.environ.get('ALLEGRO_CLIENT_ID')
    client_secret = os.environ.get('ALLEGRO_CLIENT_SECRET')
    if not client_id and not client_secret:
        codes = get_codes()
        if client_id is None: client_id = codes['client_id']
        if client_secret is None: client_secret = codes['client_secret']

    auth = AuthorizationCodeAuth(client_id, client_secret, InsecureTokenStore(token_path))
    return allegro_pl.Allegro(auth)
