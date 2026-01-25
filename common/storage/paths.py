from pathlib import Path


def get_project_root() -> Path:
    """
    Project root = folder chứa thư mục 'common'
    """
    return Path(__file__).resolve().parents[2]


def get_results_root() -> Path:
    return get_project_root() / "results"


def get_refs_root() -> Path:
    return get_results_root() / "refs"

def get_runs_root() -> Path:
    return get_results_root() / "runs"

def get_benchmarks_root() -> Path:
    return get_project_root() / "benchmarks/epfl/arithmetic/"

def get_ref_result_dir(
    script_name: str,
    option: str,
    design_name: str,
    create: bool = True,
) -> Path:
    """
    results/refs/<script_name>/<option>/<design_name>/
    """
    result_dir = (
        get_refs_root()
        / script_name
        / option
        / design_name
    )

    if create:
        result_dir.mkdir(parents=True, exist_ok=True)

    return result_dir

def get_run_result_dir(
    algo_name: str,
    option: str,
    design_name: str,
    run_id: int | None = None,
    create: bool = True,
) -> Path:
    """
    - Deterministic (greedy): run_id = None
      results/runs/<script>/<option>/<design>/

    - Stochastic (GA/RS/BO): run_id = k
      results/runs/<script>/<option>/<design>/run_k/
    """
    base = (
        get_runs_root()
        / algo_name
        / option
        / design_name
    )

    result_dir = base if run_id is None else base / f"run_{run_id}"

    if create:
        result_dir.mkdir(parents=True, exist_ok=True)

    return result_dir

