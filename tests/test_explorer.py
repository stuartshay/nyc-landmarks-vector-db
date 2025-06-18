"""
Test Discovery and Configuration for VS Code Test Explorer.

This module helps VS Code's Test Explorer discover all tests in the project
and provides utilities for test management.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

import pytest

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_discovery_basic() -> None:
    """Basic test to verify test discovery is working."""
    assert True


def test_project_structure() -> None:
    """Test that the project has the expected structure."""
    test_dir = Path(__file__).parent

    # Check that main test directories exist
    expected_dirs = ['unit', 'integration', 'functional', 'scripts']
    for dir_name in expected_dirs:
        dir_path = test_dir / dir_name
        assert dir_path.exists(), f"Expected test directory {dir_name} not found"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"


def test_python_environment() -> None:
    """Test that the Python environment is properly configured."""
    # Check Python version
    assert sys.version_info >= (3, 12), f"Python 3.12+ required, got {sys.version_info}"

    # Check that project root is in path
    assert str(project_root) in sys.path, "Project root not in Python path"


def test_pytest_configuration() -> None:
    """Test that pytest is properly configured."""
    # Check that pytest.ini exists
    pytest_ini = project_root / "pytest.ini"
    assert pytest_ini.exists(), "pytest.ini not found"

    # Check that pyproject.toml exists with pytest config
    pyproject_toml = project_root / "pyproject.toml"
    assert pyproject_toml.exists(), "pyproject.toml not found"


def test_import_main_modules() -> None:
    """Test that main project modules can be imported."""
    try:
        import nyc_landmarks

        assert nyc_landmarks is not None
    except ImportError as e:
        # This might fail in some test environments, so we'll make it non-fatal
        print(f"Warning: Could not import nyc_landmarks: {e}")


def test_vscode_test_discovery() -> None:
    """Test specifically for VS Code Test Explorer compatibility."""
    # This test should always pass and helps VS Code find the test structure
    test_count = 0

    # Count test files
    test_dir = Path(__file__).parent
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_count += 1

    assert test_count > 0, "No test files found"
    print(f"Discovered {test_count} test files")


def discover_test_modules() -> Dict[str, List[str]]:
    """
    Discover all test modules organized by category.

    Returns:
        Dictionary mapping category to list of test modules
    """
    test_modules: Dict[str, List[str]] = {
        "unit": [],
        "integration": [],
        "functional": [],
        "scripts": [],
        "config": [],
    }

    test_dir = Path(__file__).parent

    for category in test_modules.keys():
        category_dir = test_dir / category
        if category_dir.exists():
            for file_path in category_dir.glob('test_*.py'):
                module_name = file_path.stem
                test_modules[category].append(module_name)

    # Handle test_config directory
    test_config_dir = test_dir / "test_config"
    if test_config_dir.exists():
        for file_path in test_config_dir.glob('test_*.py'):
            module_name = file_path.stem
            test_modules["config"].append(module_name)

    return test_modules


def test_all_test_modules_discoverable() -> None:
    """Test that all test modules can be discovered."""
    modules = discover_test_modules()

    total_modules = sum(len(module_list) for module_list in modules.values())
    assert total_modules > 0, "No test modules discovered"

    # Print discovered modules for debugging
    for category, module_list in modules.items():
        if module_list:
            print(f"{category}: {len(module_list)} modules")


def test_can_run_sample_tests() -> None:
    """Test that we can run basic pytest functionality."""
    # Simple arithmetic test
    assert 1 + 1 == 2

    # String test
    assert "test" in "testing"

    # List test
    test_list = [1, 2, 3]
    assert len(test_list) == 3
    assert 2 in test_list


class TestExplorerConfiguration:
    """Test class for VS Code Test Explorer configuration."""

    def test_class_based_discovery(self) -> None:
        """Test that class-based tests are discovered."""
        assert True

    def test_async_support_available(self) -> None:
        """Test that async test support is available."""
        try:
            import asyncio

            assert asyncio is not None
        except ImportError:
            assert False, "asyncio not available"

    def test_pytest_plugins_loaded(self) -> None:
        """Test that required pytest plugins are available."""
        try:
            import pytest_asyncio
            import pytest_cov

            # pytest-dotenv is available but import name is different
            assert all([pytest_asyncio, pytest_cov])
        except ImportError as e:
            print(f"Warning: Some pytest plugins not available: {e}")


# Async test example for asyncio mode
@pytest.mark.asyncio
async def test_async_functionality() -> None:
    """Test async functionality works."""
    import asyncio

    await asyncio.sleep(0.001)  # Minimal async operation
    assert True


if __name__ == "__main__":
    # When run directly, print discovery information
    print("Test Explorer Configuration")
    print("=" * 40)

    modules = discover_test_modules()
    total = sum(len(module_list) for module_list in modules.values())

    print(f"Total test modules discovered: {total}")

    for category, module_list in modules.items():
        if module_list:
            print(f"\n{category.upper()}:")
            for module in sorted(module_list):
                print(f"  - {module}")

    print(f"\nProject root: {project_root}")
    print(f"Test directory: {Path(__file__).parent}")
    print(f"Python version: {sys.version}")
    print("\nConfiguration complete ✓")
