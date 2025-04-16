#!/usr/bin/env python3
"""
Script to run a Jupyter notebook and capture any errors
"""
import sys

import nbformat
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor


def run_notebook(notebook_path, output_path=None):
    """
    Run a notebook and print the first error encountered

    Args:
        notebook_path: Path to the input notebook
        output_path: Optional output path for executed notebook (default: None)
    """
    try:
        # Load the notebook
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)

        # Configure the notebook executor
        ep = ExecutePreprocessor(timeout=600)

        # Get the directory path for execution context
        import os
        notebook_dir = os.path.dirname(notebook_path)

        # Try to execute the notebook
        try:
            ep.preprocess(nb, {"metadata": {"path": notebook_dir}})
            print("Notebook executed successfully without errors!")

            # Save the executed notebook if output_path is provided
            if output_path:
                # Create directory if it doesn't exist
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                # Write the executed notebook
                with open(output_path, 'w', encoding='utf-8') as f:
                    nbformat.write(nb, f)
                print(f"Executed notebook saved to: {output_path}")

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
    import os
    import argparse

    parser = argparse.ArgumentParser(description='Run a Jupyter notebook and capture errors')
    parser.add_argument('notebook_path', help='Path to the notebook file')
    parser.add_argument('--output', '-o', help='Output path for executed notebook')
    parser.add_argument('--test-output', '-t', action='store_true',
                       help='Save to test_output directory (overrides --output)')

    args = parser.parse_args()

    notebook_path = args.notebook_path

    # Determine output path
    if args.test_output:
        # Extract the notebook name
        notebook_name = os.path.basename(notebook_path)
        base_name, ext = os.path.splitext(notebook_name)
        # Create path in test_output/notebooks
        output_path = os.path.join('test_output', 'notebooks', f"{base_name}_executed{ext}")
    elif args.output:
        output_path = args.output
    else:
        output_path = None

    success = run_notebook(notebook_path, output_path)
    sys.exit(0 if success else 1)
