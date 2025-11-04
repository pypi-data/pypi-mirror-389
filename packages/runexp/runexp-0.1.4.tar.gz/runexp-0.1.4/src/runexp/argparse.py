import argparse
import itertools
import pathlib
import shlex
import sys
import typing

import psutil

from . import run_proc, slurm_utils
from .dry_run import DryRun
from .environment import env
from .parser_utils import Options, RunExpState, add_runexp_args
from .utils import unexpected_error

_PREFIX_SWEEP_ARG = "sweep-"
_PREFIX_SWEEP_DST = "sweep_"


def prohibit_prefix(action: argparse.Action, prefix: str):
    if action.dest.startswith(prefix):
        raise argparse.ArgumentError(
            action,
            f"prefix {prefix!r} is reserved by runexp",
        )


def check_action(action: argparse.Action):
    if action.dest == "help":
        return

    # make sure there are no reserved prefixes used in the parser
    for dest_prefix in Options.all_dest_prefixes():
        prohibit_prefix(action, dest_prefix)
    prohibit_prefix(action, _PREFIX_SWEEP_DST)


def add_sweep(parser: argparse.ArgumentParser, action: argparse.Action):
    label = argparse._get_action_name(action)
    parser.add_argument(
        f"--{_PREFIX_SWEEP_ARG}{action.dest}",
        type=str,  # list to split
        required=False,
        help=f"Sweep comma separated list of values for {label}",
        dest=f"{_PREFIX_SWEEP_DST}{action.dest}",
    )


def make_runexp_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    "create a new RunExp parser with appropriate sweep options"
    runexp_parser = argparse.ArgumentParser(parser.prog + "-runexp", add_help=False)

    for act in parser._actions:
        check_action(act)
        add_sweep(runexp_parser, act)
    add_runexp_args(runexp_parser)

    return runexp_parser


def sweep_as_dict(runexp_ns: argparse.Namespace) -> dict[str, list[str]]:
    "compute the sweep parameters for each relevant argument"
    sweep_dict = {}
    for attr, csl in vars(runexp_ns).items():
        if attr == _PREFIX_SWEEP_DST:
            raise RuntimeError(
                f"empty sweep parameter: {attr=!r}: this should not happen"
            )

        # not swept : the original parser should produce an error if no value are given
        if csl is None:
            continue

        if not attr.startswith(_PREFIX_SWEEP_DST):
            raise RuntimeError(
                f"parameter {attr!r} non recognized: this should not happen"
            )

        parameter_start = len(_PREFIX_SWEEP_DST)
        parameter = attr[parameter_start:]
        values = str(csl).split(",")
        sweep_dict[parameter] = values

    return sweep_dict


def sweep_values(sweep_dict: dict[str, list[str]]):
    def _parsed(str_: str):
        try:
            return int(str_)
        except ValueError:
            pass
        try:
            return float(str_)
        except ValueError:
            pass
        return str_

    sweep_values: dict[str, set] = {}
    for key, vals in sweep_dict.items():
        sweep_values[key] = set(map(_parsed, vals))

    # TODO move that later
    return {
        key: sorted(values) for key, values in sweep_values.items() if len(values) > 1
    }


def iter_sweep(sweep_dict: dict[str, list[str]]):
    "iterate all sweep configuration from dictionary of configurations per parameter"
    choices_len = map(len, sweep_dict.values())
    choices_idx_iter = itertools.product(*map(range, choices_len))

    def idx_to_param(indices: tuple[int, ...]):
        return {
            dest: value[idx]
            for ((dest, value), idx) in zip(sweep_dict.items(), indices)
        }

    yield from map(idx_to_param, choices_idx_iter)


def build_param(action: argparse.Action, param_value: typing.Any) -> list[str]:
    "compute the parts for '--name [val0 [val1 [...]]]'"
    key = action.option_strings[0]
    nargs = action.nargs

    if isinstance(action, argparse._StoreConstAction):
        # this includes _StoreTrue and _StoreCont
        if param_value == action.default:
            return []
        if param_value == action.const:
            return [key]
        raise ValueError(
            f"illegal value {param_value!r} for store_const {action.dest}: {action.const=!r} {action.default=!r}"
        )
    if isinstance(
        action,
        (
            argparse._AppendAction,
            argparse._AppendConstAction,
            argparse._CountAction,
            argparse._HelpAction,
            argparse._VersionAction,
            argparse._SubParsersAction,
            argparse._ExtendAction,
        ),
    ):
        raise NotImplementedError(f"{type(action)} is not implemented")
    elif not isinstance(action, (argparse._StoreAction)):
        # at the time of writing, these are the only possible cases
        # hopefully assert_type() help detect breaking changes rapidly
        raise unexpected_error("688fe69c-2afa-4a78-85e8-91834c4ec565")

    if not isinstance(action, argparse._StoreAction):
        raise unexpected_error("8f947c5a-2c83-413b-be40-fe8185eb8b00")

    if nargs == 0:
        # store actions must have nargs != 0 (per argparse doc)
        raise unexpected_error("44eee62e-4d1b-49ab-a63e-a6b870ff20d8")

    # length checking
    if isinstance(nargs, int):
        # input should be a list of adequate length
        if not hasattr(param_value, "__len__") or len(param_value) != nargs:
            raise ValueError(f"expected {nargs} values for {action}: {param_value!r}")
    elif nargs == "+":
        if not hasattr(param_value, "__len__") or len(param_value) < 1:
            raise ValueError(
                f"expected at least one value for {action}: {param_value!r}"
            )

    # --key val0 [val1 [...]]
    if nargs in ["+", "*"] or isinstance(nargs, int):
        return [key] + [str(v) for v in param_value]
    elif nargs == "?" or nargs is None:
        return [key, str(param_value)]
    else:
        raise ValueError(f"unexpected value for nargs ({nargs!r}): {action=!r}")


