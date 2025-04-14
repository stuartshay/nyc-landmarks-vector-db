import argparse
import json
import math
import sys

def generate_matrix(total_records: int, api_page_size: int, job_batch_size: int) -> str:
    """
    Generates a GitHub Actions matrix configuration JSON for batch processing.

    Args:
        total_records: The total number of records to process.
        api_page_size: How many records are fetched per API call.
        job_batch_size: How many API pages each matrix job should handle.

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
        return json.dumps({"include": []}) # No jobs needed if no records

    total_pages = math.ceil(total_records / api_page_size)

    matrix_includes = []
    for i in range(0, total_pages, job_batch_size):
        start_page = i + 1
        end_page = min(i + job_batch_size, total_pages)
        matrix_includes.append({"start_page": start_page, "end_page": end_page})

    # Output the matrix in the format GitHub Actions expects
    # {"include": [ { "start_page": 1, "end_page": 5 }, ... ]}
    return json.dumps({"include": matrix_includes})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate GitHub Actions matrix for batch processing.")
    parser.add_argument("--total-records", type=int, required=True, help="Total number of records to process.")
    parser.add_argument("--api-page-size", type=int, required=True, help="Number of records per API page.")
    parser.add_argument("--job-batch-size", type=int, required=True, help="Number of API pages per job.")

    args = parser.parse_args()

    try:
        matrix_json = generate_matrix(args.total_records, args.api_page_size, args.job_batch_size)
        print(matrix_json) # Output the JSON to stdout
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
