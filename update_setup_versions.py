#!/usr/bin/env python3
"""
Script to update dependency versions in setup.py to their latest versions.
This script modifies the install_requires and extras_require sections in setup.py
to ensure packages use the latest available versions.
"""

import re
import subprocess  # nosec B404 - Used safely with fixed package names
import sys
from typing import Optional


def get_latest_version(package: str) -> Optional[str]:
    """Get the latest version of a package from PyPI."""
    try:
        # Use pip search to find latest package version - safe with fixed command structure
        result = (
            subprocess.run(  # nosec B607, B603 - Only running pip with package names
                ["pip", "install", f"{package}==", "--quiet"],
                capture_output=True,
                text=True,
            )
        )
        output = result.stderr

        # Extract the latest version
        match = re.search(r"from versions: ([0-9.]+)", output)
        if match:
            return match.group(1)

        # Alternative pattern for some pip versions
        match = re.search(r"\(from versions: ([^,\)]+)", output)
        if match:
            versions = match.group(1).strip()
            return versions.split(",")[-1].strip()

        print(f"Could not determine version for {package}")
        return None
    except subprocess.CalledProcessError:
        print(f"Error checking version for {package}")
        return None


def update_setup_py(filename: str = "setup.py") -> None:
    """Update the dependency versions in setup.py."""
    try:
        with open(filename, "r") as file:
            content = file.read()

        # Update install_requires section
        install_requires_pattern = r"install_requires=\[\s*(.*?)\s*\]"
        install_requires_match = re.search(install_requires_pattern, content, re.DOTALL)

        if install_requires_match:
            install_requires_text = install_requires_match.group(1)
            package_lines = re.findall(
                r'^\s*"([^"]+?)(?:>=.+?)?"', install_requires_text, re.MULTILINE
            )

            updated_content = content
            for package in package_lines:
                package_name = package.split("[")[
                    0
                ]  # Handle packages with extras like 'package[extra]'
                latest_version = get_latest_version(package_name)
                if latest_version:
                    print(f"Updating {package} to version {latest_version}")
                    # Replace version pattern for this package
                    pattern = rf'("{re.escape(package)})(?:>=.+?)?"'
                    replacement = rf'\1>={latest_version}"'
                    updated_content = re.sub(pattern, replacement, updated_content)

            # Update extras_require section - dev dependencies
            extras_pattern = r'"dev":\s*\[\s*(.*?)\s*\]'
            extras_match = re.search(extras_pattern, updated_content, re.DOTALL)

            if extras_match:
                extras_text = extras_match.group(1)
                package_lines = re.findall(
                    r'^\s*"([^"]+?)(?:>=.+?)?"', extras_text, re.MULTILINE
                )

                for package in package_lines:
                    package_name = package.split("[")[0]
                    latest_version = get_latest_version(package_name)
                    if latest_version:
                        print(
                            f"Updating dev dependency {package} to version {latest_version}"
                        )
                        pattern = rf'("{re.escape(package)})(?:>=.+?)?"'
                        replacement = rf'\1>={latest_version}"'
                        updated_content = re.sub(pattern, replacement, updated_content)

            # Write updated content back to setup.py
            with open(filename, "w") as file:
                file.write(updated_content)

            print("setup.py updated with latest dependency versions!")
        else:
            print("Could not find install_requires section in setup.py")

    except Exception as e:
        print(f"Error updating setup.py: {e}")
        sys.exit(1)


if __name__ == "__main__":
    update_setup_py()
