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


def parse_log_file(log_file):
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
    api_errors = []
    pinecone_errors = []
    zero_vector_errors = []
    other_errors = []
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
    print(f"Found {len(api_errors)} API errors")
    api_error_summary = Counter(
        [
            (
                re.search(r"url: ([^\s]+)", err[1]).group(1)
                if re.search(r"url: ([^\s]+)", err[1])
                else err[1]
            )
            for _, err in enumerate(api_errors)
        ]
    )
    for url, count in api_error_summary.most_common():
        print(f"  {url}: {count} occurrences")

    print("\n=== Pinecone Vector Errors ===")
    print(f"Found {len(pinecone_errors)} Pinecone errors")
    if pinecone_errors:
        print("Sample errors:")
        for i, (line_num, error) in enumerate(pinecone_errors[:5]):
            print(
                f"  Line {line_num}: {error[:100]}..."
                if len(error) > 100
                else f"  Line {line_num}: {error}"
            )
        if len(pinecone_errors) > 5:
            print(f"  ... and {len(pinecone_errors) - 5} more")

    print("\n=== Zero Vector Errors ===")
    print(f"Found {len(zero_vector_errors)} zero vector errors")
    if zero_vector_errors:
        # Extract vector IDs with format problems
        vector_ids = []
        for _, error in zero_vector_errors:
            match = re.search(r"Vector ID '([^']+)'", error)
            if match:
                vector_ids.append(match.group(1))

        # Print unique vector IDs with problems
        unique_ids = set(vector_ids)
        print(f"  {len(unique_ids)} unique problematic vector IDs")
        for i, vid in enumerate(list(unique_ids)[:10]):
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
        for i, (line_num, error) in enumerate(other_errors[:10]):
            print(
                f"  Line {line_num}: {error[:100]}..."
                if len(error) > 100
                else f"  Line {line_num}: {error}"
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

    # Save results to a summary file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = f"github_log_analysis_{timestamp}.txt"

    print(f"\nSummary saved to {summary_file}")


if __name__ == "__main__":
    main()
