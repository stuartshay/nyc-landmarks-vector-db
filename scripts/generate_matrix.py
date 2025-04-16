import argparse
import json
import math
import sys


def generate_matrix(
    total_records: int,
    api_page_size: int,
    job_batch_size: int,
    start_page_override: int = None,
    end_page_override: int = None,
) -> str:
    """
    Generates a GitHub Actions matrix configuration JSON for batch processing.

    Args:
        total_records: The total number of records to process.
        api_page_size: How many records are fetched per API call.
        job_batch_size: How many API pages each matrix job should handle.
        start_page_override: Optional override for the starting page number.
        end_page_override: Optional override for the ending page number.

    Returns:
        A JSON string representing the matrix configuration.
    """
    if api_page_size <= 0:
        raise ValueError("API page size must be positive.")
    if job_batch_size <= 0:
        raise ValueError("Job batch size must be positive.")
    if total_records < 0:
        raise ValueError("Total records cannot be negative.")

    if total_records == 0:
        return json.dumps({"include": []})  # No jobs needed if no records

    total_pages = math.ceil(total_records / api_page_size)

    # Apply page range overrides if provided
    effective_start_page = start_page_override if start_page_override is not None else 1
    effective_end_page = (
        end_page_override if end_page_override is not None else total_pages
    )

    # Validate page range
    if effective_start_page < 1:
        raise ValueError(f"Start page ({effective_start_page}) cannot be less than 1")
    if effective_end_page > total_pages:
        print(
            f"Warning: End page ({effective_end_page}) exceeds total pages ({total_pages}), using {total_pages} instead",
            file=sys.stderr,
        )
        effective_end_page = total_pages
    if effective_start_page > effective_end_page:
        raise ValueError(
            f"Start page ({effective_start_page}) cannot be greater than end page ({effective_end_page})"
        )

    print(
        f"Generating matrix for pages {effective_start_page} to {effective_end_page}",
        file=sys.stderr,
    )

    matrix_includes = []
    for i in range(effective_start_page - 1, effective_end_page, job_batch_size):
        start_page = i + 1
        end_page = min(i + job_batch_size, effective_end_page)
        matrix_includes.append({"start_page": start_page, "end_page": end_page})

    # Output the matrix in the format GitHub Actions expects
    # {"include": [ { "start_page": 1, "end_page": 5 }, ... ]}
    return json.dumps({"include": matrix_includes})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate GitHub Actions matrix for batch processing."
    )
    parser.add_argument(
        "--total-records",
        type=int,
        required=True,
        help="Total number of records to process.",
    )
    parser.add_argument(
        "--api-page-size",
        type=int,
        required=True,
        help="Number of records per API page.",
    )
    parser.add_argument(
        "--job-batch-size", type=int, required=True, help="Number of API pages per job."
    )
    parser.add_argument(
        "--start-page-override",
        type=int,
        required=False,
        help="Override for starting page number.",
    )
    parser.add_argument(
        "--end-page-override",
        type=int,
        required=False,
        help="Override for ending page number.",
    )

    args = parser.parse_args()

    try:
        matrix_json = generate_matrix(
            args.total_records,
            args.api_page_size,
            args.job_batch_size,
            args.start_page_override,
            args.end_page_override,
        )
        print(matrix_json)  # Output the JSON to stdout
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
