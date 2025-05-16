# NYC Landmarks Vector Database - Jupyter Notebook Standards

This document outlines the standards and best practices for Jupyter notebooks in the NYC
Landmarks Vector Database project. Adherence to these standards ensures consistency,
maintainability, and reproducibility of notebook-based analyses and development.

## Notebook Structure

### 1. Header and Introduction

Each notebook must begin with:

- A clear title as an H1 markdown heading (`# Title`)
- A brief description of the notebook's purpose
- Date of creation/last major update
- Author information
- Any prerequisites or dependencies

Example:

```markdown
# Landmark Query Testing Notebook

This notebook demonstrates vector search capabilities against the NYC Landmarks vector database, including basic queries, filtering options, and performance metrics.

**Last Updated:** April 15, 2025
**Author:** Data Science Team

**Prerequisites:**
- Pinecone connection configured in .env
- Vector embeddings already stored in Pinecone index
```

### 2. Import Section

- All imports should be at the top of the notebook
- Imports should be organized in groups:
  - Standard library imports first
  - Third-party library imports second
  - Project module imports last
- Each group should be separated by a blank line
- Imports within groups should be alphabetized

Example:

```python
# Standard library imports
import os
import json
from datetime import datetime

# Third-party imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

# Project imports
from nyc_landmarks.vectordb import pinecone_db
from nyc_landmarks.embeddings import generator
```

### 3. Logical Section Organization

- Divide notebook into clear logical sections using markdown headers
- Each section should have a descriptive H2 (`##`) or H3 (`###`) heading
- Include a brief description of what each section does
- Use consistent section patterns across notebooks when possible:
  - Setup and Configuration
  - Data Loading
  - Processing/Analysis
  - Visualization
  - Results/Conclusion

### 4. Documentation and Comments

- Each code cell performing a significant operation should be preceded by a markdown
  cell explaining:
  - What the code is doing
  - Why it's being done (business/technical context)
  - Any important assumptions or constraints
- Complex code blocks should include inline comments
- Include explanations of important parameters and their impact

### 5. Conclusion

- Each notebook should end with a conclusion section
- Summarize key findings or outcomes
- Identify any next steps or further work

## Code Quality Standards

### 1. Style and Formatting

- All Python code must follow PEP 8 style guidelines
- Maximum line length of 88 characters (Black default)
- Use consistent variable naming:
  - `snake_case` for variables and functions
  - `PascalCase` for classes
  - `ALL_CAPS` for constants
- Pre-commit hooks will enforce:
  - Black formatting
  - isort import sorting
  - flake8 linting

### 2. Cell Output Management

- Cell outputs must never be committed to version control
- The `nbstripout` pre-commit hook will automatically clear outputs
- For sharing results:
  - Execute the notebook using `jupyter nbconvert`
  - Save executed notebooks in the `test_output/notebooks` directory

### 3. Function Definitions

- Complex operations should be encapsulated in functions
- Each function must include a docstring that describes:
  - Purpose of the function
  - Parameters with types and descriptions
  - Return values with types and descriptions
  - Any exceptions that might be raised

Example:

```python
def filter_landmarks_by_borough(df, borough, min_score=0.7):
    """
    Filter landmark dataframe to only include entries from a specific borough with minimum score.

    Args:
        df (pd.DataFrame): DataFrame containing landmark data
        borough (str): Borough name to filter for (e.g., 'Manhattan', 'Brooklyn')
        min_score (float, optional): Minimum relevance score (0-1). Defaults to 0.7.

    Returns:
        pd.DataFrame: Filtered dataframe containing only matching landmarks

    Raises:
        ValueError: If borough is not one of the five NYC boroughs
    """
    valid_boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    if borough not in valid_boroughs:
        raise ValueError(f"Borough must be one of {valid_boroughs}")

    return df[(df["borough"] == borough) & (df["score"] >= min_score)]
```

### 4. Variable Naming

- Use descriptive, unambiguous variable names
- Avoid single-letter variables except in specific cases (e.g., `i` for loop indices)
- Be consistent with naming patterns throughout the notebook
- Prefix temporary or intermediate variables appropriately

### 5. Error Handling

- Include appropriate error handling for operations that might fail
- Use try/except blocks for potentially problematic code
- Include informative error messages

