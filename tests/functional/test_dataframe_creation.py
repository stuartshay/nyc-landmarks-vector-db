import logging

import pandas as pd
import pytest

# Configure logging for tests
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Use DEBUG for detailed test logs


@pytest.mark.functional
def test_namespace_dataframe_creation():
    """
    Tests the creation of the namespace DataFrame from mock stats data,
    replicating the logic in cell 8 of pinecone_db_stats.ipynb.
    Ensures type casting prevents pandas TypeError.
    """
    logger.info("--- Starting test_namespace_dataframe_creation ---")

    # 1. Mock data similar to Pinecone stats response
    # Using standard Python types
    mock_namespaces = {
        "landmarks": {"vector_count": 188},
        "test-ns": {"vector_count": 10},
        "": {"vector_count": 5},  # Representing default namespace
    }
    mock_total_vector_count = 203  # Sum of counts above

    logger.debug(f"Mock namespaces: {mock_namespaces}")
    logger.debug(f"Mock total_vector_count: {mock_total_vector_count}")

    # 2. Replicate logic from notebook cell 8
    namespace_data = []
    total_vector_count = int(mock_total_vector_count)  # Ensure int

    logger.debug("Processing mock namespaces...")
    if isinstance(mock_namespaces, dict):
        for ns_name, ns_stats in mock_namespaces.items():
            if isinstance(ns_stats, dict):
                vector_count = int(ns_stats.get("vector_count", 0))
                percentage = float(
                    (vector_count / total_vector_count * 100)
                    if total_vector_count > 0
                    else 0
                )

                namespace_data.append(
                    {
                        "Namespace": ns_name if ns_name else "default",
                        "Vector Count": vector_count,  # Already cast
                        "Percentage": percentage,  # Already cast
                    }
                )
                logger.debug(
                    f"Processed namespace '{ns_name}': count={vector_count}, percentage={percentage:.2f}%"
                )
            else:
                logger.warning(f"Skipping invalid ns_stats item: {ns_stats}")
    else:
        logger.error("'mock_namespaces' is not a dict.")
        pytest.fail("'mock_namespaces' should be a dictionary for this test.")

    logger.debug(f"Constructed namespace_data list: {namespace_data}")

    # 3. Attempt DataFrame creation using dictionary of lists
    namespace_df = None
    try:
        logger.info(
            "Attempting to create DataFrame column by column using pd.Series..."
        )

        # Extract data into lists with standard Python types
        namespaces_list = [str(item["Namespace"]) for item in namespace_data]
        vector_counts_list = [
            int(item["Vector Count"]) for item in namespace_data
        ]  # Already int from step 2
        percentages_list = [
            float(item["Percentage"]) for item in namespace_data
        ]  # Already float from step 2

        # Create DataFrame column by column
        namespace_df = pd.DataFrame()
        namespace_df["Namespace"] = pd.Series(namespaces_list, dtype=str)
        # Use pandas nullable integer type Int64
        namespace_df["Vector Count"] = pd.Series(vector_counts_list, dtype="Int64")
        namespace_df["Percentage"] = pd.Series(percentages_list, dtype=float)

        logger.info("DataFrame created column by column successfully.")
        logger.debug(f"DataFrame head:\n{namespace_df.head()}")
        logger.debug(f"DataFrame dtypes:\n{namespace_df.dtypes}")

    except Exception as e:
        logger.exception(f"Error creating DataFrame: {e}", exc_info=True)
        pytest.fail(f"DataFrame creation failed with error: {e}")

    # 4. Assertions
    assert namespace_df is not None, "DataFrame creation failed (namespace_df is None)."
    assert not namespace_df.empty, "Created DataFrame is empty."
    assert list(namespace_df.columns) == [
        "Namespace",
        "Vector Count",
        "Percentage",
    ], "DataFrame columns mismatch."
    assert (
        namespace_df["Vector Count"].dtype == "Int64"
    ), "Vector Count column dtype is not Int64."
    assert (
        namespace_df["Percentage"].dtype == float
    ), "Percentage column dtype is not float."
    assert len(namespace_df) == len(
        mock_namespaces
    ), "DataFrame row count doesn't match mock data."

    logger.info("DataFrame created and validated successfully.")
    logger.info("--- Finished test_namespace_dataframe_creation ---")
