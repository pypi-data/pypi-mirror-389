import argparse
import enum
import shlex
import pathlib

from pydantic import dataclasses


class Options(enum.Enum):
    "some reserved prefix"

    SLURM = "runexp-slurm"
    NO_DRY = "runexp-no-dry-run"
    SLURM_ARG = "runexp-slurm-verbatim"
    TEMPLATE_SLURM = "runexp-slurm-template"
    MAX_CONCURRENT_SWEEP = "runexp-max-concurrent-sweep"
    JOB_OUT_DIR = "runexp-job-out-dir"

    @property
    def arg(self) -> str:
        "formatted as --option"
        return "--" + self.value

    @property
    def dest(self) -> str:
        "key in the namespace"
        return self.value.replace("-", "_")

    @staticmethod
    def all_dest_prefixes():
        return [p.dest for p in Options]


@dataclasses.dataclass
class RunExpState:
    use_slurm: bool
    no_dry_run: bool
    slurm_args: list[str]
    template_file: pathlib.Path | None
    max_concurrent_proc: int | None
    job_out_dir: pathlib.Path

    @staticmethod
    def pop_state(ns: argparse.Namespace):
        "remove runexp attributes from the namespace and return the parsed state"

        # optional args first
        template_path = None
        if hasattr(ns, Options.TEMPLATE_SLURM.dest):
            path = getattr(ns, Options.TEMPLATE_SLURM.dest)
            if path:
                template_path = pathlib.Path(path)
            delattr(ns, Options.TEMPLATE_SLURM.dest)

        job_out_dir = pathlib.Path(getattr(ns, Options.JOB_OUT_DIR.dest))

        # needs a bit of processing
        args_verbatim = getattr(ns, Options.SLURM_ARG.dest)
        args = [] if not args_verbatim else shlex.split(args_verbatim)

        state = RunExpState(
            use_slurm=getattr(ns, Options.SLURM.dest) or template_path is not None,
            no_dry_run=getattr(ns, Options.NO_DRY.dest),
            slurm_args=args,
            template_file=template_path,
            max_concurrent_proc=getattr(ns, Options.MAX_CONCURRENT_SWEEP.dest),
            job_out_dir=job_out_dir,
        )

        delattr(ns, Options.SLURM.dest)
        delattr(ns, Options.NO_DRY.dest)
        delattr(ns, Options.SLURM_ARG.dest)
        delattr(ns, Options.MAX_CONCURRENT_SWEEP.dest)
        delattr(ns, Options.JOB_OUT_DIR.dest)

        return state

    def valid_job_out_dir(self, no_dry_run: bool, *suffix: str) -> pathlib.Path:
        "creates job_out_dir (but not the parent) if it doesn't exist"
        if suffix:
            path = self.job_out_dir
            for s in suffix:
                path = path / s

            # this will raise a ValueError if path is not a subdir (e.g. suffix is '..')
            path.relative_to(self.job_out_dir)
        else:
            path = self.job_out_dir

        if not no_dry_run:
            if not self.job_out_dir.parent.exists():
                raise ValueError(f"parent of {self.job_out_dir} should exist")
        else:
            self.job_out_dir.mkdir(exist_ok=True)
            if path != self.job_out_dir:
                path.mkdir(parents=True)
        return path


def remove_runexp_args(args: list[str]) -> list[str]:
    "return a copy of args without runexp general arguments"

    bad_indices: list[int] = []
    for idx, arg in enumerate(args):
        if not arg.startswith("--"):
            continue

        # key-value options
        if arg in [
            Options.SLURM_ARG.arg,
            Options.TEMPLATE_SLURM.arg,
            Options.MAX_CONCURRENT_SWEEP.arg,
            Options.JOB_OUT_DIR.arg,
        ]:
            bad_indices += [idx, idx + 1]

        # flag options
        if arg in [Options.SLURM.arg, Options.NO_DRY.arg]:
            bad_indices += [idx]

    return [a for i, a in enumerate(args) if i not in bad_indices]


def add_runexp_args(runexp_parser: argparse.ArgumentParser):
    # add an option to run with slurm
    runexp_parser.add_argument(
        Options.SLURM.arg,
        action="store_true",
        help="Use a SLURM job for the execution (or job array for a sweep)",
        dest=Options.SLURM.dest,
    )

    runexp_parser.add_argument(
        Options.NO_DRY.arg,
        action="store_true",
        help="Run the command instead of only printing it",
        dest=Options.NO_DRY.dest,
    )

    runexp_parser.add_argument(
        Options.SLURM_ARG.arg,
        type=str,
        default="",
        help="Arguments passed to slurm verbatim",
        dest=Options.SLURM_ARG.dest,
    )

    runexp_parser.add_argument(
        Options.TEMPLATE_SLURM.arg,
        type=str,
        help="Template file for the job.sh (see doc for more instructions)",
        dest=Options.TEMPLATE_SLURM.dest,
    )

    runexp_parser.add_argument(
        Options.MAX_CONCURRENT_SWEEP.arg,
        type=int,
        help="Number of concurrent processes to run sweep on. Ignored if no sweep are run",
        dest=Options.MAX_CONCURRENT_SWEEP.dest,
    )

    runexp_parser.add_argument(
        Options.JOB_OUT_DIR.arg,
        type=str,
        default=str(pathlib.Path.cwd() / ".runexp"),
        help="Directory where output files will be copied",
        dest=Options.JOB_OUT_DIR.dest,
    )
