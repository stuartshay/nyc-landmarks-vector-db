# NYC Landmarks Vector DB Co-Pilot Instructions

## Project Context Reference System

When working on this project, please reference the memory bank folder which contains
essential project context files. These files are maintained to provide up-to-date
information about the project's status, goals, and technical details.

## Memory Bank Files

When answering questions or providing assistance, please refer to the following memory
bank files to inform your responses:

1. **activeContext.md**: Contains information about the current work focus, recent
   changes, next steps, active decisions, challenges, and team collaboration. Reference
   this when asked about current priorities or recent developments.

1. **productContext.md**: Contains product-related information, requirements, and
   specifications. Reference this when answering questions about product features or
   requirements.

1. **progress.md**: Tracks project progress and milestone achievements. Reference this
   when asked about project status or timelines.

1. **projectbrief.md**: Contains the overall project description, goals, and scope.
   Reference this when providing high-level project information or context.

1. **systemPatterns.md**: Documents system architecture patterns and design decisions.
   Reference this when discussing system design or architectural questions.

1. **techContext.md**: Provides technical context, specifications, and constraints.
   Reference this when answering technical questions about implementations or technology
   choices.

## Instructions for Co-Pilot

1. **Reference Memory Bank**: Before answering questions, check the relevant memory bank
   files to ensure your responses align with the most up-to-date project context.

1. **Prioritize Context**: When there's a conflict between general knowledge and
   project-specific information in the memory bank, prioritize the project-specific
   information.

1. **Maintain Consistency**: Ensure your suggestions and solutions maintain consistency
   with the established patterns, decisions, and goals documented in the memory bank.

1. **Update References**: If you notice information that should be updated in the memory
   bank files, suggest updates to keep the memory bank current.

1. **Follow Established Patterns**: When suggesting new code or solutions, follow the
   system patterns and technical context established in the memory bank.

1. **Technology Stack Awareness**: Use the technical context to inform your suggestions,
   ensuring they align with the project's technology stack and constraints.

## Additional Project-Specific Guidelines

- The project uses Python for backend processing with a focus on PDF text extraction and
  vector database operations
- APIs are designed for vector search and chat functionality
- Data sources include PostgreSQL database and CoreDataStore API with a toggleable
  configuration
- External services include OpenAI (for embeddings), Pinecone (vector database), Azure
  (storage), and PostgreSQL
- Environmental variables are managed through the .env file and should be referenced in
  code through the config module

## Code Cleanup and Quality Guidelines

When performing code cleanup, refactoring, or addressing linting issues:

1. **Always run pre-commit on all files** to ensure consistent code quality:

   ```bash
   pre-commit run --all-files
   ```

1. **Use Makefile targets** for standard development tasks:

   ```bash
   # Run linting checks
   make lint

   # Format code
   make format

   # Run pre-commit on all files
   make pre-commit

   # Check development environment
   make check-env

   # Run tests
   make test
   ```

1. **Code cleanup workflow**:

   - Address all pre-commit findings before considering cleanup complete
   - Verify functionality after cleanup by running the test suite
   - Never break existing functionality during cleanup activities
   - Use `utils/check_dev_env.py` to verify environment setup after changes

1. **Quality standards**:

   - Follow PEP 8 style guide
   - Use Black for code formatting (88 character line length)
   - Sort imports with isort
   - Use type hints for all functions and methods
   - Maintain at least 80% test coverage

## Package Management Guidelines

1. **Dual Dependency Management**:

   - `setup.py` defines package metadata and flexible dependencies with minimum version
     constraints (`>=`)
   - `requirements.txt` contains pinned, exact versions for reproducible environments
   - Both files must be kept in sync using the `sync_versions.sh` script

1. **Adding New Dependencies**:

   - Always add new dependencies to `setup.py` first with appropriate version
     constraints
   - Then generate `requirements.txt` using:
     `pip-compile --constraint=constraints.txt --output-file=requirements.txt`
   - Commit both files together as a single change

1. **Version Management**:

   - Use `>=` version constraints in `setup.py` for flexibility
   - The `requirements.txt` file should have exact versions with `==` for
     reproducibility
   - Avoid using specific versions in `setup.py` unless absolutely necessary

1. **Dependency Updates**:

   - Dependabot manages automated updates, checking for security vulnerabilities
   - Our GitHub workflow automatically syncs versions between files when Dependabot
     creates updates
   - When suggesting manual dependency updates, recommend updating both files using the
     sync script
   - To manually sync versions: `./sync_versions.sh`

1. **Environment Setup**:

   - For development environments, recommend using the `setup_env.sh` script
   - For tests and CI/CD, use `requirements.txt` to ensure consistent environments
   - For package distribution, reference the `setup.py` configuration

