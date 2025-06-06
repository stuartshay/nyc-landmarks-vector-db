"""
Test script to validate the concurrent processing improvements in fetch_landmark_reports.py

This script tests the performance of the parallel execution improvements in PR #144
by running the fetch_landmark_reports.py script with a small dataset, both with
Wikipedia article counting and PDF index status checking enabled.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nyc_landmarks.utils.logger import get_logger

logger = get_logger(name="test_landmark_concurrency")


def _build_command(
    limit: int,
    include_wikipedia: bool,
    include_pdf_index: bool,
    verbose: bool,
) -> list[str]:
    """Build the command line arguments for the fetch_landmark_reports.py script."""
    cmd = [sys.executable, "scripts/fetch_landmark_reports.py", "--limit", str(limit)]

    if include_wikipedia:
        cmd.append("--include-wikipedia")

    if include_pdf_index:
        cmd.append("--include-pdf-index")

    if verbose:
        cmd.append("--verbose")

    return cmd


def _execute_command(cmd: list[str]) -> tuple[int, str, str]:
    """Execute the command and return the results."""
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def _log_output_summary(stdout: str) -> None:
    """Log relevant lines from stdout."""
    if not stdout:
        return

    logger.info("OUTPUT SUMMARY:")
    for line in stdout.split("\n"):
        if any(
            keyword in line
            for keyword in ["Wikipedia articles", "PDF index", "Processing time"]
        ):
            logger.info(f"  {line.strip()}")


def _log_errors(stderr: str) -> None:
    """Log error messages from stderr."""
    if not stderr:
        return

    logger.error("ERRORS:")
    for line in stderr.split("\n"):
        if line.strip():
            logger.error(f"  {line.strip()}")


def run_test(
    limit: int = 10,
    include_wikipedia: bool = True,
    include_pdf_index: bool = True,
    verbose: bool = True,
) -> tuple[int, float]:
    """
    Run the fetch_landmark_reports.py script with specified options.

    Args:
        limit: Number of landmarks to process
        include_wikipedia: Whether to include Wikipedia article counts
        include_pdf_index: Whether to check PDF index status
        verbose: Enable verbose logging

    Returns:
        tuple: (return_code, execution_time_seconds)
    """
    start_time = time.time()

    cmd = _build_command(limit, include_wikipedia, include_pdf_index, verbose)
    logger.info(f"Running command: {' '.join(cmd)}")

    return_code, stdout, stderr = _execute_command(cmd)
    execution_time = time.time() - start_time

    logger.info(f"Command completed with return code: {return_code}")
    logger.info(f"Execution time: {execution_time:.2f} seconds")

    _log_output_summary(stdout)
    _log_errors(stderr)

    return return_code, execution_time


def main() -> int:
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Test concurrent processing in fetch_landmark_reports.py"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of landmarks to process (default: 10)",
    )
    parser.add_argument(
        "--no-wikipedia", action="store_true", help="Disable Wikipedia article counting"
    )
    parser.add_argument(
        "--no-pdf-index", action="store_true", help="Disable PDF index status checking"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("STARTING CONCURRENT PROCESSING TEST")
    logger.info("=" * 70)
    logger.info(f"Testing with {args.limit} landmarks")
    logger.info(
        f"Wikipedia article counting: {'Disabled' if args.no_wikipedia else 'Enabled'}"
    )
    logger.info(
        f"PDF index status checking: {'Disabled' if args.no_pdf_index else 'Enabled'}"
    )

    return_code, execution_time = run_test(
        limit=args.limit,
        include_wikipedia=not args.no_wikipedia,
        include_pdf_index=not args.no_pdf_index,
    )

    logger.info("=" * 70)
    if return_code == 0:
        logger.info(f"TEST PASSED - Completed in {execution_time:.2f} seconds")
    else:
        logger.error(f"TEST FAILED - Return code: {return_code}")
    logger.info("=" * 70)

    return return_code


if __name__ == "__main__":
    sys.exit(main())
