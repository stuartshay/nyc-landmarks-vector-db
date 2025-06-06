# Memory Bank Guidelines

2025-06-05

This file provides instructions for agents working with documentation in the
`memory-bank` directory.

## Purpose of the Memory Bank

- The directory serves as a centralized place for project documentation and
  research notes. It helps track important decisions and improvements
  over time.
- Store implementation details, design patterns, performance optimizations,
  test strategies and other guides that support maintenance of the project.

## What Not to Store

- Do **not** place source code or configuration files here.
- Avoid personal notes or duplicated content already documented elsewhere
  (e.g. the project README or docstrings).

## Naming Conventions

- Use descriptive *kebab-case* file names, for example `test-improvements.md`
  or `api-design.md`.

## Document Format

- All documents must be in Markdown (`.md`).
- Begin each file with a clear title and date.
- Organize content with appropriate headings (H1, H2, H3).
- When updating content, modify existing documents instead of creating
  duplicates.

## Organization

- As the number of documents grows, create subdirectories by category
  (e.g. `architecture/`, `research/`, `improvements/`).

## Docs Folder

- The top-level `docs/` directory contains how‑to guides and developer
  documentation. Consult those files when you need project-specific examples
  (e.g. type checking or security remediation).

For an overview of available documents and categories, see `README.md` in this
directory.
