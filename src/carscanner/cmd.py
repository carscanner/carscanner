import argparse

import carscanner.allegro
from carscanner.allegro.auth import InsecureTokenStore, AuthorizationCodeAuth, TravisTokenStore
from carscanner.make_model import load_car_list


class CommandLine:
    def __init__(self):
        parser = argparse.ArgumentParser()
        subparser = parser.add_subparsers()

        token_parser = subparser.add_parser('token', help='token actions')
        token_subparsers = token_parser.add_subparsers()
        token_parser.add_argument('--format', nargs='?', default='yaml', choices=['yaml', 'travis'],
                                  help='Where to save file to. One of %(choices)s. Default is %(default)s',
                                  metavar='format')

        token_refresh_parser = token_subparsers.add_parser('refresh', help='refresh token')
        token_refresh_parser.set_defaults(func=self.token_refresh)

        token_fetch_opt = token_subparsers.add_parser('fetch', help='fetch token')
        token_fetch_opt.set_defaults(func=self.token_fetch)

        car_list_opt = subparser.add_parser('carlist')
        car_list_opt.set_defaults(func=self.load_car_list)
        car_list_opt.add_argument('path', help='Input json file', metavar='path')

        args = parser.parse_args()
        args.func(**vars(args))

    def _get_oauth(self, format):
        if format == 'yaml':
            ts = InsecureTokenStore(carscanner.allegro.token_path)
        elif format == 'travis':
            ts = TravisTokenStore()
        else:
            raise ValueError(format)
        codes = carscanner.allegro.auth.get_codes()
        return AuthorizationCodeAuth(codes['client_id'], codes['client_secret'], ts)

    def token_refresh(self, format, **_):
        self._get_oauth(format).refresh_token()

    def token_fetch(self, format, **_):
        self._get_oauth(format).fetch_token()

    def load_car_list(self, path, **_):
        load_car_list(path)


if __name__ == '__main__':
    carscanner.configure_logging()
    CommandLine()
