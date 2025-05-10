#!/usr/bin/env python3
"""
GitHub Action Log Analyzer

This script parses a GitHub Action log file and extracts warnings, errors,
and other important information to help diagnose issues in the workflow.

python scripts/analyze_github_log.py <github_action_job_url_or_log_file_path>
"""

import os
import re
import shutil  # Added import
import subprocess  # nosec B404 - subprocess is used safely with fixed commands
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple  # Removed Union

LOG_DIR = "logs"  # Added constant for log directory


def download_log_from_url(log_url: str) -> Optional[str]:
    """
    Downloads a GitHub Action log from a given URL.

    Args:
        log_url: The URL of the GitHub Action job log.
                 Example: https://github.com/owner/repo/actions/runs/run_id/job/job_id

    Returns:
        The path to the downloaded log file, or None if download fails.
    """
    print(f"Attempting to download log from URL: {log_url}")
    parsed = _parse_github_url(log_url)
    if parsed is None:
        return None
    owner, repo, run_id, job_id = parsed
    os.makedirs(LOG_DIR, exist_ok=True)
    output_filename = os.path.join(LOG_DIR, f"github_action_log_{job_id}.txt")
    success = _execute_gh_log_download(owner, repo, run_id, job_id, output_filename)
    if success:
        print(f"Log successfully downloaded to: {output_filename}")
        return output_filename
    else:
        return None


# --- Helper functions for download_log_from_url ---
def _parse_github_url(log_url: str) -> Optional[Tuple[str, str, str, str]]:
    """
    Parse a GitHub Actions job log URL and extract owner, repo, run_id, and job_id.
    Returns a tuple (owner, repo, run_id, job_id) or None if parsing fails.
    """
    pattern = re.compile(
        r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/actions/runs/(?P<run_id>\d+)/job/(?P<job_id>\d+)"
    )
    match = pattern.match(log_url)
    if not match:
        print(f"Error: Invalid GitHub Action log URL format: {log_url}")
        print(
            "Expected format: https://github.com/owner/repo/actions/runs/run_id/job/job_id"
        )
        return None
    owner = match.group("owner")
    repo = match.group("repo")
    run_id = match.group("run_id")
    job_id = match.group("job_id")
    return owner, repo, run_id, job_id


