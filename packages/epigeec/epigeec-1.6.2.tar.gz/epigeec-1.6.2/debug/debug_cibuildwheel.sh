#!/usr/bin/env bash
set -euxo pipefail

# Debug cibuildwheel build using a local custom Docker image
# (so you don't have to reinstall dependencies every time)

# To debug without custom image, using same options as CI:
# cibuildwheel --platform linux --archs x86_64

# --- SETUP CIBUILDWHEEL ENVIRONMENT VARIABLES ---

# Get tag from input argument or default
if [ -n "${1-}" ]; then
    tag="$1"
else
    tag="custom-manylinux_2_28_x86_64"
fi

# Only two acceptable tags
if [ "$tag" != "custom-manylinux_2_28_x86_64" ] && [ "$tag" != "custom-manylinux_2_28_x86_64-epigeec-built" ]; then
    echo "Usage: $0 [custom-manylinux_2_28_x86_64|custom-manylinux_2_28_x86_64-epigeec-built]"
    exit 1
fi

export CIBW_MANYLINUX_X86_64_IMAGE="$tag"  # use custom image

# Customize these as needed:
export CIBW_OUTPUT_DIR=wheelhouse
export CIBW_PLATFORM=linux
export CIBW_BUILD="cp311-manylinux_x86_64"      # limit to one build to test faster
export CIBW_BUILD_VERBOSITY=3                   # verbose debug output
export CIBW_BUILD_FRONTEND="build"              # optionally disable parallel builds for easier debugging
export CIBW_BEFORE_ALL=""                      # overwrite yum installs

if [ "$tag" == "custom-manylinux_2_28_x86_64-epigeec-built" ]; then
    echo "Using epigeec-built custom image, skipping build step."
    export CIBW_BEFORE_BUILD=""
else
    echo "Using standard custom image, running build step."
    export CIBW_BEFORE_BUILD="git clean -fdx && cmake . && make -j \$(nproc --all)"
fi

# Run specific test scripts inside wheel test phase
# export CIBW_TEST_COMMAND="echo '--- Filesystem before test ---' && tree {project} && python -Wd {project}/epigeec/test/filter_test.py && python -Wd {project}/epigeec/test/test.py"
export CIBW_TEST_COMMAND="python -Wd {project}/epigeec/test/filter_test.py && python -Wd {project}/epigeec/test/test.py"


# --- RUN CIBUILDWHEEL ---

# Find the project root (where pyproject.toml or setup.py is)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Verify project root has package files
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "Error: Could not find pyproject.toml in $PROJECT_ROOT"
    echo "Contents of $PROJECT_ROOT:"
    ls -la "$PROJECT_ROOT"
    exit 1
fi

# Run cibuildwheel from project root
cd "$PROJECT_ROOT"
echo "Running cibuildwheel from: $(pwd)"
cibuildwheel --output-dir wheelhouse .
echo "Debug build complete! Wheels are in wheelhouse/"
ls -lh wheelhouse/
