import argparse
import json
import sys

from carscanner.cli.cmd_context import CmdContext


class FilterCommand:
    @staticmethod
    def build_argparse(subparsers):
        filter_parser = subparsers.add_parser('filter', help='Manipulate category filters')
        filter_parser.set_defaults(func=lambda _: filter_parser.print_help())
        filter_subparsers = filter_parser.add_subparsers()

        filter_show_cmd: argparse.ArgumentParser = filter_subparsers.add_parser('get')
        filter_show_cmd.add_argument('--category', '-c', default='ALL', help='Category id. Default is all categories')
        filter_show_cmd.add_argument('--output', '-o', default='-', help='Output file. use - to output to the standard '
                                                                         'output (the default)')
        filter_show_cmd.set_defaults(func=lambda ctx: FilterCommand.get(ctx))

    @staticmethod
    def get(ctx: CmdContext):
        output_path = ctx.ns.output
        cat_id = ctx.ns.category

        def to_dict(o):
            return o.to_dict()

        try:
            if output_path == '-':
                output = sys.stdout
            else:
                output = open(output_path, 'wt')

            cat_ids = [cat_id] if cat_id != 'ALL' else [c.category_id for c in ctx.criteria_dao().all()]

            result = {cat_id: ctx.allegro().get_filters(cat_id) for cat_id in cat_ids}
            json.dump(result, output, default=to_dict, indent=2)
        finally:
            if output and output is not sys.stdout:
                output.close()
