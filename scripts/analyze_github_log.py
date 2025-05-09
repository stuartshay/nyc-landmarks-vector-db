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
import subprocess  # Added import
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
    # Regex to parse owner, repo, run_id, and job_id from the URL
    # This regex makes job_id optional in capture, but we will require it.
    pattern = re.compile(
        r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/actions/runs/(?P<run_id>\d+)(?:/job/(?P<job_id>\d+))?"
    )
    match = pattern.match(log_url)

    if not match:
        print(f"Error: Invalid GitHub Action log URL format: {log_url}")
        print(
            "Expected format: https://github.com/owner/repo/actions/runs/run_id/job/job_id"
        )
        return None

    parsed_url = match.groupdict()
    run_id_str: Optional[str] = parsed_url.get("run_id")
    job_id_str: Optional[str] = parsed_url.get("job_id")

    if (
        not run_id_str
    ):  # Should not happen with the current regex if match is successful
        print("Error: Could not parse run_id from URL.")
        return None

    # The example URL and desired filename format github_action_log_{job_id}.txt imply job_id is essential.
    if not job_id_str:
        print(
            "Error: Job ID not found in the URL. Please provide a URL that includes the job ID."
        )
        print("Example: https://github.com/owner/repo/actions/runs/run_id/job/job_id")
        # Re-check with a stricter pattern if job_id was initially optional but now deemed necessary
        strict_pattern = re.compile(
            r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/actions/runs/(?P<run_id_strict>\d+)/job/(?P<job_id_strict>\d+)"
        )
        strict_match = strict_pattern.match(log_url)
        if not strict_match:
            # This means the URL didn't have /job/job_id part
            print(f"Error: The provided URL does not contain a job ID: {log_url}")
            return None
        # If strict_match is successful, we can get job_id_strict.
        # However, the initial regex already tries to capture job_id if present.
        # This block is more of a safeguard or clarification.
        # If job_id_str was None, it means the /job/ part was missing.
        return None

    os.makedirs(LOG_DIR, exist_ok=True)
    output_filename = os.path.join(LOG_DIR, f"github_action_log_{job_id_str}.txt")

    # Ensure all parts of the command are strings.
    # run_id_str and job_id_str are already confirmed to be not None here.
    # The type checker might complain if it can't infer that they are strings.
    # We can assert they are strings or use a type guard if necessary,
    # but the logic flow should ensure they are strings by this point.

    # Explicitly ensure command parts are strings for type safety if there were issues.
    # However, run_id_str and job_id_str are derived from regex groups, so they are strings.
    # No, they are Optional[str] initially. We need to ensure they are str.
    # The checks `if not run_id_str:` and `if not job_id_str:` handle this.
    # So, after these checks, they are effectively str.

    # Command to download the log using GitHub CLI
    # Using `gh run view <run_id> --job <job_id> --log`
    # The repo can be specified with --repo owner/repo if gh cannot infer it.
    # For simplicity, assume gh is configured or running in the repo context.
    # If explicit repo is needed:
    # gh_command_list: List[str] = ["gh", "run", "view", run_id_str, "--job", job_id_str, "--log", "--repo", f"{parsed_url['owner']}/{parsed_url['repo']}"]
    gh_command_list: List[str] = [
        "gh",
        "run",
        "view",
        run_id_str,
        "--job",
        job_id_str,
        "--log",
    ]

    print(f"Executing: {' '.join(gh_command_list)}")
    try:
        # subprocess.run expects a list of strings for the command.
        process = subprocess.run(
            gh_command_list,
            capture_output=True,
            text=True,  # Decodes stdout/stderr as text
            check=False,  # We will check returncode manually
            encoding="utf-8",  # Specify encoding for text mode
        )

        if process.returncode == 0:
            with open(output_filename, "w", encoding="utf-8") as f_out:
                f_out.write(process.stdout)
            print(f"Log successfully downloaded to: {output_filename}")
            return output_filename
        else:
            print(
                f"Error downloading log (gh command return code: {process.returncode}):"
            )
            # Make sure stdout and stderr are not None before stripping
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
                    f"Could not find job with ID {job_id_str} for run {run_id_str}. Check the URL and permissions."
                )
            return None  # Explicitly return None on failure

    except FileNotFoundError:  # Raised if 'gh' command itself is not found
        print(
            "Error: GitHub CLI ('gh') not found. Please install it and ensure it's in your PATH."
        )
        print("Installation guide: https://cli.github.com/")
        return None
    except subprocess.CalledProcessError as e:  # Should not be hit if check=False
        print(f"Error executing gh command (CalledProcessError): {e}")
        stderr_val = (
            e.stderr.strip()
            if isinstance(e.stderr, str)
            else (e.stderr.decode("utf-8").strip() if e.stderr else "")
        )
        print(f"Stderr: {stderr_val}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during log download: {e}")
        return None
    # Ensure all paths return a value if the function is expected to.
    # The only path not returning was if an unhandled exception occurred before the final return None.
    # Added explicit return None in more places for clarity.


