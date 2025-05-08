#!/usr/bin/env python3
"""
GitHub Action Log Analyzer

This script parses a GitHub Action log file and extracts warnings, errors,
and other important information to help diagnose issues in the workflow.
"""

import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def parse_log_file(log_file: str) -> Optional[Dict[str, Any]]:
    """Parse the GitHub Action log file and extract warnings and errors."""

    if not os.path.exists(log_file):
        print(f"Error: File {log_file} does not exist.")
        return

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


def main():
    """Main function to run the log analyzer."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_github_log.py <log_file>")
        return

    log_file = sys.argv[1]
    results = parse_log_file(log_file)

    if results:
        # Save results to a summary file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"github_log_analysis_{timestamp}.txt"

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"Log File: {log_file}\\n")
            f.write(f"Analysis Timestamp: {timestamp}\\n")
            f.write("-" * 80 + "\\n")
            f.write(f"Total errors: {results['error_count']}\\n")
            f.write(f"Total warnings: {results['warning_count']}\\n")
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

        print(f"\\nSummary saved to {summary_file}")
    elif results is None and os.path.exists(log_file):
        # This case implies parse_log_file returned None due to an internal issue
        # but the file itself exists. The function already prints an error.
        print("\\nCould not generate summary report due to parsing issues.")
    # If results is None because file doesn't exist, parse_log_file handles the print.


if __name__ == "__main__":
    main()
