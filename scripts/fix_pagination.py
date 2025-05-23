#!/usr/bin/env python3
"""
This script fixes the pagination layout in the Wikipedia Integration Testing notebook.
It specifically targets Section 1 to put the pager on top and make it functional.
"""

import copy
import json

# Path to the source notebook
source_notebook = (
    "/workspaces/nyc-landmarks-vector-db/notebooks/wikipedia_integration_testing.ipynb"
)
# Path to the target notebook
target_notebook = "/workspaces/nyc-landmarks-vector-db/notebooks/wikipedia_integration_testing_fixed.ipynb"

# Load the notebook
with open(source_notebook, "r", encoding="utf-8") as f:
    notebook = json.load(f)

# Find the cell that needs to be modified - in Section 1, the one with the dashboard layout
fixed_cell_index = None
for i, cell in enumerate(notebook["cells"]):
    if cell["cell_type"] == "code":
        if (
            "dashboard = widgets.VBox([controls, status_label, output_area])"
            in "".join(cell["source"])
        ):
            fixed_cell_index = i
            break

if fixed_cell_index is not None:
    # This is the cell that needs to be fixed
    print(f"Found target cell at index {fixed_cell_index}")

    # Get the original cell's source code
    original_source = notebook["cells"][fixed_cell_index]["source"]

    # Locate where the dashboard layout is defined
    dashboard_line_index = None
    for i, line in enumerate(original_source):
        if "dashboard = widgets.VBox" in line:
            dashboard_line_index = i
            break

    if dashboard_line_index is not None:
        # Create a modified version with the corrected dashboard layout
        modified_source = copy.deepcopy(original_source)

        # Replace the dashboard layout line and any relevant lines
        # Find where the layout part begins
        layout_start_index = None
        for i, line in enumerate(original_source):
            if "# Layout the widgets" in line:
                layout_start_index = i
                break

        if layout_start_index is not None:
            # Keep all code up to the layout section
            modified_source = original_source[:layout_start_index]

            # Add the fixed layout code
            modified_source.extend(
                [
                    "# Layout the widgets - if they display properly in your environment\n",
                    "# Put the pagination controls at the top\n",
                    "controls = widgets.HBox([page_size_dropdown, page_number, prev_button, next_button])\n",
                    "# Position status label and controls above the output area\n",
                    "dashboard = widgets.VBox([\n",
                    "    status_label,  # Status label on top\n",
                    "    controls,      # Pagination controls below status\n",
                    "    output_area    # Output area at the bottom\n",
                    "])\n",
                    "\n",
                    "# Try displaying the widgets\n",
                    "try:\n",
                    "    display(dashboard)\n",
                    "except Exception as e:\n",
                    '    print(f"Note: Widget display error: {str(e)}. Use the alternative functions above instead.")\n',
                ]
            )

            # Update the notebook cell source
            notebook["cells"][fixed_cell_index]["source"] = modified_source

            # Save the modified notebook
            with open(target_notebook, "w", encoding="utf-8") as f:
                json.dump(notebook, f, indent=1)

            print(f"Fixed pagination layout saved to {target_notebook}")
        else:
            print("Could not locate the layout section in the cell")
    else:
        print("Could not locate the dashboard layout definition in the cell")
else:
    print("Could not find the cell that needs to be fixed")