def _execute_gh_log_download(
    owner: str, repo: str, run_id: str, job_id: str, output_filename: str
) -> bool:
    """
    Download the GitHub Actions job log using the gh CLI.
    Returns True if successful, False otherwise.

    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        run_id: GitHub workflow run ID
        job_id: GitHub workflow job ID
        output_filename: Path where the log file will be saved
    """
    # The run_id and job_id are validated by regex pattern before passing to this function
    gh_command_list: List[str] = [
        "gh",
        "run",
        "view",
        run_id,
        "--job",
        job_id,
        "--log",
    ]
    print(f"Executing: {' '.join(gh_command_list)}")
    try:
        process = subprocess.run(
            gh_command_list,  # nosec B603 - All inputs are validated using regex
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
        if process.returncode == 0:
            with open(output_filename, "w", encoding="utf-8") as f_out:
                f_out.write(process.stdout)
            return True
        else:
            print(
                f"Error downloading log (gh command return code: {process.returncode}):"
            )
            stdout_msg = process.stdout.strip() if process.stdout else ""
            stderr_msg = process.stderr.strip() if process.stderr else ""
            print(f"Stdout: {stdout_msg}")
            print(f"Stderr: {stderr_msg}")
            if "gh: command not found" in stderr_msg or process.returncode == 127:
                print(
                    "GitHub CLI ('gh') not found. Please install it and ensure it's in your PATH."
                )
                print("Installation guide: https://cli.github.com/")
            elif "Could not find job" in stderr_msg or "HTTP 404" in stderr_msg:
                print(
                    f"Could not find job with ID {job_id} for run {run_id}. Check the URL and permissions."
                )
            return False
    except FileNotFoundError:
        print(
            "Error: GitHub CLI ('gh') not found. Please install it and ensure it's in your PATH."
        )
        print("Installation guide: https://cli.github.com/")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error executing gh command (CalledProcessError): {e}")
        stderr_val = (
            e.stderr.strip()
            if isinstance(e.stderr, str)
            else (e.stderr.decode("utf-8").strip() if e.stderr else "")
        )
        print(f"Stderr: {stderr_val}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during log download: {e}")
        return False


# mypy: ignore-errors
# Type definitions for better readability
ErrorRecord = Tuple[int, str]  # Line number, error message
ErrorCollection = List[ErrorRecord]
ModuleErrors = Dict[str, ErrorCollection]
ErrorTrackers = Dict[str, Any]  # Can't be more specific due to mixture of types
PatternDict = Dict[str, Any]  # Using Any for re.Pattern to avoid typing issues


def initialize_error_trackers() -> ErrorTrackers:
    """Initialize counters and collections for error tracking."""
    return {
        "error_count": 0,
        "warning_count": 0,
        "api_errors": [],
        "pinecone_errors": [],
        "zero_vector_errors": [],
        "other_errors": [],
        "errors_by_module": defaultdict(list),
    }


def compile_error_patterns() -> PatternDict:
    """Compile regular expressions to match different error patterns."""
    return {
        "error_pattern": re.compile(r"ERROR:(.*)"),
        "warning_pattern": re.compile(r"WARNING:(.*)"),
        "api_error_pattern": re.compile(r".*Error making API request:.*"),
        "pinecone_pattern": re.compile(r".*Error storing vectors:.*"),
        "zero_vector_pattern": re.compile(
            r".*Dense vectors must contain at least one non-zero value.*"
        ),
        "module_pattern": re.compile(r"ERROR:([^:]+):(.+)"),
    }


def process_log_line(
    line: str, line_num: int, trackers: ErrorTrackers, patterns: PatternDict
) -> None:
    """Process a single line from the log file."""
    line = line.strip()

    # Check for errors
    error_match = patterns["error_pattern"].match(line)
    if error_match or "ERROR:" in line:
        trackers["error_count"] += 1
        error_text = error_match.group(1) if error_match else line

        # Categorize errors
        if patterns["api_error_pattern"].match(line):
            trackers["api_errors"].append((line_num, error_text))
        elif patterns["pinecone_pattern"].match(line):
            trackers["pinecone_errors"].append((line_num, error_text))
        elif patterns["zero_vector_pattern"].match(line):
            trackers["zero_vector_errors"].append((line_num, error_text))
        else:
            trackers["other_errors"].append((line_num, error_text))

        # Group errors by module
        module_match = patterns["module_pattern"].match(line)
        if module_match:
            module_name = module_match.group(1)
            trackers["errors_by_module"][module_name].append(
                (line_num, module_match.group(2))
            )

    # Check for warnings
    warning_match = patterns["warning_pattern"].match(line)
    if warning_match or "WARNING:" in line:
        trackers["warning_count"] += 1


def print_api_error_summary(api_errors: ErrorCollection) -> None:
    """Print summary of API errors."""
    print("\n=== API Errors ===")
    api_error_summary = Counter(
        [
            (
                search_result.group(1)
                if (search_result := re.search(r"url: ([^\s]+)", err[1])) is not None
                else err[1]
            )
            for err in api_errors
        ]
    )
    for url, count in api_error_summary.most_common():
        print(f"  {url}: {count} occurrences")


def print_error_category(
    errors: ErrorCollection, category_name: str, limit: int = 5
) -> None:
    """Print a summary of errors for a specific category."""
    print(f"\n=== {category_name} ===")
    print(f"Found {len(errors)} {category_name}")

    if errors:
        for line_num, error_text in errors[:limit]:
            print(
                f"  Line {line_num}: {error_text[:100]}..."
                if len(error_text) > 100
                else f"  Line {line_num}: {error_text}"
            )
        if len(errors) > limit:
            print(f"  ... and {len(errors) - limit} more")


def print_zero_vector_errors(zero_vector_errors: ErrorCollection) -> None:
    """Print summary of zero vector errors."""
    print("\n=== Zero Vector Errors ===")
    if zero_vector_errors:
        # Extract vector IDs with format problems
        vector_ids: List[str] = []
        for _, error_text in zero_vector_errors:
            match = re.search(r"Vector ID '([^']+)'", error_text)
            if match:
                vector_ids.append(match.group(1))

        # Print unique vector IDs with problems
        unique_ids = set(vector_ids)
        for vid in list(unique_ids)[:10]:
            print(f"  {vid}")
        if len(unique_ids) > 10:
            print(f"  ... and {len(unique_ids) - 10} more")


def print_module_errors(errors_by_module: Dict[str, ErrorCollection]) -> None:
    """Print errors grouped by module."""
    print("\n=== Errors by Module ===")
    for module, errors in sorted(
        errors_by_module.items(), key=lambda x: len(x[1]), reverse=True
    ):
        print(f"{module}: {len(errors)} errors")


def parse_log_file(log_file: str) -> Optional[Dict[str, Any]]:
    """Parse the GitHub Action log file and extract warnings and errors."""

    if not os.path.exists(log_file):
        print(f"Error: File {log_file} does not exist.")
        return None

    print(
        f"Analyzing log file: {log_file} ({os.path.getsize(log_file) / 1024 / 1024:.2f} MB)"
    )
    print("-" * 80)

    # Initialize trackers and patterns
    trackers = initialize_error_trackers()
    patterns = compile_error_patterns()

    # Read and process the file
    with open(log_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            process_log_line(line, line_num, trackers, patterns)

    # Print summaries
    print(f"Total errors: {trackers['error_count']}")
    print(f"Total warnings: {trackers['warning_count']}")
    print("-" * 80)

    print_api_error_summary(trackers["api_errors"])
    print_error_category(trackers["pinecone_errors"], "Pinecone Vector Errors")
    print_zero_vector_errors(trackers["zero_vector_errors"])
    print_module_errors(trackers["errors_by_module"])
    print_error_category(trackers["other_errors"], "Other Errors", limit=10)

    # Return findings for further processing
    return {
        "error_count": trackers["error_count"],
        "warning_count": trackers["warning_count"],
        "api_errors": trackers["api_errors"],
        "pinecone_errors": trackers["pinecone_errors"],
        "zero_vector_errors": trackers["zero_vector_errors"],
        "other_errors": trackers["other_errors"],
        "errors_by_module": trackers["errors_by_module"],
    }


def print_usage_instructions() -> None:
    """Print usage instructions for the script."""
    print(
        "Usage: python analyze_github_log.py <github_action_job_url_or_log_file_path>"
    )
    print("Example URL: https://github.com/owner/repo/actions/runs/run_id/job/job_id")
    print("Example File: logs/github_action_log_somenumber.txt")


def get_log_file_path(input_arg: str) -> Optional[str]:
    """
    Determine the log file path based on the input argument.
    Returns the path to the log file or None if it cannot be determined.
    """
    if input_arg.startswith("https://github.com/"):
        print("Input detected as URL, attempting to download log...")
        os.makedirs(LOG_DIR, exist_ok=True)
        downloaded_log_path = download_log_from_url(input_arg)
        if downloaded_log_path:
            return downloaded_log_path
        else:
            print("Failed to download log file from URL.")
            return None
    elif os.path.exists(input_arg):
        print(f"Input detected as local file path: {input_arg}")
        return input_arg
    else:
        print(
            f"Error: Input '{input_arg}' is not a valid URL or an existing file path."
        )
        return None


def create_log_copy(log_file_path: str) -> Tuple[str, str, str]:
    """
    Create a timestamped copy of the log file.
    Returns a tuple of (timestamp, base_name_for_outputs, complete_log_copy_path)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(log_file_path).replace(".txt", "")

    copy_path = os.path.join(LOG_DIR, f"complete_raw_log_{base_name}_{timestamp}.txt")

    try:
        shutil.copyfile(log_file_path, copy_path)
        print(f"Complete log content has been copied to: {copy_path}")
    except Exception as e:
        print(f"Warning: Could not create a timestamped copy of the complete log: {e}")

    return timestamp, base_name, copy_path


def write_summary_header(
    f: Any, log_file_path: str, timestamp: str, results: Dict[str, Any]
) -> None:
    """Write the header section of the summary file."""
    f.write(f"Log File Analyzed: {log_file_path}\\n")
    f.write(f"Analysis Timestamp: {timestamp}\\n")
    f.write("-" * 80 + "\\n")
    f.write(f"Total errors: {results['error_count']}\\n")
    f.write(f"Total warnings: {results['warning_count']}\\n")
    f.write("-" * 80 + "\\n")


def write_error_section(
    f: Any, errors: ErrorCollection, section_name: str, limit: int = 10
) -> None:
    """Write a section of errors to the summary file."""
    f.write(f"\\n=== {section_name} ===\\n")
    if errors:
        for line_num, err_text in errors[:limit]:
            f.write(f"  Line {line_num}: {err_text}\\n")
        if len(errors) > limit:
            f.write(f"  ... and {len(errors) - limit} more\\n")
    else:
        f.write(f"  No {section_name.lower()} found.\\n")


def write_zero_vector_section(f: Any, zero_vector_errors: ErrorCollection) -> None:
    """Write the zero vector errors section to the summary file."""
    f.write("\\n=== Zero Vector Errors ===\\n")
    if zero_vector_errors:
        vector_ids: List[str] = []
        for _, err_text in zero_vector_errors:
            match = re.search(r"Vector ID '([^']+)'", err_text)
            if match:
                vector_ids.append(match.group(1))

        unique_ids = set(vector_ids)
        for vid in list(unique_ids)[:10]:
            f.write(f"  Vector ID: {vid}\\n")
        if len(unique_ids) > 10:
            f.write(f"  ... and {len(unique_ids) - 10} more unique vector IDs\\n")
    else:
        f.write("  No zero vector errors found.\\n")


def write_module_errors_section(
    f: Any, errors_by_module: Dict[str, ErrorCollection]
) -> None:
    """Write the module errors section to the summary file."""
    f.write("\\n=== Errors by Module ===\\n")
    if errors_by_module:
        for module, errors_list in sorted(
            errors_by_module.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        ):
            f.write(f"{module}: {len(errors_list)} errors\\n")
            for line_num, err_text in errors_list[
                :5
            ]:  # Print first 5 errors per module
                f.write(
                    f"  Line {line_num}: {err_text[:100]}...\\n"
                    if len(err_text) > 100
                    else f"  Line {line_num}: {err_text}\\n"
                )
            if len(errors_list) > 5:
                f.write(f"  ... and {len(errors_list) - 5} more in this module\\n")
    else:
        f.write("  No module-specific errors categorized.\\n")


def write_summary_file(
    results: Dict[str, Any], log_file_path: str, timestamp: str, base_name: str
) -> str:
    """Write analysis results to a summary file."""
    summary_file = os.path.join(
        LOG_DIR, f"analysis_summary_{base_name}_{timestamp}.txt"
    )

    with open(summary_file, "w", encoding="utf-8") as f:
        write_summary_header(f, log_file_path, timestamp, results)
        write_error_section(f, results["api_errors"], "API Errors")
        write_error_section(f, results["pinecone_errors"], "Pinecone Vector Errors")
        write_zero_vector_section(f, results["zero_vector_errors"])
        write_module_errors_section(f, results["errors_by_module"])
        write_error_section(f, results["other_errors"], "Other Errors")

    print(f"\\nSummary saved to {summary_file}")
    return summary_file


def main() -> None:
    """Main function to run the log analyzer."""
    # Check for command line arguments
    if len(sys.argv) < 2:
        print_usage_instructions()
        return

    # Get log file path
    input_arg = sys.argv[1]
    log_file_path = get_log_file_path(input_arg)

    if not log_file_path:
        print("No log file available to analyze.")
        return

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Create a copy of the log file
    timestamp, base_name, _ = create_log_copy(log_file_path)

    # Parse the log file
    results = parse_log_file(log_file_path)

    # Generate summary file if results are available
    if results:
        write_summary_file(results, log_file_path, timestamp, base_name)
    elif os.path.exists(log_file_path):
        print(
            "\\nCould not generate summary report due to parsing issues (parse_log_file returned None)."
        )
    else:
        print(
            "\\nCould not generate summary report because the log file was not found or could not be processed."
        )


if __name__ == "__main__":
    main()
