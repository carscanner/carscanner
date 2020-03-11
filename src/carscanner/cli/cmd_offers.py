class OffersCommand:
    @staticmethod
    def build_argparse(subparsers):
        offers_parser = subparsers.add_parser('offers', help='Manipulate offers')
        offers_parser.set_defaults(func=lambda _: offers_parser.print_help())
        offers_subparsers = offers_parser.add_subparsers()

        offers_update_opt = offers_subparsers.add_parser('update', help='Update and export current offers')
        offers_update_opt.set_defaults(func=lambda ctx: ctx.vehicle_updatóer().update())

        offers_export_opt = offers_subparsers.add_parser('export')
        offers_export_opt.set_defaults(func=lambda ctx: ctx.offer_export_svc().export(ctx.data_path / 'export.json'))
