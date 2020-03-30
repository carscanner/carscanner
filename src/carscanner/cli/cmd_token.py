class TokenCommand:
    @staticmethod
    def build_argparse(subparsers):
        token_parser = subparsers.add_parser('token', help='Manipulate security tokens')
        token_parser.set_defaults(func=lambda _: token_parser.print_help())
        token_subparsers = token_parser.add_subparsers()

        token_refresh_parser = token_subparsers.add_parser('refresh', help='Refresh token')
        token_refresh_parser.set_defaults(func=lambda ctx: ctx.allegro_auth.refresh_token())

        token_fetch_opt = token_subparsers.add_parser('fetch', help='Fetch token')
        token_fetch_opt.set_defaults(func=lambda ctx: ctx.allegro_auth.fetch_token())

