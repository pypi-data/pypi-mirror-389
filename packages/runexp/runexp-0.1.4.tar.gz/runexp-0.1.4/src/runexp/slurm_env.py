import os


class _slurm_env:
    "descriptor class to load slurm environment variable based on function name."

    def __init__(self, fun):
        self.key = "SLURM_" + str(fun.__name__).upper()

    def __get__(self, _, __):
        value_s = os.environ.get(self.key)
        if value_s is not None:
            return int(value_s)
        return None


class SLURMEnv:
    """Collection of SLURM environment variables in a namespace. Instantiating
    SlurmEnv is useless, but will work fine.

    - All variables are None if the current program is not ran by SLURM.
    - All variables beginning with "array_" are None if the current program is not
    part of a SLURM job array.

    Reference: https://slurm.schedmd.com/sbatch.html#SECTION_OUTPUT-ENVIRONMENT-VARIABLES
    """

    @_slurm_env
    def job_id():  # type:ignore[misc]
        "job ID (%j)"

    @_slurm_env
    def array_job_id():  # type:ignore[misc]
        "job ID of the array's master job (%A)"

    @_slurm_env
    def array_task_id():  # type:ignore[misc]
        "job array one-based index (%a)"

    @_slurm_env
    def array_task_count():  # type:ignore[misc]
        "number of tasks in the array"

    @_slurm_env
    def array_task_max():  # type:ignore[misc]
        "maximum index of any task in the array"

    @_slurm_env
    def array_task_min():  # type:ignore[misc]
        "minimum index of any task in the array"

    @staticmethod
    def is_ran_by_slurm():
        return SLURMEnv.job_id is not None

    @staticmethod
    def is_array():
        return SLURMEnv.array_job_id is not None

    @staticmethod
    def array_pos_len():
        "zero based indexing and length of the task in the array"
        idx_1 = SLURMEnv.array_job_id
        idx_max = SLURMEnv.array_task_max
        if idx_1 is None:
            return None
        assert idx_max is not None

        return idx_1 - 1, idx_max
