class VoivodeshipCommand:
    @staticmethod
    def build_argparse(subparsers):
        vs_parser = subparsers.add_parser('voivodeship', help='Manipulate voivodeship database')
        vs_parser.set_defaults(func=lambda _: vs_parser.print_help())
        vs_subparsers = vs_parser.add_subparsers()

        def load(ctx):
            ctx.modify_static = True
            ctx.voivodeship_svc().load_voivodeships()

        vs_load_cmd = vs_subparsers.add_parser('load')
        vs_load_cmd.set_defaults(func=load)