1. **Specific Package Requirements**:

   - Pinecone SDK: Must use v6.0.2 or later (not the legacy client)
   - Follow the PyPI page at https://pypi.org/project/pinecone/
   - For updating Pinecone SDK specifically, use `./update_pinecone.sh`

1. **Python Version**:

   - Project requires Python 3.12+
   - Virtual environment should be created using `venv312/`
   - All dependencies should be compatible with Python 3.12+

## Test Execution Optimization Rules

When running tests, follow these rules to optimize execution time and provide focused feedback:

### 1. **Component-Specific Testing Priority**

- **Run specific tests first** when working on a particular component or fixing a specific issue
- **Run broader test suites** only when necessary (final validation, core changes, or user request)
- **Avoid running all tests** unless explicitly requested or when changes affect multiple components

### 2. **Test Execution Guidelines by Scope**

#### **Specific Function/Method Changes**

```bash
# Test the specific function
pytest tests/unit/test_module.py::test_specific_function -v

# Test the entire test class if multiple related methods changed
pytest tests/unit/test_module.py::TestSpecificClass -v
```

#### **Single Module Changes**

```bash
# Test the specific module
pytest tests/unit/test_module.py -v
pytest tests/integration/test_module_integration.py -v
```

#### **API Endpoint Changes**

```bash
# Test specific API endpoints
pytest tests/integration/test_query_api.py::test_specific_endpoint -v

# For API validation changes
pytest tests/integration/test_api_validation_logging.py -v
```

#### **Database/Vector Operations Changes**

```bash
# Test specific database operations
pytest tests/integration/test_pinecone_*.py::test_specific_functionality -v

# For Pinecone-specific changes
pytest tests/integration/test_pinecone_upsert.py -v
```

#### **Configuration/Settings Changes**

```bash
# Test configuration-related functionality
pytest tests/unit/test_config.py -v
pytest tests/integration/test_environment_*.py -v
```

### 3. **When to Run Broader Test Suites**

#### **Run Test Module** (when multiple functions in a file are affected):

```bash
pytest tests/unit/test_module.py -v
pytest tests/integration/test_module_integration.py -v
```

#### **Run Test Category** (when changes affect a specific type of functionality):

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Functional tests only
pytest tests/functional/ -v
```

#### **Run All Tests** (only when absolutely necessary):

```bash
# All tests - use sparingly, only for:
# - Final validation before completion
# - Changes to core infrastructure/shared components
# - User explicitly requests it
# - Pre-commit or CI/CD pipeline
pytest tests/ -v
```

### 4. **Test Selection Examples**

#### **Bug Fix Scenarios**

```bash
# Fixing metadata consistency bug
pytest tests/integration/test_pinecone_validation.py::test_metadata_consistency -v

# Fixing API validation error
pytest tests/integration/test_query_api.py::test_query_api_validation_errors -v

# Fixing retry logic
pytest tests/integration/test_pinecone_upsert.py::test_retry_logic_standalone -v
```

#### **Feature Development Scenarios**

```bash
# Adding new API endpoint
pytest tests/integration/test_query_api.py -v

# Adding new vector functionality
pytest tests/integration/test_pinecone_*.py -v

# Adding new logging feature
pytest tests/integration/test_*logging*.py -v
```

### 5. **Performance Considerations**

- **Integration tests** can take several minutes - run specific ones when possible
- **API tests** require running server - check API availability first
- **Pinecone tests** interact with external service - run targeted tests to save time
- **Unit tests** are fast - these can be run more broadly when in doubt

### 6. **Test Failure Response Strategy**

1. **Single test failure**: Fix and re-run that specific test
1. **Multiple related test failures**: Run the test module to verify fix
1. **Unrelated test failures**: Investigate if changes affected other components
1. **Run full suite**: Only after fixing specific issues and before final completion

### 7. **Communication Pattern**

When suggesting test execution, always specify:

- **Why** running specific tests (what component/functionality is being tested)
- **What** specific test command to run
- **When** to escalate to broader test execution

Example:

```
"Since we modified the retry logic in PineconeDB, let's run the specific retry test:
pytest tests/integration/test_pinecone_upsert.py::test_retry_logic_standalone -v

This will verify our fix without running the entire integration suite unnecessarily."
```

### 8. **Exception Cases**

Always run broader tests when:

- Changes affect shared utilities or base classes
- Modifying configuration or environment setup
- Refactoring core infrastructure components
- User explicitly requests comprehensive testing
- Final validation before task completion

When helping with this project, please regularly check the memory bank folder to provide
the most accurate and contextually appropriate assistance.
