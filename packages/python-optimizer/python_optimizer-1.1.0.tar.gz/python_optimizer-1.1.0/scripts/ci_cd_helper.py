#!/usr/bin/env python3
"""
CI/CD Helper Script for Python Optimizer

This script helps you run CI/CD pipeline steps locally before pushing to GitHub.
It mirrors the GitHub Actions workflow for local testing and validation.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"🔄 Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd, shell=isinstance(cmd, str), cwd=cwd, 
            capture_output=False, check=check
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with return code {e.returncode}")
        return False


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("📋 Checking dependencies...")
    
    required_packages = [
        "black", "isort", "flake8", "mypy", "pytest", 
        "pytest-cov", "safety", "bandit"
    ]
    
    missing = []
    for package in required_packages:
        try:
            subprocess.check_output([sys.executable, "-c", f"import {package}"], 
                                   stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, ImportError):
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("💡 Install with: pip install -e \".[dev]\"")
        return False
    
    print("✅ All dependencies found")
    return True


def run_linting():
    """Run all linting checks."""
    print("\n🔍 Running linting checks...")
    
    # Critical flake8 checks
    success = run_command([
        sys.executable, "-m", "flake8", "python_optimizer", 
        "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"
    ])
    if not success:
        print("❌ Critical linting errors found!")
        return False
    
    # Full flake8 (non-blocking)
    print("📝 Running full linting check...")
    run_command([
        sys.executable, "-m", "flake8", "python_optimizer",
        "--count", "--exit-zero", "--max-complexity=15", "--max-line-length=88"
    ], check=False)
    
    return True


def run_formatting_checks():
    """Run formatting checks."""
    print("\n🎨 Checking code formatting...")
    
    # Black check
    black_ok = run_command([
        sys.executable, "-m", "black", "--check", "--diff", "python_optimizer/"
    ], check=False)
    
    # isort check
    isort_ok = run_command([
        sys.executable, "-m", "isort", "--check-only", "--diff", "python_optimizer/"
    ], check=False)
    
    if not black_ok or not isort_ok:
        print("❌ Formatting issues found!")
        print("💡 Fix with: make format")
        return False
    
    print("✅ Code formatting is correct")
    return True


def run_type_checking():
    """Run type checking with mypy."""
    print("\n🔬 Running type checking...")
    
    success = run_command([
        sys.executable, "-m", "mypy", "python_optimizer/"
    ], check=False)  # Non-blocking for now
    
    if success:
        print("✅ Type checking passed")
    else:
        print("⚠️  Type checking issues found (non-blocking)")
    
    return True  # Always return True since mypy is non-blocking


def run_tests():
    """Run the test suite."""
    print("\n🧪 Running tests...")
    
    success = run_command([
        sys.executable, "-m", "pytest", "tests/",
        "--cov=python_optimizer",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--tb=short",
        "-v"
    ])
    
    if success:
        print("✅ All tests passed")
    else:
        print("❌ Some tests failed")
    
    return success


def run_security_checks():
    """Run security checks."""
    print("\n🛡️  Running security checks...")
    
    try:
        # Safety check
        print("🔒 Checking for known vulnerabilities...")
        run_command([sys.executable, "-m", "safety", "check"], check=False)
        
        # Bandit check
        print("🔍 Running security scan...")
        run_command([
            sys.executable, "-m", "bandit", "-r", "python_optimizer/", "-f", "text"
        ], check=False)
        
        print("✅ Security checks completed")
        return True
        
    except FileNotFoundError:
        print("⚠️  Security tools not found. Install with: pip install safety bandit")
        return True  # Non-blocking


def build_package():
    """Build the package."""
    print("\n📦 Building package...")
    
    try:
        success = run_command([sys.executable, "-m", "build"])
        if success:
            print("✅ Package built successfully")
            
            # Check package
            run_command([sys.executable, "-m", "twine", "check", "dist/*"])
            return True
        else:
            print("❌ Package build failed")
            return False
            
    except FileNotFoundError:
        print("❌ Build tools not found. Install with: pip install build twine")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="CI/CD Helper for Python Optimizer")
    parser.add_argument(
        "--step", 
        choices=["lint", "format", "type", "test", "security", "build", "all"],
        default="all",
        help="Which step to run"
    )
    parser.add_argument(
        "--fix", 
        action="store_true",
        help="Fix formatting issues automatically"
    )
    
    args = parser.parse_args()
    
    print("🚀 Python Optimizer CI/CD Helper")
    print("=" * 40)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    subprocess.run(["git", "status", "--porcelain"], cwd=project_root, check=False)
    
    if not check_dependencies():
        sys.exit(1)
    
    success = True
    
    if args.fix:
        print("\n🔧 Fixing code formatting...")
        run_command([sys.executable, "-m", "black", "python_optimizer/"])
        run_command([sys.executable, "-m", "isort", "python_optimizer/"])
        print("✅ Code formatting fixed")
        return
    
    if args.step in ["lint", "all"]:
        success &= run_linting()
    
    if args.step in ["format", "all"]:
        success &= run_formatting_checks()
    
    if args.step in ["type", "all"]:
        success &= run_type_checking()
    
    if args.step in ["test", "all"]:
        success &= run_tests()
    
    if args.step in ["security", "all"]:
        success &= run_security_checks()
    
    if args.step in ["build", "all"]:
        success &= build_package()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All checks passed! Ready to push 🚀")
    else:
        print("❌ Some checks failed. Fix issues before pushing.")
        sys.exit(1)


if __name__ == "__main__":
    main()