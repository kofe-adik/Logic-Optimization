import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Setup logger with:
      - StreamHandler (terminal)
      - Optional FileHandler

    Re-entrant safe: gọi nhiều lần không nhân handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # tránh add handler trùng
    if not logger.handlers:
        # terminal
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(level)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        # file
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, mode="w")
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    logger.propagate = False
    return logger

