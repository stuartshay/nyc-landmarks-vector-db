#!/usr/bin/env python3
"""
Script to run a Jupyter notebook and capture any errors
"""
import sys

import nbformat
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor


def run_notebook(notebook_path):
    """Run a notebook and print the first error encountered"""
    try:
        # Load the notebook
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)

        # Configure the notebook executor
        ep = ExecutePreprocessor(timeout=600)

        # Try to execute the notebook
        try:
            ep.preprocess(nb, {"metadata": {"path": "."}})
            print("Notebook executed successfully without errors!")
            return True
        except CellExecutionError as e:
            # Extract the error details
            error_msg = str(e)
            print(f"\nError executing the notebook: {error_msg}")

            # Try to parse and extract just the most relevant part of the error
            if "Cell execution caused an exception" in error_msg:
                parts = error_msg.split("Cell execution caused an exception")
                if len(parts) > 1:
                    error_details = parts[1].strip()
                    print(f"\nError details:\n{error_details}")
            return False
    except Exception as e:
        print(f"Error loading or processing the notebook: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_notebook.py <path_to_notebook>")
        sys.exit(1)

    notebook_path = sys.argv[1]
    success = run_notebook(notebook_path)
    sys.exit(0 if success else 1)
