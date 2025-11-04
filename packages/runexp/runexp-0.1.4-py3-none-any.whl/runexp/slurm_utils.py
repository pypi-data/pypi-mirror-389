"""

- make a slurm invocation
- create job-file from a template

"""


import contextlib
import pathlib
import shlex
import subprocess
import tempfile

from .dry_run import DryRun
from .environment import env


__JOB_OUT_DIR = "runexp-job-out-dir"
__JOB_NAME = "runexp-job-name"
__JOB_COMMAND = "runexp-command"
__JOB_OPTIONS = "runexp-sbatch-options"


def unique(path: pathlib.Path, idx_start: int = 1):
    if not path.exists():
        return path

    stem: str = path.stem

    i = idx_start - 1
    while True:
        i += 1
        new_path = path.with_stem(stem + f"-{i}")
        if not new_path.exists():
            return new_path


def write_job_file(job_data: str, path: pathlib.Path, no_dry_run: bool):
    if no_dry_run:
        destination_path = str(unique(path))
        should_remove = False
    else:
        _, destination_path = tempfile.mkstemp(".sh", "runexp-slurm-job", text=True)
        should_remove = True

    with open(destination_path, "w", encoding="utf8") as job_file:
        job_file.write(job_data)

    return destination_path, should_remove


def job_path(like: str | pathlib.Path, key: str):
    if isinstance(like, pathlib.Path):
        path = like
    else:
        path = pathlib.Path(like)
    path = path.with_stem(path.stem + "_slurm_" + key)
    path = path.with_suffix(".sh")

    return unique(path)


def load_template(
    path: pathlib.Path,
    job_out_dir: pathlib.Path,
    job_name: str,
    srun_command: str,
    env_suffix: str,
    sbatch_options: list[str] | None = None,
) -> str:
    """load and format a template

    Args:
        path (pathlib.Path): path to the template
        job_name (str): #SBATCH --job-name=
        srun_command (str): argument to `srun`
        sbatch_options (list[str] | None): other #SBATCH items to add
        allow_missing (bool): ignore missing format specifier (default, False)

    Returns:
        str: The formatted template
    """

    with open(path, "r", encoding="utf8") as template_file:
        template = template_file.read()

    env_str = env.execution_env_str(env_suffix)

    options = "" if not sbatch_options else "\n".join(sbatch_options)
    format_dict = {
        __JOB_NAME: job_name,
        __JOB_COMMAND: srun_command,
        __JOB_OPTIONS: options + f"\nexport {env_str}\n",
        __JOB_OUT_DIR: str(job_out_dir),
    }

    return template.format(**format_dict)


def run_sbatch(
    job_data: str,
    job_path: pathlib.Path,
    slurm_args: list[str],
    no_dry_run: bool,
):
    with contextlib.ExitStack() as stack:
        dest, remove = write_job_file(job_data, job_path, no_dry_run)
        if remove:
            stack.callback(pathlib.Path(dest).unlink)

        sbatch_command = ["sbatch"] + slurm_args + [dest]

        if no_dry_run:
            subprocess.run(sbatch_command)
        else:
            run = DryRun()
            run.print(shlex.join(sbatch_command))
            run.print(f"\vslurm submission scrip ({dest}):\v")
            run.print(job_data)


def run_slurm_array(
    commands: list[list[str]],
    max_concurrency: int | None,
    template_path: pathlib.Path,
    job_out_dir: pathlib.Path,
    no_dry_run: bool,
    job_name: str,
    slurm_args: list[str],
    sbatch_options: list[str] | None = None,
):
    # add each configuration as its own command
    bash_array = "commands=(\n  "
    bash_array += "\n  ".join(shlex.quote(shlex.join(cmd)) for cmd in commands)
    bash_array += "\n)"

    if max_concurrency is None:
        max_concurrency = len(commands)
    sbatch_options = [
        "#SBATCH --array=0-{:d}%{:d}".format(len(commands)-1, max_concurrency),
        "",  # newline before the args,
        bash_array,
    ]

    job_data = load_template(
        template_path,
        job_out_dir,
        job_name,
        "${commands[@]:$SLURM_ARRAY_TASK_ID:1}",
        "${SLURM_ARRAY_TASK_ID}",
        sbatch_options,
    )

    run_sbatch(job_data, job_out_dir / template_path.name, slurm_args, no_dry_run)


def run_slurm(
    template_file: pathlib.Path | None,
    job_out_dir: pathlib.Path,
    job_name: str,
    command: list[str],
    slurm_args: list[str],
    no_dry_run: bool,
):
    if template_file is not None:
        command_ = shlex.join(command)

        job_data = load_template(
            template_file,
            job_out_dir,
            job_name,
            command_,
            "main",
        )

        run_sbatch(job_data, job_out_dir / template_file.name, slurm_args, no_dry_run)
        return

    job_stdout = unique(job_out_dir / "stdout.out")
    job_stderr = unique(job_out_dir / "stderr.out")

    # srun invocation
    srun_command = ["srun"] + slurm_args + command
    if no_dry_run:
        subprocess.Popen(
            srun_command,
            stdin=subprocess.DEVNULL,
            stdout=open(job_stdout, "w", encoding="utf8"),
            stderr=open(job_stderr, "w", encoding="utf8"),
            env=env.execution_env_dct("main", include_os_environ=True),
        )
    else:
        DryRun().print(shlex.join(srun_command) + f" 1> {job_stdout} 2> {job_stderr} &")
