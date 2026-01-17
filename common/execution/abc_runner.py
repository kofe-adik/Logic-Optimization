import subprocess

class AbcRunError(RuntimeError):
    pass

def run_abc_script(
    script: str,
    abc_bin: str = "yosys-abc",
) -> str:
    """
    Execute ABC with a given script.
    Args:
        script: ABC command string passed to `-c`
        abc_bin: ABC binary (default: yosys-abc)
    Returns:
        Raw stdout from ABC
    Raises:
        AbcRunError: if ABC execution fails
    """
    try:
        proc = subprocess.run(
            [abc_bin, "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    except FileNotFoundError as e:
        raise AbcRunError(f"ABC binary not found: {abc_bin}") from e

    if proc.returncode != 0:
        raise AbcRunError(
            "ABC execution failed\n"
            f"Return code: {proc.returncode}\n"
            f"STDERR:\n{proc.stderr}\n"
            f"STDOUT:\n{proc.stdout}"
        )

    return proc.stdout

