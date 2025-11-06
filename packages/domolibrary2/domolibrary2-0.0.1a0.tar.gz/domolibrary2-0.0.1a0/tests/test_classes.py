"""
Main test runner for all class tests.
Runs DomoDataset and DomoUser test suites.
"""

import asyncio
import importlib.util
import sys
from pathlib import Path

# Add the tests/classes directory to the path so we can import the test modules
sys.path.insert(0, str(Path(__file__).parent / "classes"))


def import_module_from_path(file_path: Path):
    """Import a Python module from a file path"""
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


async def run_test_module(file_name: str, file_path: Path):
    """Run tests from a specific test module"""
    print("=" * 60)
    print(f"Running {file_name} Tests")
    print("=" * 60)

    try:
        print(f"📦 Importing {file_name} module...")
        # Import the module dynamically
        test_module = import_module_from_path(file_path)
        print(f"✅ Successfully imported {file_name}")

        # Check if module has a main function and call it
        if hasattr(test_module, "main"):
            print(f"🏃 Executing {file_name}.main()...")
            await test_module.main()
            print(f"✅ {file_name} tests completed successfully")
        else:
            print(f"⚠️ {file_name} has no main() function to run")

    except ImportError as e:
        print(f"❌ Failed to import {file_name}: {e}")
        raise
    except AttributeError as e:
        print(f"❌ Module error in {file_name}: {e}")
        raise
    except Exception as e:
        print(f"❌ {file_name} tests failed: {e}")
        import traceback

        print("📄 Full error traceback:")
        traceback.print_exc()
        raise


def discover_test_files(test_dir) -> list[tuple[str, Path]]:
    """Discover all test files in the given directory"""
    test_files = []

    # Ensure test_dir is a Path object
    if isinstance(test_dir, str):
        test_dir = Path(test_dir)

    # Look for .py files that don't start with underscores
    for file_path in test_dir.glob("*.py"):
        if file_path.name.startswith("Domo"):
            test_files.append((file_path.stem, file_path))

    return sorted(test_files)


async def main(test_pattern: str = None, test_dir="./tests/classes"):
    """Main test runner with optional test pattern filtering"""
    print("Starting Domo Library Class Tests")
    print("=" * 60)

    # Discover test files

    discovered_tests = discover_test_files(test_dir)

    # Filter tests if pattern provided
    if test_pattern:
        discovered_tests = [
            (name, path)
            for name, path in discovered_tests
            if test_pattern.lower() in name.lower()
        ]
        print(
            f"Filtered to tests matching '{test_pattern}': {[name for name, _ in discovered_tests]}"
        )

    print(
        f"Discovered {len(discovered_tests)} test files: {[name for name, _ in discovered_tests]}"
    )

    results = {}

    for test_name, test_path in discovered_tests:
        try:
            print(f"\n🚀 Starting {test_name} test suite...")
            await run_test_module(test_name, test_path)
            results[test_name] = "✅ PASSED"
            print(f"✅ {test_name} test suite completed successfully!")
        except Exception as e:
            results[test_name] = f"❌ FAILED: {e}"
            print(f"❌ {test_name} test suite failed: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for suite_name, result in results.items():
        print(f"{suite_name}: {result}")

    # Check if all tests passed
    failed_tests = [name for name, result in results.items() if "FAILED" in result]

    if failed_tests:
        print(
            f"\n❌ {len(failed_tests)} test suite(s) failed: {', '.join(failed_tests)}"
        )
        sys.exit(1)
    else:
        print(f"\n✅ All {len(results)} test suites passed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Domo Library class tests")
    parser.add_argument(
        "--filter",
        "-f",
        type=str,
        help="Filter tests by name pattern (case-insensitive)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="list available test files without running them",
    )

    args = parser.parse_args()

    if args.list:
        test_dir = Path(__file__).parent / "classes"
        discovered_tests = discover_test_files(test_dir)
        print("Available test files:")
        for name, path in discovered_tests:
            print(f"  - {name} ({path.name})")
    else:
        asyncio.run(main(args.filter))
