from pathlib import Path
from typing import Union


def ensure_directory_exists(directory_path: Union[str, Path]) -> None:
    """Ensure that the specified directory exists.

    Args:
        directory_path: Path to the directory to ensure exists.
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)
