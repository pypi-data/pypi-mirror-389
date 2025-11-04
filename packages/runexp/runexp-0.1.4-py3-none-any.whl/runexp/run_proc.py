import multiprocessing
import pathlib
import subprocess
import time
import threading
import typing

from .environment import env

A = typing.TypeVar("A")


def _t_sp(
    idx: int,
    cmd: list[str],
    cfg_path: pathlib.Path,
    semaphore,
):
    with (
        semaphore as _,
        open(cfg_path.with_suffix(".out"), "x", encoding="utf8") as f_o,
        open(cfg_path.with_suffix(".err"), "x", encoding="utf8") as f_e,
    ):
        start = time.time()
        proc = subprocess.Popen(
            cmd,
            executable=None,  # infer from args
            stdin=subprocess.DEVNULL,  # no input
            stdout=f_o,
            stderr=f_e,
            shell=False,  # not needed -> directly python
            env=env.execution_env_dct(str(idx + 1), include_os_environ=True),
        )

        status = proc.wait()
        delay = time.time() - start
        f_e.write(f"\n RUNEXP: program exited ({status=}) after {delay:.3}s\n")


def run_multi(
    commands: dict[pathlib.Path, list[str]],
    max_concurrency: int | None,
):
    """run multiple processes concurrently from the give commands.
    The files given as keys to `commands` don't need to exist, the the parent
    directory of all commands must exist and be writable. The files' suffix will
    be updated to .out and .err for STDOUT/STDERR redirection.

    Args:
        commands (dict[pathlib.Path, list[str]]): map from file to command
        max_concurrency (int | None): maximum number of live processes (use #CPU if None)
    """
    if max_concurrency is None:
        max_concurrency = multiprocessing.cpu_count()
    semaphore = threading.Semaphore(max_concurrency)

    threads: list[threading.Thread] = []
    for idx, (cfg_path, command) in enumerate(commands.items()):
        t_arg = (idx, command, cfg_path, semaphore)
        threads.append(threading.Thread(target=_t_sp, args=t_arg))
        threads[-1].start()

    for t in threads:
        t.join()


def call_fn(fun: typing.Callable[[A], None], arg: A):
    # a sweep will re-execute runexp in an execution context, fun should just be forwarded
    if env.is_execution_context():
        fun(arg)
        return

    # a simple call should transition to an execution context
    with env.make_execution_context("main"):
        fun(arg)


def run_command(command: list[str]):
    subprocess.run(
        command,
        env=env.execution_env_dct("main", include_os_environ=True),
    )
