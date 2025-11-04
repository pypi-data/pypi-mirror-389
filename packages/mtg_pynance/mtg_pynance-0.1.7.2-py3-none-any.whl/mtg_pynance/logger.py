from pathlib import Path
import logging

ROOT_LOGGER = "mtg_pynance"


def make_logger(workspace_path: Path):
    """
    Make mtg_pynance logger.

    Parameters
    ----------
    workspace_path: pathlib.Path
        The project workspace path
    """
    logger = logging.getLogger(ROOT_LOGGER)
    fmt = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    fh = logging.FileHandler(workspace_path / "log.txt", mode="w")
    fh.setFormatter(fmt)
    fh.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    logger.addHandler(fh)


def logger_error(module: str, message: str):
    """
    Record an error in the log.

    Parameters
    ----------
    module: str
        Name of module that function is being called from.
        It should always be "__name__".
    message: str
        Error message.
    """
    logger = logging.getLogger(module)
    logger.error(message)
