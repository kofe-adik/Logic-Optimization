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

