#!/usr/bin/env python3
"""
Script to run all Jupyter notebooks in the project and save executed versions to test_output
"""
import os
import subprocess
import argparse
from pathlib import Path


def get_notebooks(notebooks_dir="notebooks"):
    """Get all notebook files in the specified directory"""
    notebook_dir = Path(notebooks_dir)
    notebooks = list(notebook_dir.glob("*.ipynb"))

    # Filter out notebooks that look like they're already executed versions
    return [nb for nb in notebooks if not nb.name.endswith("_executed.ipynb")]


def run_notebook(notebook_path, output_dir="test_output/notebooks"):
    """Run a notebook and save the executed version to the output directory"""
    notebook_name = os.path.basename(notebook_path)
    base_name, ext = os.path.splitext(notebook_name)
    output_path = os.path.join(output_dir, f"{base_name}_executed{ext}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Build the command
    cmd = [
        "jupyter", "nbconvert",
        "--to", "notebook",
        "--execute",
        notebook_path,
        "--output", f"{base_name}_executed{ext}",
        "--output-dir", output_dir
    ]

    print(f"Running notebook: {notebook_path}")
    print(f"Output will be saved to: {output_path}")

    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Successfully executed notebook: {notebook_name}")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing notebook {notebook_name}:")
        print(e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run all notebooks and save executed versions to test_output")
    parser.add_argument("--notebooks-dir", default="notebooks", help="Directory containing notebooks")
    parser.add_argument("--output-dir", default="test_output/notebooks", help="Output directory for executed notebooks")
    parser.add_argument("--notebook", help="Run a specific notebook instead of all notebooks")
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    if args.notebook:
        # Run a single notebook
        success = run_notebook(args.notebook, args.output_dir)
        exit(0 if success else 1)
    else:
        # Run all notebooks
        notebooks = get_notebooks(args.notebooks_dir)
        print(f"Found {len(notebooks)} notebooks to run")

        results = []
        for notebook in notebooks:
            success = run_notebook(str(notebook), args.output_dir)
            results.append((notebook.name, success))

        # Print summary
        print("\n=== Execution Summary ===")
        all_succeeded = True
        for notebook, success in results:
            status = "✅ Success" if success else "❌ Failed"
            print(f"{status}: {notebook}")
            if not success:
                all_succeeded = False

        exit(0 if all_succeeded else 1)


if __name__ == "__main__":
    main()
