"""Custom setup.py to build C++ components with CMake before packaging."""

import os
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build import build


def is_binary(filepath: str | Path) -> bool:
    """Check if a file is a binary executable."""
    path = str(filepath)
    if path.startswith("."):
        return False
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\0" in chunk:
                return True
    except OSError as err:
        print(f"Error checking if file is binary: {err}", file=sys.stderr)
        return False
    return False


class CustomBuild(build):
    """Custom build command that runs cmake and make."""

    def run(self):
        """Run cmake and make before the normal build."""
        bin_dir = Path("epigeec/bin")
        lib_dir = Path("epigeec/lib")

        # Check if binaries exist
        has_binaries = False
        if bin_dir.exists():
            binaries = [b for b in bin_dir.glob("*") if is_binary(b)]
            has_binaries = len(binaries) > 0

        if lib_dir.exists() and not has_binaries:
            libs = list(lib_dir.glob("*.so*"))
            has_binaries = len(libs) > 0

        if not has_binaries:
            print("=" * 60, file=sys.stderr)
            print("Building C++ components with CMake...", file=sys.stderr)
            print("=" * 60, file=sys.stderr)

            try:
                # Create build directory
                build_dir = Path("build_cmake")
                build_dir.mkdir(exist_ok=True)

                # Run cmake (configure from build directory)
                result = subprocess.run(
                    ["cmake", ".."],
                    cwd=build_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(result.stdout, file=sys.stderr)

                # Run make
                nproc = os.cpu_count() or 4
                result = subprocess.run(
                    ["cmake", "--build", ".", "-j", str(nproc)],
                    cwd=build_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(result.stdout, file=sys.stderr)

                print("=" * 60, file=sys.stderr)
                print("C++ build complete!", file=sys.stderr)

                # Verify build succeeded
                if bin_dir.exists():
                    binaries = [b for b in bin_dir.glob("*") if is_binary(b)]
                    print(f"Built {len(binaries)} binaries:", file=sys.stderr)
                    for b in binaries:
                        print(f"  - {b.name}", file=sys.stderr)

                print("=" * 60, file=sys.stderr)

            except FileNotFoundError as e:
                print(
                    f"""
ERROR: Required build tool not found: {e}

Please install the required dependencies:
  - CMake
  - C++ compiler (gcc/g++)
  - HDF5 development libraries
  - Boost development libraries

On Ubuntu/Debian:
  sudo apt-get install cmake build-essential libhdf5-dev libboost-dev

On RHEL/Fedora:
  sudo yum install cmake gcc-c++ hdf5-devel boost-devel

On macOS:
  brew install cmake hdf5 boost libomp
                """,
                    file=sys.stderr,
                )
                sys.exit(1)

            except subprocess.CalledProcessError as e:
                print(
                    f"""
ERROR: Build failed with exit code {e.returncode}

STDOUT:
{e.stdout}

STDERR:
{e.stderr}

Please check that all dependencies are installed correctly.
                """,
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            print("=" * 60, file=sys.stderr)
            print("C++ binaries already exist, skipping build.", file=sys.stderr)
            if bin_dir.exists():
                binaries = [b for b in bin_dir.glob("*") if is_binary(b)]
                for b in binaries:
                    print(f"  - {b.name}", file=sys.stderr)
            print("=" * 60, file=sys.stderr)

        # Continue with normal build
        super().run()


setup(
    cmdclass={"build": CustomBuild},
    has_ext_modules=lambda: True,  # Makes wheel tag platform-specific
)
