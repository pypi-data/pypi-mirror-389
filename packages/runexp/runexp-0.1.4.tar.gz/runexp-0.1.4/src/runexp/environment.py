"env: relevant information on a run"

import contextlib
import os
from datetime import datetime

# TODO what is the base key even used for ?
#   -> items are already grouped by the prefix
#   -> we could create a directory per run instead
# 'invocation' context could only produce keys
# 'execution' context could only read the current key
# 'transition' is it useful ?
# the copy of config/... does not happen all the times -> it should


# refactor
#   * create a directory for each run
#       - copy launch information (commands + config file + slurm template)
#       - copy stdout & stderr
#   * each run should still be responsible for copying the config file in an output directory if necessary

class env:
    _K_EX = "RUNEXP_EXEC_KEY"
    _SEP = "--"
    _DT_FORMAT = f"%Y-%m-%d{_SEP}%H-%M-%S-%f{_SEP}%z"
    _now = datetime.now().astimezone().strftime(_DT_FORMAT)

    @staticmethod
    def _derive_ex_key(arg: str):
        inv_key = env.invocation_key()
        return inv_key + env._SEP + arg

    @staticmethod
    def _derive_inv_key(ex_key: str):
        parts = ex_key.split(env._SEP)
        if len(parts) != 4:
            raise ValueError(f"illegal value for {ex_key=!r} in non-public method")

        return env._SEP.join(parts[:3])

    @staticmethod
    def execution_env_str(arg: str):
        "suitable for a POSIX environment assignment in a command"
        return f"{env._K_EX}=\"{env._derive_ex_key(arg)}\""

    @staticmethod
    def execution_env_dct(arg: str, *, include_os_environ: bool):
        """suitable for

        `os.environ.update(env.execution_env_dct(...)) ; fn(...)`

        `subprocess.Popen(..., env={**os.environ, **env.execution_env_dct(0)})`

        `subprocess.run(..., env={**os.environ, **env.execution_env_dct(0)})`
        """

        specific = {env._K_EX: env._derive_ex_key(arg)}
        if include_os_environ:
            return {**os.environ, **specific}
        return specific

    @contextlib.contextmanager
    @staticmethod
    def make_execution_context(arg: str):
        "context manager to transition to an execution context"

        value = env._derive_ex_key(arg)
        try:
            os.environ[env._K_EX] = value
            yield value
        finally:
            del os.environ[env._K_EX]

    @staticmethod
    def _execution_key_faillible():
        return os.environ.get(env._K_EX)

    @staticmethod
    def is_execution_context():
        return env._execution_key_faillible() is not None

    @staticmethod
    def execution_key():
        "key identifying the task inside the run/sweep"
        if (key := env._execution_key_faillible()) is None:
            raise ValueError("no execution context found")
        return key

    @staticmethod
    def invocation_key():
        "key identifying the whole run/sweep"

        if env._execution_key_faillible() is not None:
            raise ValueError("invocation key may not be accessed in execution context")

        return env._now
