#!/bin/bash
# sync_versions.sh
#
# This script synchronizes package versions between requirements.txt and setup.py.
# It extracts exact versions from requirements.txt and updates the corresponding
# versions in setup.py to use >= version constraints.
#
# Usage: ./scripts/ci/sync_versions.sh
#
# Note: This script is designed to be run from the root directory of the project.

set -e  # Exit immediately if a command exits with a non-zero status

echo "Starting version synchronization between requirements.txt and setup.py"

# Check if we're in the root directory
if [ ! -f "requirements.txt" ] || [ ! -f "setup.py" ]; then
    echo "Error: This script must be run from the root directory of the project."
    echo "Make sure both requirements.txt and setup.py exist."
    exit 1
fi

# Create a temporary file for processing
TEMP_FILE=$(mktemp)

echo "Extracting package versions from requirements.txt..."

# First, extract direct dependencies from setup.py
DIRECT_DEPS_FILE=$(mktemp)
trap 'rm -f "$TEMP_FILE" "$DIRECT_DEPS_FILE"' EXIT

echo "Extracting direct dependencies from setup.py..."
grep -E '^\s*"[a-zA-Z0-9_.-]+[>=<~]' setup.py | sed 's/.*"\([^"]*\)".*/\1/' | sed 's/[>=<~!].*//' > "$DIRECT_DEPS_FILE"

echo "Direct dependencies found in setup.py:"
cat "$DIRECT_DEPS_FILE"

# Extract package names and versions from requirements.txt
# Format: package==version or package>=version
while IFS= read -r line; do
    # Skip empty lines, comments, and lines without version pins
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# || ! "$line" =~ [=\~\>\<] ]]; then
        continue
    fi

    # Extract package name and version
    if [[ "$line" =~ ^([a-zA-Z0-9_.-]+)[=\~\>\<]+([0-9a-zA-Z.-]+) ]]; then
        package="${BASH_REMATCH[1]}"
        version="${BASH_REMATCH[2]}"

        # Convert package name to lowercase for case-insensitive comparison
        package_lower=$(echo "$package" | tr '[:upper:]' '[:lower:]')

        # Check if this package is a direct dependency
        if ! grep -q -i "^${package}$" "$DIRECT_DEPS_FILE" && ! grep -q -i "^${package_lower}$" "$DIRECT_DEPS_FILE"; then
            echo "  Skipping $package (transitive dependency)"
            continue
        fi

        # Special cases for package name mapping
        case "$package_lower" in
            "pypdf")
                # Already correct in setup.py
                ;;
            "pinecone")
                # Note: Was pinecone-client before, but now just pinecone
                ;;
            *)
                # Standard package
                ;;
        esac

        echo "$package:$version" >> "$TEMP_FILE"
    fi
done < requirements.txt

echo "Updating package versions in setup.py..."

# Read setup.py into a variable for processing
setup_content=$(cat setup.py)

# Process each package and update its version in setup.py
while IFS=: read -r package version; do
    # Skip empty lines
    if [ -z "$package" ]; then
        continue
    fi

    # Convert package name to lowercase for matching
    package_lower=$(echo "$package" | tr '[:upper:]' '[:lower:]')

    # Look for package in install_requires section with version constraint
    # Match patterns like: "package>=1.0.0" or "package==1.0.0" or "package"
    if [[ "$setup_content" =~ \"($package)([>=<~]+[0-9a-zA-Z.-]+)?\" ]]; then
        # Update version constraint to use >= with the version from requirements.txt
        old_entry="\"$package${BASH_REMATCH[2]}\""
        new_entry="\"$package>=$version\""

        echo "  Updating $old_entry to $new_entry"
        setup_content=${setup_content//$old_entry/$new_entry}
    elif [[ "$setup_content" =~ \"($package_lower)([>=<~]+[0-9a-zA-Z.-]+)?\" ]]; then
        # Try case-insensitive match
        matched_package="${BASH_REMATCH[1]}"
        old_entry="\"$matched_package${BASH_REMATCH[2]}\""
        new_entry="\"$matched_package>=$version\""

        echo "  Updating $old_entry to $new_entry (case-insensitive match)"
        setup_content=${setup_content//$old_entry/$new_entry}
    else
        # Package not found in install_requires - could be in extras_require or not used
        # Just log this for now
        echo "  Note: Package $package not found in install_requires section"
    fi
done < "$TEMP_FILE"

# Write updated content back to setup.py
echo "$setup_content" > setup.py

echo "Version synchronization complete!"
echo "setup.py has been updated with versions from requirements.txt"

exit 0
