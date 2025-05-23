#!/usr/bin/env python3
"""
Script to verify both vector integrity and Wikipedia imports.
This is a wrapper that runs both verify_vectors.py and verify_wikipedia_imports.py
to provide a comprehensive verification of the Pinecone database.
"""

import os.path
import re
import subprocess
import sys
from typing import List, Tuple


def run_script(script_path: str) -> Tuple[int, List[str]]:
    """
    Run a Python script and capture its output.

    Args:
        script_path: Path to the script to run

    Returns:
        Tuple of (exit code, output lines)

    Raises:
        ValueError: If script path is invalid or contains suspicious characters
    """
    # Validate script path for security
    if not os.path.isfile(script_path):
        raise ValueError(f"Script file does not exist: {script_path}")

    if not script_path.endswith(".py"):
        raise ValueError(f"Script must be a Python file: {script_path}")

    # Ensure script path doesn't contain suspicious characters
    if not re.match(r"^[a-zA-Z0-9/_.-]+$", script_path):
        raise ValueError(f"Script path contains invalid characters: {script_path}")

    print(f"\n\n{'=' * 80}")
    print(f"Running {os.path.basename(script_path)}")
    print(f"{'=' * 80}")

    # Subprocess is used safely with fixed commands
    # All inputs are validated using regex
    # nosec: B603 - subprocess call is secure with fixed interpreter and validated paths
    process = subprocess.run(
        [sys.executable, script_path],  # Using fixed command
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    output = process.stdout.splitlines()
    for line in output:
        print(line)

    return process.returncode, output


def main() -> None:
    """Main entry point."""
    scripts_dir = os.path.dirname(os.path.abspath(__file__))

    # Run vector verification
    vector_script = os.path.join(scripts_dir, "verify_vectors.py")
    vector_code, vector_output = run_script(vector_script)

    # Run Wikipedia import verification
    wiki_script = os.path.join(scripts_dir, "verify_wikipedia_imports.py")
    wiki_code, wiki_output = run_script(wiki_script)

    # Determine overall status
    if vector_code == 0 and wiki_code == 0:
        print("\n\n✅ ALL VERIFICATIONS PASSED!")
        sys.exit(0)
    else:
        print("\n\n❌ SOME VERIFICATIONS FAILED!")
        if vector_code != 0:
            print("  - Vector verification failed")
        if wiki_code != 0:
            print("  - Wikipedia import verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