def parse_log_file(log_file: str) -> Optional[Dict[str, Any]]:
    """Parse the GitHub Action log file and extract warnings and errors."""

    if not os.path.exists(log_file):
        print(f"Error: File {log_file} does not exist.")
        return None

    print(
        f"Analyzing log file: {log_file} ({os.path.getsize(log_file) / 1024 / 1024:.2f} MB)"
    )
    print("-" * 80)
    # Initialize counters and collections
    error_count = 0
    warning_count = 0
    api_errors: List[Tuple[int, str]] = []
    pinecone_errors: List[Tuple[int, str]] = []
    zero_vector_errors: List[Tuple[int, str]] = []
    other_errors: List[Tuple[int, str]] = []
    errors_by_module: Dict[str, List[Tuple[int, str]]] = defaultdict(list)
    errors_by_module = defaultdict(list)

    # Regular expressions to match different patterns
    error_pattern = re.compile(r"ERROR:(.*)")
    warning_pattern = re.compile(r"WARNING:(.*)")
    api_error_pattern = re.compile(r".*Error making API request:.*")
    pinecone_pattern = re.compile(r".*Error storing vectors:.*")
    zero_vector_pattern = re.compile(
        r".*Dense vectors must contain at least one non-zero value.*"
    )
    module_pattern = re.compile(r"ERROR:([^:]+):(.+)")

    # Read and process the file
    with open(log_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Check for errors
            error_match = error_pattern.match(line)
            if error_match or "ERROR:" in line:
                error_count += 1
                error_text = error_match.group(1) if error_match else line

                # Categorize errors
                if api_error_pattern.match(line):
                    api_errors.append((line_num, error_text))
                elif pinecone_pattern.match(line):
                    pinecone_errors.append((line_num, error_text))
                elif zero_vector_pattern.match(line):
                    zero_vector_errors.append((line_num, error_text))
                else:
                    other_errors.append((line_num, error_text))

                # Group errors by module
                module_match = module_pattern.match(line)
                if module_match:
                    module_name = module_match.group(1)
                    errors_by_module[module_name].append(
                        (line_num, module_match.group(2))
                    )

            # Check for warnings
            warning_match = warning_pattern.match(line)
            if warning_match or "WARNING:" in line:
                warning_count += 1

    # Print summary
    print(f"Total errors: {error_count}")
    print(f"Total warnings: {warning_count}")
    print("-" * 80)

    # Print error categories
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

    print("\n=== Pinecone Vector Errors ===")
    print(f"Found {len(pinecone_errors)} Pinecone errors")
    if pinecone_errors:
        for line_num, error_text in pinecone_errors[:5]:
            print(
                f"  Line {line_num}: {error_text[:100]}..."
                if len(error_text) > 100
                else f"  Line {line_num}: {error_text}"
            )
        if len(pinecone_errors) > 5:
            print(f"  ... and {len(pinecone_errors) - 5} more")

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

    print("\n=== Errors by Module ===")
    for module, errors in sorted(
        errors_by_module.items(), key=lambda x: len(x[1]), reverse=True
    ):
        print(f"{module}: {len(errors)} errors")

    print("\n=== Other Errors ===")
    if other_errors:
        for line_num, error_text in other_errors[:10]:
            print(
                f"  Line {line_num}: {error_text[:100]}..."
                if len(error_text) > 100
                else f"  Line {line_num}: {error_text}"
            )
        if len(other_errors) > 10:
            print(f"  ... and {len(other_errors) - 10} more")

    # Return findings for further processing
    return {
        "error_count": error_count,
        "warning_count": warning_count,
        "api_errors": api_errors,
        "pinecone_errors": pinecone_errors,
        "zero_vector_errors": zero_vector_errors,
        "other_errors": other_errors,
        "errors_by_module": errors_by_module,
    }


def main() -> None:
    """Main function to run the log analyzer."""
    if len(sys.argv) < 2:
        print(
            "Usage: python analyze_github_log.py <github_action_job_url_or_log_file_path>"
        )
        print(
            "Example URL: https://github.com/owner/repo/actions/runs/run_id/job/job_id"
        )
        print("Example File: logs/github_action_log_somenumber.txt")
        return  # main function does not have a return type annotation, so bare return is fine.

    input_arg = sys.argv[1]
    log_file_to_analyze: Optional[str] = None  # Ensure type consistency

    if input_arg.startswith("https://github.com/"):
        print("Input detected as URL, attempting to download log...")
        # Ensure LOG_DIR exists before attempting download, as download_log_from_url writes there
        os.makedirs(LOG_DIR, exist_ok=True)
        downloaded_log_path = download_log_from_url(input_arg)
        if downloaded_log_path:
            log_file_to_analyze = downloaded_log_path
        else:
            print("Failed to download log file from URL.")
            return  # Exit if download failed
    elif os.path.exists(input_arg):
        print(f"Input detected as local file path: {input_arg}")
        log_file_to_analyze = input_arg
    else:
        print(
            f"Error: Input '{input_arg}' is not a valid URL or an existing file path."
        )
        return  # Exit if input is invalid

    if (
        not log_file_to_analyze
    ):  # This check might be redundant if returns are used above, but safe.
        print("No log file available to analyze.")
        return  # Exit if no file

    # Ensure LOG_DIR exists for outputs (might be redundant if URL path taken, but good for local files)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Create a timestamped copy of the complete log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name_for_outputs = os.path.basename(log_file_to_analyze).replace(".txt", "")

    complete_log_copy_path = os.path.join(
        LOG_DIR, f"complete_raw_log_{base_name_for_outputs}_{timestamp}.txt"
    )

    try:
        shutil.copyfile(log_file_to_analyze, complete_log_copy_path)
        print(f"Complete log content has been copied to: {complete_log_copy_path}")
    except Exception as e:
        print(
            f"Warning: Could not create a timestamped copy of the complete log at {complete_log_copy_path}: {e}"
        )
        # Continue with analysis even if copy fails

    results = parse_log_file(log_file_to_analyze)

    if results:
        # Save results to a summary file
        # timestamp and base_name_for_outputs are already defined
        summary_file = os.path.join(
            LOG_DIR, f"analysis_summary_{base_name_for_outputs}_{timestamp}.txt"
        )

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"Log File Analyzed: {log_file_to_analyze}\\\\n")
            f.write(f"Analysis Timestamp: {timestamp}\\\\n")
            f.write("-" * 80 + "\\n")
            f.write(f"Total errors: {results['error_count']}\\\\n")
            f.write(f"Total warnings: {results['warning_count']}\\\\n")
            f.write("-" * 80 + "\\n")

            f.write("\\n=== API Errors ===\\n")
            if results["api_errors"]:
                for line_num, err_text in results["api_errors"][:10]:
                    f.write(f"  Line {line_num}: {err_text}\\n")
                if len(results["api_errors"]) > 10:
                    f.write(f"  ... and {len(results['api_errors']) - 10} more\\n")
            else:
                f.write("  No API errors found.\\n")

            f.write("\\n=== Pinecone Vector Errors ===\\n")
            if results["pinecone_errors"]:
                for line_num, err_text in results["pinecone_errors"][:10]:
                    f.write(f"  Line {line_num}: {err_text}\\n")
                if len(results["pinecone_errors"]) > 10:
                    f.write(f"  ... and {len(results['pinecone_errors']) - 10} more\\n")
            else:
                f.write("  No Pinecone errors found.\\n")

            f.write("\\n=== Zero Vector Errors ===\\n")
            if results["zero_vector_errors"]:
                temp_vector_ids: List[str] = []
                for _, err_text in results["zero_vector_errors"]:
                    match = re.search(r"Vector ID '([^']+)'", err_text)
                    if match:
                        temp_vector_ids.append(match.group(1))
                unique_ids_summary = set(temp_vector_ids)
                for vid_summary in list(unique_ids_summary)[:10]:
                    f.write(f"  Vector ID: {vid_summary}\\n")
                if len(unique_ids_summary) > 10:
                    f.write(
                        f"  ... and {len(unique_ids_summary) - 10} more unique vector IDs\\n"
                    )
            else:
                f.write("  No zero vector errors found.\\n")

            f.write("\\n=== Errors by Module ===\\n")
            if results["errors_by_module"]:
                for module, errors_list in sorted(
                    results["errors_by_module"].items(),
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
                        f.write(
                            f"  ... and {len(errors_list) - 5} more in this module\\n"
                        )
            else:
                f.write("  No module-specific errors categorized.\\n")

            f.write("\\n=== Other Errors ===\\n")
            if results["other_errors"]:
                for line_num, err_text in results["other_errors"][:10]:
                    f.write(f"  Line {line_num}: {err_text}\\n")
                if len(results["other_errors"]) > 10:
                    f.write(f"  ... and {len(results['other_errors']) - 10} more\\n")
            else:
                f.write("  No other errors found.\\n")

        print(f"\\\\nSummary saved to {summary_file}")
    # Check if log_file_to_analyze is not None before os.path.exists
    elif (
        results is None and log_file_to_analyze and os.path.exists(log_file_to_analyze)
    ):
        print(
            "\\\\nCould not generate summary report due to parsing issues (parse_log_file returned None)."
        )
    elif results is None and not (
        log_file_to_analyze and os.path.exists(log_file_to_analyze)
    ):
        # This case means parse_log_file was called with a non-existent file,
        # which parse_log_file itself should handle by printing an error and returning None.
        # Or, log_file_to_analyze was None to begin with (e.g. download failed and main didn't exit early)
        print(
            "\\\\nCould not generate summary report because the log file was not found or could not be processed."
        )


if __name__ == "__main__":
    main()
