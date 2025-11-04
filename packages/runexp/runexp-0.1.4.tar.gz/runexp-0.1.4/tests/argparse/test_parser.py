import argparse
import unittest

import runexp


class TestParser(unittest.TestCase):
    def test_ok(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=float)
        self.assertRaises(
            runexp.argparse.SkipRunExp,
            runexp.argparse._parse,
            parser,
            ["--a", "3.0"],
        )

        _, _, cfg = runexp.argparse._parse(parser, ["--a", "3.0", "--runexp-slurm"])
        self.assertEqual(cfg["a"], 3.0)

        ns, _, cfg = runexp.argparse._parse(parser, ["--sweep-a", "3.0,4.0",])
        self.assertIsNone(cfg["a"])
        self.assertEqual(getattr(ns, "sweep_a"), "3.0,4.0")

        sweep_dict = runexp.argparse.sweep_as_dict(ns)
        self.assertEqual(sweep_dict["a"], ["3.0", "4.0"])

    def test_prohibited(self):
        parser_l = argparse.ArgumentParser()
        parser_l.add_argument("--a", type=float)
        parser_l.add_argument("--sweep-a")
        self.assertRaises(argparse.ArgumentError, runexp.argparse._parse, parser_l, ["--a", "3.0", "--runexp-slurm"])

        parser_r = argparse.ArgumentParser()
        parser_r.add_argument("--a", type=float)
        parser_r.add_argument("--sweep_a")
        self.assertRaises(argparse.ArgumentError, runexp.argparse._parse, parser_r, ["--a", "3.0", "--runexp-slurm"])

        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=float)
        parser.add_argument("sweep_a")
        self.assertRaises(argparse.ArgumentError, runexp.argparse._parse, parser, ["3.0,4.0", "--runexp-slurm"])

        # this is actually OK : runexp only ever looks at getattr(ns, "sweep_a") so we don't care about getattr(ns, "sweep-a")
        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=float)
        parser.add_argument("sweep-a")
        runexp.argparse._parse(parser, ["3.0,3.0", "--runexp-slurm"])

        # runexp flags are not allowed either
        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=float)
        parser.add_argument("runexp_slurm")
        self.assertRaises(
            argparse.ArgumentError,
            runexp.argparse._parse,
            parser,
            ["--a", 3.0]
        )

        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=float)
        parser.add_argument("--runexp-slurm")
        self.assertRaises(
            argparse.ArgumentError,
            runexp.argparse._parse,
            parser,
            ["--a", 3.0]
        )

        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=float)
        parser.add_argument("--runexp_slurm")
        self.assertRaises(
            argparse.ArgumentError,
            runexp.argparse._parse,
            parser,
            ["--a", 3.0]
        )


if __name__ == "__main__":
    unittest.main()
