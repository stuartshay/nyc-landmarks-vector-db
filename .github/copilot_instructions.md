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

   - Project requires Python 3.11+
   - Virtual environment should be created using `venv311/`
   - All dependencies should be compatible with Python 3.11+

When helping with this project, please regularly check the memory bank folder to provide
the most accurate and contextually appropriate assistance.
