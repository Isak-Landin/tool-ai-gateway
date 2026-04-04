from errors import ProjectBootstrapError
from repository_runtime.bootstrap.bs1 import Bs1VerificationFailure, _verify_bs1, bs1
from repository_runtime.bootstrap.bs2 import _verify_bs2, bs2


def verify_bs_all(
    *,
    project_paths,
    shell,
):
    try:
        verify_bs_1_ok, verify_bs_1_failure = _verify_bs1(
            project_paths=project_paths,
            shell=shell,
        )
        if not verify_bs_1_ok:
            return False, verify_bs_1_failure

        verify_bs_2_ok, verify_bs_2_failure = _verify_bs2(
            project_paths=project_paths,
            shell=shell,
        )
        if not verify_bs_2_ok:
            return False, verify_bs_2_failure

        return True, None
    except ProjectBootstrapError:
        raise

__all__ = [
    "bs1",
    "bs2",
    "Bs1VerificationFailure",
    "verify_bs_all"
]