def build_command(parser: argparse.ArgumentParser, namespace: dict[str, typing.Any]):
    "inverse of ArgumentParser.parse: produce a command from a parser and a namespace"

    # NOTE This is simplistic and will likely need updates when the workflow gets more complex

    parts: list[str] = []
    done_keys: list[str] = []

    for action in parser._actions:
        # skip help
        if action.dest == "help":
            continue

        param_value = namespace.get(action.dest, None)

        # this is considered: even if it's not written
        done_keys.append(action.dest)

        # skip omitted optional values : it is not possible to pass None
        if param_value is None:
            if action.required:
                raise ValueError(f"missing a value for {action}")
            continue

        # print shorter command by removing the defaults
        if param_value == action.default:
            continue

        if action.option_strings:
            parts.extend(build_param(action, param_value))
        else:
            # positional argument : no key
            parts.append(str(param_value))

    assert set(done_keys) == set(namespace.keys())

    return parts


def run_no_sweep(
    cmd: list[str],
    name: str,
    state: RunExpState,
):

    if not state.use_slurm:
        if state.no_dry_run:
            run_proc.run_command(cmd)
        else:
            DryRun().print(shlex.join(cmd))
        return

    job_out_dir = state.valid_job_out_dir(state.no_dry_run, name, env.invocation_key())
    slurm_utils.run_slurm(
        state.template_file,
        job_out_dir,
        name,
        cmd,
        state.slurm_args,
        state.no_dry_run,
    )


def run_sweep(
    sweep_cmd_list: list[list[str]],
    name: str,
    state: RunExpState,
):
    job_out_dir = state.valid_job_out_dir(state.no_dry_run, name, env.invocation_key())

    if not state.use_slurm:
        if state.no_dry_run:
            commands = {
                job_out_dir / f"item-{idx}": cmd
                for idx, cmd in enumerate(sweep_cmd_list)
            }
            run_proc.run_multi(commands, max_concurrency=state.max_concurrent_proc)
        else:
            run = DryRun()
            for arg in sweep_cmd_list:
                run.print(shlex.join(arg))
        return

    if state.template_file is None:
        raise ValueError("slurm sweep are only implemented with template files")

    slurm_utils.run_slurm_array(
        sweep_cmd_list,
        state.max_concurrent_proc,
        state.template_file,
        job_out_dir,
        state.no_dry_run,
        name,
        state.slurm_args,
    )


def get_python_head_flags():
    "necessary flags for the system executable before any arguments"
    sys_args = sys.argv[1:]
    argc = len(sys_args)
    ps_args = psutil.Process().cmdline()[1:]

    if argc == 0:
        header, args = ps_args, []
    else:
        header, args = ps_args[:-argc], ps_args[-argc:]

    assert args == sys_args

    return header, args


class SkipRunExp(Exception):
    def __init__(self, *args: object, ret_args: argparse.Namespace) -> None:
        super().__init__(*args)
        self.ret_args = ret_args


def _parse(parser: argparse.ArgumentParser, args: list[str]):
    # detect if any RunExp options were used (slurm or sweep)
    runexp_parser = make_runexp_parser(parser)
    runexp_ns, remaining_args = runexp_parser.parse_known_args(args)
    runexp_state = RunExpState.pop_state(runexp_ns)  # removes specific fields as well

    # no runexp options, don't interfere with the program
    base_args = parser.parse_args(remaining_args)
    if len(remaining_args) == len(args):
        raise SkipRunExp(ret_args=base_args)

    base_cfg = vars(base_args)

    return runexp_ns, runexp_state, base_cfg


def parse(parser: argparse.ArgumentParser) -> argparse.Namespace | typing.NoReturn:
    # used for module, optimization, ..., target
    python_flags, args = get_python_head_flags()

    try:
        runexp_ns, runexp_state, base_cfg = _parse(parser, args)
    except SkipRunExp as skip:
        return skip.ret_args

    def _make_command(ns_: dict[str, typing.Any]):
        return [sys.executable] + python_flags + build_command(parser, ns_)

    # executed file
    name = parser.prog or pathlib.Path(sys.argv[0]).stem

    # build configs one by one
    sweep_dict = sweep_as_dict(runexp_ns)

    # simpler no-sweep config
    if not sweep_dict:
        run_no_sweep(
            _make_command(base_cfg),
            name,
            runexp_state,
        )
        exit(0)

    # sweep_vals = sweep_values(sweep_dict)

    # TODO build list here for wandb
    #   values are str by default, we could assume float/int
    #   bool flag sweep are not working atm...

    # build 1 command per config
    all_commands: list[list[str]] = []
    for param in iter_sweep(sweep_dict):
        # update the namespace
        new_cfg = {**base_cfg, **param}
        # rebuild the CLI command
        all_commands.append(_make_command(new_cfg))

    run_sweep(all_commands, name, runexp_state)
    exit(0)
