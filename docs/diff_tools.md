# Diff Tools Guide

This guide provides instructions on how to use diff tools available in VS Code for the NYC Landmarks Vector DB project.

## Built-in VS Code Diff

VS Code has built-in diff functionality that you can use without any extensions:

1. Right-click on a file in the explorer and select "Select for Compare"
2. Right-click on another file and select "Compare with Selected"

## Partial Diff Extension

The Partial Diff extension allows you to compare selections within files:

1. Select text in a file
2. Right-click and select "Compare Text with Selection" or use the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) and type "Partial Diff: Select Text for Compare"
3. Select another piece of text
4. Right-click and select "Compare Text with Clipboard" or use the Command Palette and type "Partial Diff: Compare Text with Previous Selection"

### Keyboard Shortcuts

- `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac) -> Type "Partial Diff" to see all available commands

### Use Cases

- Compare two functions in the same file
- Compare a piece of code before and after changes
- Compare vector embeddings output by selecting the vector values

## Diff Extension

The Diff extension provides a simple way to compare two opened files:

1. Open two files you want to compare
2. Use the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) and type "Diff: Compare Active File With..."
3. Select the file you want to compare against

## Using Diff with Vector Data

When working with vector embeddings, you can:

1. Save vector data to text files (using numpy's `savetxt` or similar)
2. Use the diff tools to compare the files
3. For visual comparison, consider using the `diff` command in the Makefile which calls our custom diff tool for comparing vectors with plot visualizations

## Git Integration

For Git-based diffing:

1. Use VS Code's built-in Source Control panel (`Ctrl+Shift+G` or `Cmd+Shift+G`)
2. Click on any modified file to see the diff view
3. Right-click on a file and select "Compare with Previous Version" to see changes

## Makefile Integration

Our project includes a Makefile with a `diff` target that shows usage examples of our custom Python-based diff tool:

```bash
make diff
```

This will show examples of how to compare files, vectors, and DataFrames using our custom diff tool.
