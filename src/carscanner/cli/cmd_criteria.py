class CriteriaCommand:
    @staticmethod
    def build_argparse(subparsers):
        criteria_parser = subparsers.add_parser('criteria', aliases=['crit'], help='Manipulate criteria')
        criteria_parser.set_defaults(func=lambda _: criteria_parser.print_help())
        criteria_subparsers = criteria_parser.add_subparsers()

        def build(ctx):
            ctx.modify_static = True
            ctx.categories_svc().build_criteria()

        criteria_build_opt = criteria_subparsers.add_parser('build', help='Build criteria database')
        criteria_build_opt.set_defaults(func=build)
