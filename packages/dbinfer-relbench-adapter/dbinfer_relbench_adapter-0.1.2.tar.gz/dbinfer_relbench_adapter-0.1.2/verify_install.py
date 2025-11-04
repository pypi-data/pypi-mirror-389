#!/usr/bin/env python3
"""
Verify that dbinfer-relbench-adapter is installed correctly.

This script checks:
1. All required packages are installed
2. PyTorch version is compatible with DGL
3. DGL can be imported successfully
4. The adapter package works correctly
"""

import sys
import subprocess

def check_package_version(package_name, expected_version=None):
    """Check if a package is installed and optionally verify its version."""
    try:
        if package_name == "torch":
            import torch
            version = torch.__version__
            package_display = "PyTorch"
        elif package_name == "dgl":
            import dgl
            version = dgl.__version__
            package_display = "DGL"
        elif package_name == "torchdata":
            import torchdata
            version = torchdata.__version__
            package_display = "torchdata"
        elif package_name == "dbinfer_bench":
            import dbinfer_bench
            version = getattr(dbinfer_bench, "__version__", "unknown")
            package_display = "dbinfer_bench"
        elif package_name == "relbench":
            import relbench
            version = getattr(relbench, "__version__", "unknown")
            package_display = "RelBench"
        elif package_name == "dbinfer_relbench_adapter":
            import dbinfer_relbench_adapter
            version = getattr(dbinfer_relbench_adapter, "__version__", "0.1.2")
            package_display = "dbinfer-relbench-adapter"
        else:
            return False, f"Unknown package: {package_name}"

        if expected_version and not version.startswith(expected_version):
            return False, f"{package_display} version {version} (expected {expected_version}.x)"

        return True, f"{package_display} version {version}"

    except ImportError as e:
        return False, f"{package_name} is not installed: {e}"
    except Exception as e:
        return False, f"Error checking {package_name}: {e}"

def main():
    print("Verifying dbinfer-relbench-adapter installation...")
    print("=" * 60)

    all_passed = True

    # Check critical packages with version requirements
    checks = [
        ("torch", "2.3"),
        ("torchdata", "0.9"),
        ("dgl", None),
        ("dbinfer_bench", None),
        ("relbench", None),
        ("dbinfer_relbench_adapter", None),
    ]

    for package, expected_version in checks:
        success, message = check_package_version(package, expected_version)
        status = "✓" if success else "✗"
        print(f"{status} {message}")
        if not success:
            all_passed = False

    print("=" * 60)

    # Test the adapter functionality
    if all_passed:
        print("\nTesting adapter functionality...")
        try:
            from dbinfer_relbench_adapter import load_dbinfer_data
            print("✓ Adapter import successful")

            # Try loading a small dataset (this will be cached)
            print("✓ Testing dataset loading (this may take a moment)...")
            dataset, task = load_dbinfer_data("diginetica", "ctr")
            print(f"✓ Successfully loaded diginetica dataset with ctr task")
            print(f"  - Dataset has {len(dataset.get_db().table_dict)} tables")
            print(f"  - Task type: {task.task_type}")

            print("\n" + "=" * 60)
            print("✓ All checks passed! Installation is working correctly.")
            return 0

        except Exception as e:
            print(f"✗ Error testing adapter: {e}")
            print("\nTry running: python example.py")
            return 1
    else:
        print("\n✗ Some checks failed. Please reinstall:")
        print("  bash install.sh")
        return 1

if __name__ == "__main__":
    sys.exit(main())
