import os
import shlex
import sys

import psutil

from . import parser_utils


class DryRun:
    def __init__(self, file=sys.stdout) -> None:
        args = psutil.Process(os.getpid()).cmdline()
        no_dry_arg = parser_utils.Options.NO_DRY.arg
        # add --runexp-no-dry-run (only if not present)
        if no_dry_arg in args:
            raise RuntimeError(f"{no_dry_arg} has been specified, a {type(self)} object should not have been created")

        self.content = [
            "=== DRY RUN ===",
            "run the command below for an actual execution",
            shlex.join(args + [no_dry_arg]),
            "==============="
        ]
        self.file = file

    def print(self, arg: str):
        if self.content:
            for line in self.content:
                print(line, file=self.file)
            self.content = []

        print(arg, file=self.file)
