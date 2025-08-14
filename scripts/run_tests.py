#!/usr/bin/env python3
"""
Test runner script for Business Intelligence Platform.
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run tests for Business Intelligence Platform")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--slow", action="store_true", help="Include slow tests")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--file", type=str, help="Run specific test file")
    parser.add_argument("--test", type=str, help="Run specific test function")
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    subprocess.run(["cd", str(project_root)], shell=True)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    
    # Add specific file or test
    if args.file:
        cmd.append(f"tests/{args.file}")
    elif args.test:
        cmd.extend(["-k", args.test])
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    # Exclude slow tests unless requested
    if not args.slow:
        cmd.extend(["-m", "not slow"])
    
    # Run tests
    success = run_command(cmd, "Running tests")
    
    if not success:
        print("\n❌ Tests failed!")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    
    # Run additional checks
    if args.coverage:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    # Optional: Run linting
    print("\n🔍 Running additional checks...")
    
    # Check imports
    import_check = run_command(
        ["python", "-c", "import src.business_intelligence; print('✅ Main imports successful')"],
        "Checking main imports"
    )
    
    if not import_check:
        print("⚠️  Import check failed")
        sys.exit(1)
    
    print("\n🎉 All checks passed! System is ready for deployment.")

if __name__ == "__main__":
    main()