## Execution and Testing

### 1. Sequential Execution

- Notebooks should be designed to run from top to bottom sequentially
- Avoid relying on out-of-order execution
- Test notebook execution using:

```
python scripts/run_notebook.py notebooks/your_notebook.ipynb
```

### 2. Headless Execution

- All notebooks must execute successfully in headless environments
- Avoid code that requires manual interaction
- For visualization components that might fail in headless mode, include conditionals:

```python
import os

# Only show interactive plots when not in CI environment
if os.environ.get("CI") != "true":
    plt.show()
else:
    plt.savefig("output_figure.png")
```

### 3. Reproducibility

- Set random seeds for any operations using randomness
- Document any external dependencies or data sources
- Include version information for critical libraries
- Consider using environment variables or config files for sensitive information

### 4. Performance Considerations

- Include execution timing for expensive operations
- For long-running cells, include progress bars (e.g., tqdm)
- Consider chunking large data operations
- Add memory usage monitoring for large-scale data processing

Example:

```python
from time import time
import psutil
import os


def log_resource_usage(func):
    """Decorator to log execution time and memory usage of a function."""

    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        start_time = time()

        result = func(*args, **kwargs)

        elapsed_time = time() - start_time
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Function '{func.__name__}' executed in {elapsed_time:.2f} seconds")
        print(f"Memory usage: {mem_after:.2f} MB (Δ {mem_after - mem_before:.2f} MB)")

        return result

    return wrapper


@log_resource_usage
def process_large_dataset(data):
    # Processing code here
    pass
```

## Visualization Standards

### 1. Plot Formatting

- All visualizations should include:
  - Descriptive title
  - Labeled axes with units
  - Legend when multiple data series are shown
  - Appropriate color schemes (colorblind-friendly when possible)
- Use consistent styling across plots in the same notebook

### 2. Interactive Visualizations

- Consider using interactive visualizations for complex data exploration
- Ensure interactive elements degrade gracefully in non-interactive environments
- Document any interactivity features in markdown

### 3. Plot Sizing

- Set appropriate figure sizes for visualizations
- Consider the context in which the plot will be viewed
- For multiple related plots, maintain consistent sizing

## Version Control and Collaboration

### 1. Pre-commit Hooks

The following pre-commit hooks are applied to notebooks:

- `nbstripout`: Clears all cell outputs
- `nbqa-black`: Formats code cells according to Black standards
- `nbqa-isort`: Sorts imports
- `nbqa-flake8`: Performs linting

### 2. Review Process

- All notebook changes should be reviewed before merging to main
- Reviewers should run the notebook independently to verify results
- Focus on both code quality and analytical approach

### 3. Notebook Execution Results

- Execute notebooks using the provided scripts:
  ```bash
  # Run a single notebook
  python scripts/run_notebook.py notebooks/your_notebook.ipynb

  # Run all notebooks
  python scripts/run_all_notebooks.py
  ```
- Examine the execution outputs in `test_output/notebooks/`
- Verify all cells executed without errors
- Review outputs for correctness

## Example Notebook Template

````
# Notebook Title

Brief description of the notebook's purpose and context.

## Setup and Configuration

### Environment Setup
```python
# Standard library imports
import os
import json

# Third-party imports
import numpy as np
import pandas as pd

# Project imports
from nyc_landmarks.config import settings
````

### Configuration Parameters

```python
# Set configuration parameters
LANDMARK_LIMIT = 100
SCORE_THRESHOLD = 0.75
```

## Data Loading and Preparation

Description of the data sources and loading process.

```python
# Load the data
data = pd.read_csv("path/to/data.csv")

# Preview the data
data.head()
```

## Analysis

Description of the analysis approach.

```python
# Perform analysis
results = process_data(data)

# Show results
results.describe()
```

## Visualization

Explanation of what the visualization shows.

```python
# Create visualization
plt.figure(figsize=(10, 6))
plt.plot(results["x"], results["y"])
plt.title("Analysis Results")
plt.xlabel("X Axis Label")
plt.ylabel("Y Axis Label")
plt.show()
```

## Conclusion

Summary of findings and next steps.

```

By following these standards, we ensure that all notebooks in the project are consistent, maintainable, and reproducible, facilitating collaboration and knowledge sharing across the team.
```
