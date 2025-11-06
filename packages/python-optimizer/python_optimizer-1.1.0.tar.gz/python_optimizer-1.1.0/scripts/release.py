#!/usr/bin/env python3
"""
Release preparation script for Python Optimizer.

This script automates version bumping, changelog updates, and release preparation.
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def get_current_version():
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)
    
    raise ValueError("Could not find version in pyproject.toml")

def bump_version(current_version, bump_type):
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError("bump_type must be 'major', 'minor', or 'patch'")

def update_version_files(new_version):
    """Update version in relevant files."""
    files_to_update = [
        ("pyproject.toml", r'version = "[^"]+"', f'version = "{new_version}"'),
        ("python_optimizer/__init__.py", r'__version__ = "[^"]+"', f'__version__ = "{new_version}"'),
    ]
    
    for file_path, pattern, replacement in files_to_update:
        path = Path(file_path)
        content = path.read_text()
        updated_content = re.sub(pattern, replacement, content)
        path.write_text(updated_content)
        print(f"Updated version in {file_path}")

def update_changelog(new_version):
    """Update CHANGELOG.md with new version."""
    changelog_path = Path("CHANGELOG.md")
    content = changelog_path.read_text()
    
    # Get current date
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Replace [Unreleased] section with new version
    unreleased_section = re.search(
        r'## \[Unreleased\].*?(?=## \[|\Z)', 
        content, 
        re.DOTALL
    )
    
    if unreleased_section:
        # Extract changes from unreleased section
        unreleased_content = unreleased_section.group(0)
        
        # Create new version section
        new_section = f"""## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [{new_version}] - {today}
{unreleased_content.replace('## [Unreleased]', '').strip()}

"""
        
        # Replace unreleased section
        updated_content = content.replace(unreleased_section.group(0), new_section)
        changelog_path.write_text(updated_content)
        print(f"Updated CHANGELOG.md with version {new_version}")

def run_tests():
    """Run test suite to ensure everything works."""
    print("Running test suite...")
    result = subprocess.run(["python", "-m", "pytest", "tests/"], capture_output=True)
    
    if result.returncode != 0:
        print("❌ Tests failed! Aborting release.")
        print(result.stdout.decode())
        print(result.stderr.decode())
        return False
    
    print("✅ All tests passed!")
    return True

def run_linting():
    """Run code quality checks."""
    print("Running linting checks...")
    
    checks = [
        (["black", "--check", "python_optimizer/"], "Black formatting"),
        (["flake8", "python_optimizer/"], "Flake8 linting"),
        (["isort", "--check-only", "python_optimizer/"], "Import sorting"),
    ]
    
    for cmd, name in checks:
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print(f"❌ {name} failed! Please fix issues first.")
            print(result.stdout.decode())
            print(result.stderr.decode())
            return False
        print(f"✅ {name} passed!")
    
    return True

def build_package():
    """Build the package for distribution."""
    print("Building package...")
    
    # Clean previous builds
    subprocess.run(["rm", "-rf", "build/", "dist/", "*.egg-info/"], shell=True)
    
    # Build package
    result = subprocess.run(["python", "-m", "build"], capture_output=True)
    
    if result.returncode != 0:
        print("❌ Package build failed!")
        print(result.stdout.decode())
        print(result.stderr.decode())
        return False
    
    print("✅ Package built successfully!")
    return True

def create_git_tag(version):
    """Create git tag for the release."""
    print(f"Creating git tag v{version}...")
    
    # Add all changes
    subprocess.run(["git", "add", "."])
    
    # Commit changes
    commit_msg = f"chore: bump version to {version}"
    subprocess.run(["git", "commit", "-m", commit_msg])
    
    # Create tag
    tag_msg = f"Release version {version}"
    subprocess.run(["git", "tag", "-a", f"v{version}", "-m", tag_msg])
    
    print(f"✅ Created git tag v{version}")

def main():
    """Main release preparation function."""
    parser = argparse.ArgumentParser(description="Prepare Python Optimizer release")
    parser.add_argument(
        "bump_type", 
        choices=["major", "minor", "patch"],
        help="Type of version bump"
    )
    parser.add_argument(
        "--skip-tests", 
        action="store_true",
        help="Skip running tests"
    )
    parser.add_argument(
        "--skip-linting", 
        action="store_true",
        help="Skip linting checks"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    try:
        # Get current version
        current_version = get_current_version()
        new_version = bump_version(current_version, args.bump_type)
        
        print(f"🚀 Preparing release: {current_version} → {new_version}")
        
        if args.dry_run:
            print("🔍 DRY RUN - No changes will be made")
            print(f"Would bump version from {current_version} to {new_version}")
            print("Would update: pyproject.toml, __init__.py, CHANGELOG.md")
            print("Would run tests, linting, build package, and create git tag")
            return
        
        # Run quality checks
        if not args.skip_tests and not run_tests():
            sys.exit(1)
        
        if not args.skip_linting and not run_linting():
            sys.exit(1)
        
        # Update version files
        update_version_files(new_version)
        update_changelog(new_version)
        
        # Build package
        if not build_package():
            sys.exit(1)
        
        # Create git tag
        create_git_tag(new_version)
        
        print(f"""
🎉 Release {new_version} prepared successfully!

Next steps:
1. Push changes: git push origin main --tags
2. Create GitHub release from tag v{new_version}
3. Publish to PyPI: twine upload dist/*

Or use: make publish
""")
        
    except Exception as e:
        print(f"❌ Release preparation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
