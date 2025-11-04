#!/usr/bin/env python3
"""
Release script for async-decorator package.
"""

import subprocess


def run_command(cmd, check=True):
    """Run a shell command."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode


def main():
    """Main release process."""
    # Clean previous builds
    print("Cleaning previous builds...")
    run_command("rm -rf build/ dist/ *.egg-info/")

    # Build package
    print("Building package...")
    run_command("python -m build")

    # Check build
    print("Checking build...")
    run_command("twine check dist/*")

    # Upload to TestPyPI
    print("Uploading to TestPyPI...")
    run_command("twine upload --repository testpypi dist/*")

    print("\n" + "="*50)
    print("Package uploaded to TestPyPI successfully!")
    print("Test installation with:")
    print("pip install --index-url https://test.pypi.org/simple/ async-decorator")
    print("="*50)

    # Ask for confirmation to upload to PyPI
    response = input("\nUpload to real PyPI? (y/n): ")
    if response.lower() == 'y':
        print("Uploading to PyPI...")
        run_command("twine upload dist/*")
        print("Package uploaded to PyPI successfully!")
    else:
        print("Skipping PyPI upload.")


if __name__ == "__main__":
    main()
