import argparse
import logging
import pathlib

import allegro_pl
import pytel

import carscanner
import carscanner.utils
from carscanner.cli import CarListCommand, CriteriaCommand, FilterCommand, OffersCommand, VoivodeshipCommand, \
    TokenCommand
from carscanner.context import ENV_LOCAL, ENV_TRAVIS, Context, Config

log = logging.getLogger(__name__)


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', '-d', default='.', type=pathlib.Path, metavar='dir',
                        help='Database directory. Default is %(default)s')
    parser.add_argument('--environment', '-e', default=ENV_LOCAL, choices=[ENV_LOCAL, ENV_TRAVIS], metavar='env',
                        help='Where to read client codes from. One of %(choices)s. Default is %(default)s')
    parser.add_argument('--no-fetch', '--nf', action='store_true', default=False,
                        help="Don't fetch token if it's expired")
    parser.add_argument('--version', '-v', action='version', version=carscanner.__version__)
    subparsers = parser.add_subparsers()

    for c in [
        CarListCommand,
        CriteriaCommand,
        FilterCommand,
        OffersCommand,
        TokenCommand,
        VoivodeshipCommand,
    ]:
        c.build_argparse(subparsers)

    return parser


def main():
    ns = build_parser().parse_args()
    if ns.data:
        ns.data = ns.data.expanduser()
    log.info("Starting")

    config = Config()
    config.allow_fetch = ns.environment == ENV_LOCAL

    with pytel.Pytel([
        Context(), {
            'config': config,
            'ns': ns,
            'offers_cmd': OffersCommand,
        }
    ]) as context:

        context.migration_service.check_migrate()

        try:
            ns.func(context)
        except allegro_pl.TokenError as x:
            print('Invalid token, fetch disabled. Exiting', x.args)
            raise


if __name__ == '__main__':
    carscanner.utils.configure_logging()
    main()
