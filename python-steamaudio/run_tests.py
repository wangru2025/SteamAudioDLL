#!/usr/bin/env python
"""Test runner script for Steam Audio library."""

import sys
import subprocess
import argparse


def run_tests(args):
    """Run tests with specified options."""
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    cmd.append("tests/")
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=steamaudio", "--cov-report=html", "--cov-report=term"])
    
    # Add specific test file
    if args.test_file:
        cmd[-1] = f"tests/{args.test_file}"
    
    # Add specific test
    if args.test_name:
        cmd.append(f"-k {args.test_name}")
    
    # Add markers
    if args.markers:
        cmd.append(f"-m {args.markers}")
    
    # Add fail fast
    if args.fail_fast:
        cmd.append("-x")
    
    # Add show output
    if args.show_output:
        cmd.append("-s")
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Steam Audio tests")
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "-f", "--test-file",
        help="Run specific test file (e.g., test_basic.py)"
    )
    
    parser.add_argument(
        "-t", "--test-name",
        help="Run specific test by name"
    )
    
    parser.add_argument(
        "-m", "--markers",
        help="Run tests with specific markers"
    )
    
    parser.add_argument(
        "-x", "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    
    parser.add_argument(
        "-s", "--show-output",
        action="store_true",
        help="Show print statements"
    )
    
    args = parser.parse_args()
    
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
