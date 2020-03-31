import argparse
from unittest import TestCase

from pytel import Pytel

from carscanner.cli.cmd_context import CmdContext
from carscanner.context import Context, Config


class TestContext(TestCase):
    def test_init(self) -> None:
        p = Pytel([Context(), CmdContext(argparse.Namespace()), {'config': Config()}])
