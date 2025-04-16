#!/usr/bin/env python3
"""
Script to run Jupyter notebooks in the project and save executed versions to test_output

This script serves as the primary tool for notebook execution in the NYC Landmarks Vector DB
project. It can run a single notebook or all notebooks in a directory, ensuring they execute
properly in a headless environment and saving the executed versions for review.

Usage:
    To run all notebooks in the default directory:
        python scripts/run_all_notebooks.py

    To run a specific notebook:
        python scripts/run_all_notebooks.py --notebook notebooks/landmark_query_testing.ipynb

    To specify a different notebooks directory:
        python scripts/run_all_notebooks.py --notebooks-dir path/to/notebooks

    To specify a different output directory:
        python scripts/run_all_notebooks.py --output-dir path/to/output

All executed notebooks will have cell outputs included and will be saved with "_executed"
suffix in the specified output directory. This helps verify notebook functionality while
keeping the source notebooks clean in the repository (via nbstripout).
"""
import argparse
import os
import subprocess  # nosec B404 - Required for notebook execution
from pathlib import Path
from typing import List, Tuple


def get_notebooks(notebooks_dir: str = "notebooks") -> List[Path]:
    """
    Get all notebook files in the specified directory

    Args:
        notebooks_dir: Path to the directory containing notebooks

    Returns:
        List of Path objects for notebooks (excluding already executed versions)
    """
    notebook_dir = Path(notebooks_dir)
    notebooks = list(notebook_dir.glob("*.ipynb"))

    # Filter out notebooks that look like they're already executed versions
    return [nb for nb in notebooks if not nb.name.endswith("_executed.ipynb")]


def run_notebook(
    notebook_path: str, output_dir: str = "test_output/notebooks", timeout: int = 600
) -> bool:
    """
    Run a notebook and save the executed version to the output directory

    This function executes a Jupyter notebook using nbconvert, capturing any errors
    and saving the executed notebook (with outputs) to the specified output directory.

    Args:
        notebook_path: Path to the notebook to execute
        output_dir: Directory where executed notebook will be saved
        timeout: Cell execution timeout in seconds

    Returns:
        True if execution succeeded, False otherwise
    """
    notebook_name = os.path.basename(notebook_path)
    base_name, ext = os.path.splitext(notebook_name)
    output_path = os.path.join(output_dir, f"{base_name}_executed{ext}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Build the command
    cmd = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        f"--ExecutePreprocessor.timeout={timeout}",
        notebook_path,
        "--output",
        f"{base_name}_executed{ext}",
        "--output-dir",
        output_dir,
    ]

    print(f"Running notebook: {notebook_path}")
    print(f"Output will be saved to: {output_path}")

    try:
        # Run the command - we're using trusted input, not user input
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )  # nosec B603
        print(f"Successfully executed notebook: {notebook_name}")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing notebook {notebook_name}:")
        print(e.stderr)
        return False


def main() -> None:
    """
    Main function to parse arguments and run notebooks

    The script can run in two modes:
    1. Single notebook mode: Runs a specific notebook with the --notebook flag
    2. Batch mode: Runs all notebooks in a specified directory

    In both cases, executed notebooks are saved to the output directory.
    """
    parser = argparse.ArgumentParser(
        description="Run notebooks and save executed versions to test_output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all notebooks in the notebooks directory
  python scripts/run_all_notebooks.py

  # Run a specific notebook
  python scripts/run_all_notebooks.py --notebook notebooks/landmark_query_testing.ipynb

  # Run all notebooks with a custom output directory
  python scripts/run_all_notebooks.py --output-dir my_test_results/notebooks
""",
    )
    parser.add_argument(
        "--notebooks-dir", default="notebooks", help="Directory containing notebooks"
    )
    parser.add_argument(
        "--output-dir",
        default="test_output/notebooks",
        help="Output directory for executed notebooks",
    )
    parser.add_argument(
        "--notebook", help="Run a specific notebook instead of all notebooks"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Cell execution timeout in seconds (default: 600)",
    )
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    if args.notebook:
        # Run a single notebook
        success = run_notebook(args.notebook, args.output_dir, args.timeout)
        exit(0 if success else 1)
    else:
        # Run all notebooks
        notebooks = get_notebooks(args.notebooks_dir)
        print(f"Found {len(notebooks)} notebooks to run")

        results: List[Tuple[str, bool]] = []
        for notebook in notebooks:
            # Store the name before passing the path as a string to run_notebook
            notebook_name = notebook.name
            success = run_notebook(str(notebook), args.output_dir, args.timeout)
            results.append((notebook_name, success))

        # Print summary
        print("\n=== Execution Summary ===")
        all_succeeded = True
        for notebook_name, success in results:
            status = "✅ Success" if success else "❌ Failed"
            print(f"{status}: {notebook_name}")
            if not success:
                all_succeeded = False

        exit(0 if all_succeeded else 1)


if __name__ == "__main__":
    main()
