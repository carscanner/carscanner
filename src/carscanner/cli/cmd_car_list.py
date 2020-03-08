import pathlib

from carscanner.cli.cmd_context import CmdContext


class CarListCommand:
    @staticmethod
    def build_argparse(subparsers):
        carlist_cmd = subparsers.add_parser('carlist', help='Manipulate car makes & models list')
        carlist_cmd.set_defaults(func=lambda _: carlist_cmd.print_help())
        carlist_subparsers = carlist_cmd.add_subparsers()

        def update(ctx: CmdContext):
            ctx.modify_static = True
            ctx.car_makemodel_svc().load_car_list(ctx.ns.input)

        carlist_update_cmd = carlist_subparsers.add_parser('update', help='Load car makes & models from json file to '
                                                                          'the database')
        carlist_update_cmd.set_defaults(func=update)
        carlist_update_cmd.add_argument('--input', '-i', type=pathlib.Path, help='Input json file', metavar='path')

        carlist_show_cmd = carlist_subparsers.add_parser('show')
        carlist_show_cmd.set_defaults(func=lambda ctx: ctx.car_makemodel_svc().show_car_list())

