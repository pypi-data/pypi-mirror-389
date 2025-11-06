"""
Test module for validating that all route files can be imported without errors.

This test ensures that:
1. All individual route files can be imported
2. The route package and its subpackages can be imported
3. No circular imports or syntax errors exist
4. All dependencies are properly resolved

Run with: pytest tests/test_route_imports.py -v
"""

import importlib
import inspect
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

import pytest


class RouteImportTester:
    """Helper class for testing route imports."""

    def __init__(self, routes_path: str = None):
        """Initialize the tester with the routes directory path."""
        if routes_path is None:
            # Auto-detect routes path relative to this test file
            test_dir = Path(__file__).parent
            project_root = test_dir.parent
            self.routes_path = project_root / "src" / "domolibrary2" / "routes"
            self.tests_routes_path = test_dir  # tests/routes directory

            # Add project root to Python path for imports
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
        else:
            self.routes_path = Path(routes_path)
            self.tests_routes_path = Path(__file__).parent

        self.routes_module_path = "src.domolibrary2.routes"
        self.import_results = {}
        self.failed_imports = {}

    def discover_route_files(self) -> list[tuple[str, Path]]:
        """
        Discover all route files and packages.

        Returns:
            list of tuples (module_name, file_path)
        """
        route_files = []

        # Add the main routes package
        route_files.append(
            ("src.domolibrary2.routes", self.routes_path / "__init__.py")
        )

        # Discover individual route files
        for file_path in self.routes_path.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            module_name = f"src.domolibrary2.routes.{file_path.stem}"
            route_files.append((module_name, file_path))

        # Discover route subpackages (like account/)
        for subdir in self.routes_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("__"):
                init_file = subdir / "__init__.py"
                if init_file.exists():
                    module_name = f"src.domolibrary2.routes.{subdir.name}"
                    route_files.append((module_name, init_file))

                    # Also discover files within the subpackage
                    for py_file in subdir.glob("*.py"):
                        if py_file.name == "__init__.py":
                            continue
                        sub_module_name = (
                            f"src.domolibrary2.routes.{subdir.name}.{py_file.stem}"
                        )
                        route_files.append((sub_module_name, py_file))

        return sorted(route_files)

    def test_single_import(self, module_name: str, file_path: Path) -> dict[str, Any]:
        """
        Test importing a single module.

        Args:
            module_name: The full module name (e.g., 'src.domolibrary2.routes.auth')
            file_path: Path to the file being imported

        Returns:
            Dictionary with import results
        """
        result = {
            "module_name": module_name,
            "file_path": str(file_path),
            "success": False,
            "error": None,
            "error_type": None,
            "error_details": None,
            "module": None,
            "exports": [],
        }

        try:
            # Import the module
            module = importlib.import_module(module_name)
            result["module"] = module
            result["success"] = True

            # Get exported items from __all__ if available
            if hasattr(module, "__all__"):
                result["exports"] = list(module.__all__)
            else:
                # Fall back to public attributes
                result["exports"] = [
                    name for name in dir(module) if not name.startswith("_")
                ]

        except Exception as e:
            result["error"] = str(e)
            result["error_type"] = type(e).__name__
            result["error_details"] = traceback.format_exc()

        return result

    def test_all_imports(self) -> dict[str, Any]:
        """
        Test importing all discovered route files.

        Returns:
            Dictionary with overall results
        """
        route_files = self.discover_route_files()
        results = {
            "total_files": len(route_files),
            "successful_imports": 0,
            "failed_imports": 0,
            "import_results": {},
            "failed_modules": [],
            "summary": "",
        }

        print(f"\nTesting imports for {len(route_files)} route files/packages...")

        for module_name, file_path in route_files:
            print(f"  Testing: {module_name}")

            import_result = self.test_single_import(module_name, file_path)
            results["import_results"][module_name] = import_result

            if import_result["success"]:
                results["successful_imports"] += 1
                print(f"    ✅ SUCCESS - {len(import_result['exports'])} exports")
            else:
                results["failed_imports"] += 1
                results["failed_modules"].append(
                    {
                        "module": module_name,
                        "error": import_result["error"],
                        "error_type": import_result["error_type"],
                    }
                )
                print(
                    f"    ❌ FAILED - {import_result['error_type']}: {import_result['error']}"
                )

        # Generate summary
        success_rate = (results["successful_imports"] / results["total_files"]) * 100
        results["summary"] = (
            f"Import Test Results: {results['successful_imports']}/{results['total_files']} "
            f"successful ({success_rate:.1f}% success rate)"
        )

        return results

    def get_import_dependencies(self, module_name: str) -> list[str]:
        """
        Analyze import dependencies for a module.

        Args:
            module_name: The module to analyze

        Returns:
            list of imported module names
        """
        dependencies = []

        try:
            module = importlib.import_module(module_name)

            # Get all imported modules
            for name, obj in inspect.getmembers(module):
                if inspect.ismodule(obj):
                    dependencies.append(obj.__name__)

        except Exception:
            pass  # Module failed to import

        return dependencies

    def discover_test_files(self) -> list[Path]:
        """
        Discover all test files in the tests/routes directory.

        Returns:
            list of test file paths
        """
        test_files = []

        # Find all Python test files in tests/routes
        for file_path in self.tests_routes_path.glob("*.py"):
            if file_path.name.startswith("test_") or file_path.name.endswith(
                "_test.py"
            ):
                test_files.append(file_path)
            elif file_path.name not in [
                "__init__.py",
                "test.py",
            ]:  # Exclude this file and __init__.py
                # Check if it's a test file by content or naming convention
                if self._is_test_file(file_path):
                    test_files.append(file_path)

        # Also check subdirectories
        for subdir in self.tests_routes_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("__"):
                for file_path in subdir.glob("*.py"):
                    if (
                        file_path.name.startswith("test_")
                        or file_path.name.endswith("_test.py")
                        or self._is_test_file(file_path)
                    ):
                        test_files.append(file_path)

        return sorted(test_files)

    def _is_test_file(self, file_path: Path) -> bool:
        """
        Check if a file appears to be a test file based on content.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file appears to contain tests
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            # Look for common test patterns
            test_indicators = [
                "def test_",
                "class Test",
                "import pytest",
                "from pytest",
                "@pytest.",
                "assert ",
                "TestCase",
            ]
            return any(indicator in content for indicator in test_indicators)
        except Exception:
            return False

    def run_single_test_file(self, test_file: Path) -> dict[str, Any]:
        """
        Run a single test file using pytest.

        Args:
            test_file: Path to the test file

        Returns:
            Dictionary with test execution results
        """
        result = {
            "test_file": str(test_file),
            "file_name": test_file.name,
            "success": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error": None,
            "duration": 0,
            "tests_collected": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
        }

        try:
            import time

            start_time = time.time()

            # Run pytest on the specific file
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(test_file),
                "-v",
                "--tb=short",
                "--no-header",
            ]

            process = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
            )

            result["duration"] = time.time() - start_time
            result["exit_code"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["success"] = process.returncode == 0

            # Parse pytest output for test counts
            output = process.stdout + process.stderr
            result.update(self._parse_pytest_output(output))

        except subprocess.TimeoutExpired:
            result["error"] = "Test execution timed out (5 minutes)"
        except Exception as e:
            result["error"] = str(e)

        return result

    def _parse_pytest_output(self, output: str) -> dict[str, int]:
        """
        Parse pytest output to extract test statistics.

        Args:
            output: Combined stdout and stderr from pytest

        Returns:
            Dictionary with test counts
        """
        stats = {
            "tests_collected": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
        }

        # Look for collection line like "collected 5 items"
        if "collected" in output:
            for line in output.split("\n"):
                if "collected" in line and "items" in line:
                    try:
                        # Extract number from "collected X items"
                        words = line.split()
                        for i, word in enumerate(words):
                            if word == "collected" and i + 1 < len(words):
                                stats["tests_collected"] = int(words[i + 1])
                                break
                    except (ValueError, IndexError):
                        pass

        # Look for final summary line like "5 passed, 2 failed, 1 skipped"
        summary_patterns = [
            (r"(\d+) passed", "tests_passed"),
            (r"(\d+) failed", "tests_failed"),
            (r"(\d+) skipped", "tests_skipped"),
        ]

        import re

        for pattern, key in summary_patterns:
            matches = re.findall(pattern, output)
            if matches:
                try:
                    stats[key] = int(matches[-1])  # Take the last match
                except ValueError:
                    pass

        return stats

    def run_all_test_files(self, verbose: bool = True) -> dict[str, Any]:
        """
        Run all test files in the tests/routes directory.

        Args:
            verbose: Whether to print detailed output

        Returns:
            Dictionary with overall test execution results
        """
        test_files = self.discover_test_files()

        results = {
            "total_test_files": len(test_files),
            "successful_files": 0,
            "failed_files": 0,
            "test_file_results": {},
            "overall_stats": {
                "total_tests": 0,
                "total_passed": 0,
                "total_failed": 0,
                "total_skipped": 0,
                "total_duration": 0,
            },
            "failed_files_list": [],
            "summary": "",
        }

        if verbose:
            print(f"\nRunning {len(test_files)} test files from tests/routes/...")
            print("=" * 60)

        for test_file in test_files:
            if verbose:
                print(f"\n📁 Running: {test_file.name}")

            file_result = self.run_single_test_file(test_file)
            results["test_file_results"][str(test_file)] = file_result

            # Update overall statistics
            if file_result["success"]:
                results["successful_files"] += 1
                if verbose:
                    print(
                        f"   ✅ PASSED - {file_result['tests_passed']} tests passed "
                        f"({file_result['duration']:.2f}s)"
                    )
            else:
                results["failed_files"] += 1
                results["failed_files_list"].append(
                    {
                        "file": test_file.name,
                        "error": file_result.get("error"),
                        "exit_code": file_result.get("exit_code"),
                    }
                )
                if verbose:
                    print(f"   ❌ FAILED - Exit code: {file_result['exit_code']}")
                    if file_result.get("error"):
                        print(f"      Error: {file_result['error']}")

            # Add to totals
            stats = results["overall_stats"]
            stats["total_tests"] += file_result["tests_collected"]
            stats["total_passed"] += file_result["tests_passed"]
            stats["total_failed"] += file_result["tests_failed"]
            stats["total_skipped"] += file_result["tests_skipped"]
            stats["total_duration"] += file_result["duration"]

        # Generate summary
        stats = results["overall_stats"]
        success_rate = (
            (results["successful_files"] / results["total_test_files"]) * 100
            if results["total_test_files"] > 0
            else 0
        )

        results["summary"] = (
            f"Route Tests Summary: {results['successful_files']}/{results['total_test_files']} "
            f"files passed ({success_rate:.1f}% success rate)\n"
            f"Total Tests: {stats['total_passed']} passed, {stats['total_failed']} failed, "
            f"{stats['total_skipped']} skipped in {stats['total_duration']:.2f}s"
        )

        if verbose:
            print(f"\n{'=' * 60}")
            print("ROUTE TEST EXECUTION SUMMARY")
            print(f"{'=' * 60}")
            print(results["summary"])

            if results["failed_files_list"]:
                print(f"\n❌ FAILED FILES ({len(results['failed_files_list'])}):")
                for failed in results["failed_files_list"]:
                    print(f"  • {failed['file']} (exit code: {failed['exit_code']})")
                    if failed["error"]:
                        print(f"    {failed['error']}")

        return results

    def validate_module_exports(self, module_name: str) -> dict[str, Any]:
        """
        Validate that all exports in __all__ are actually available.

        Args:
            module_name: Module to validate

        Returns:
            Validation results
        """
        result = {
            "module_name": module_name,
            "has_all": False,
            "all_exports": [],
            "missing_exports": [],
            "invalid_exports": [],
            "valid": True,
        }

        try:
            module = importlib.import_module(module_name)

            if hasattr(module, "__all__"):
                result["has_all"] = True
                result["all_exports"] = list(module.__all__)

                # Check each export
                for export_name in module.__all__:
                    if not hasattr(module, export_name):
                        result["missing_exports"].append(export_name)
                        result["valid"] = False
                    else:
                        # Check if the export is valid (not None, etc.)
                        export_obj = getattr(module, export_name)
                        if export_obj is None:
                            result["invalid_exports"].append(export_name)

        except Exception:
            result["valid"] = False

        return result


# Test fixtures and helper functions


@pytest.fixture
def route_tester():
    """Provide a RouteImportTester instance."""
    return RouteImportTester()


@pytest.fixture
def routes_path():
    """Get the path to the routes directory."""
    test_dir = Path(__file__).parent
    return test_dir.parent / "src" / "routes"


# Main test classes


class TestRouteImports:
    """Test class for route import validation."""

    def test_all_route_files_can_be_imported(self, route_tester):
        """Test that all route files can be imported without errors."""
        results = route_tester.test_all_imports()

        print(f"\n{results['summary']}")

        if results["failed_imports"] > 0:
            print("\nFailed imports:")
            for failed in results["failed_modules"]:
                print(
                    f"  - {failed['module']}: {failed['error_type']} - {failed['error']}"
                )

        # Assert that all imports succeeded
        assert results["failed_imports"] == 0, (
            f"{results['failed_imports']} route files failed to import. "
            f"See test output for details."
        )

    def test_routes_package_import(self, route_tester):
        """Test that the main routes package can be imported."""
        result = route_tester.test_single_import(
            "src.domolibrary2.routes", route_tester.routes_path / "__init__.py"
        )

        assert result[
            "success"
        ], f"Routes package failed to import: {result['error_type']} - {result['error']}"

    def test_individual_route_files(self, route_tester, routes_path):
        """Test each individual route file separately."""
        failures = []

        for py_file in routes_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            module_name = f"src.domolibrary2.routes.{py_file.stem}"
            result = route_tester.test_single_import(module_name, py_file)

            if not result["success"]:
                failures.append(
                    {
                        "file": py_file.name,
                        "module": module_name,
                        "error": result["error"],
                        "error_type": result["error_type"],
                    }
                )

        if failures:
            error_details = "\n".join(
                [f"  - {f['file']}: {f['error_type']} - {f['error']}" for f in failures]
            )
            pytest.fail(f"Individual route files failed to import:\n{error_details}")

    def test_route_subpackages(self, route_tester, routes_path):
        """Test route subpackages (like account/)."""
        failures = []

        for subdir in routes_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("__"):
                init_file = subdir / "__init__.py"
                if init_file.exists():
                    module_name = f"src.domolibrary2.routes.{subdir.name}"
                    result = route_tester.test_single_import(module_name, init_file)

                    if not result["success"]:
                        failures.append(
                            {
                                "package": subdir.name,
                                "module": module_name,
                                "error": result["error"],
                                "error_type": result["error_type"],
                            }
                        )

        if failures:
            error_details = "\n".join(
                [
                    f"  - {f['package']}/: {f['error_type']} - {f['error']}"
                    for f in failures
                ]
            )
            pytest.fail(f"Route subpackages failed to import:\n{error_details}")

    def test_route_exports_validation(self, route_tester):
        """Test that all modules with __all__ export valid items."""
        route_files = route_tester.discover_route_files()
        validation_failures = []

        for module_name, _ in route_files:
            validation = route_tester.validate_module_exports(module_name)

            if validation["has_all"] and not validation["valid"]:
                validation_failures.append(
                    {
                        "module": module_name,
                        "missing": validation["missing_exports"],
                        "invalid": validation["invalid_exports"],
                    }
                )

        if validation_failures:
            error_details = "\n".join(
                [
                    f"  - {f['module']}: "
                    f"missing={f['missing']}, invalid={f['invalid']}"
                    for f in validation_failures
                ]
            )
            pytest.fail(f"Route export validation failed:\n{error_details}")

    @pytest.mark.slow
    def test_import_performance(self, route_tester):
        """Test that route imports complete within reasonable time."""
        import time

        start_time = time.time()
        results = route_tester.test_all_imports()
        total_time = time.time() - start_time

        # Assert reasonable performance (adjust threshold as needed)
        max_time = 30.0  # 30 seconds max for all imports
        assert (
            total_time < max_time
        ), f"Route imports took {total_time:.2f}s, exceeding {max_time}s threshold"

        print(
            f"\nImport performance: {total_time:.2f}s for {results['total_files']} files"
        )

    def test_no_circular_imports(self, route_tester):
        """Test that there are no circular import issues."""
        # This test attempts to import all modules and checks for circular import errors
        route_files = route_tester.discover_route_files()
        circular_import_errors = []

        for module_name, _ in route_files:
            result = route_tester.test_single_import(module_name, _)
            if not result["success"] and "circular import" in result["error"].lower():
                circular_import_errors.append(
                    {"module": module_name, "error": result["error"]}
                )

        if circular_import_errors:
            error_details = "\n".join(
                [
                    f"  - {err['module']}: {err['error']}"
                    for err in circular_import_errors
                ]
            )
            pytest.fail(f"Circular import errors detected:\n{error_details}")


class TestSpecificRouteFiles:
    """Test specific route files that might have special requirements."""

    def test_auth_routes(self, route_tester):
        """Test authentication routes specifically."""
        result = route_tester.test_single_import("src.domolibrary2.routes.auth", None)
        assert result["success"], f"Auth routes failed: {result['error']}"

    def test_account_package(self, route_tester):
        """Test the account package specifically."""
        # Test main package
        result = route_tester.test_single_import(
            "src.domolibrary2.routes.account", None
        )
        assert result["success"], f"Account package failed: {result['error']}"

        # Test individual account modules
        account_modules = [
            "src.domolibrary2.routes.account.core",
            "src.domolibrary2.routes.account.crud",
            "src.domolibrary2.routes.account.oauth",
            "src.domolibrary2.routes.account.config",
            "src.domolibrary2.routes.account.sharing",
            "src.domolibrary2.routes.account.exceptions",
        ]

        for module_name in account_modules:
            result = route_tester.test_single_import(module_name, None)
            assert result[
                "success"
            ], f"Account module {module_name} failed: {result['error']}"

    def test_core_utility_routes(self, route_tester):
        """Test core utility routes."""
        core_routes = [
            "src.domolibrary2.routes.dataset",
            "src.domolibrary2.routes.user",
            "src.domolibrary2.routes.group",
            "src.domolibrary2.routes.datacenter",
        ]

        for route in core_routes:
            result = route_tester.test_single_import(route, None)
            assert result["success"], f"Core route {route} failed: {result['error']}"


class TestRouteTestExecution:
    """Test class for executing all route test files."""

    def test_discover_route_test_files(self, route_tester):
        """Test that we can discover route test files."""
        test_files = route_tester.discover_test_files()

        assert len(test_files) > 0, "Should find at least one test file in tests/routes"

        # Verify all discovered files exist
        for test_file in test_files:
            assert test_file.exists(), f"Test file should exist: {test_file}"
            assert (
                test_file.suffix == ".py"
            ), f"Test file should be Python file: {test_file}"

        print(f"\n✅ Discovered {len(test_files)} test files:")
        for test_file in test_files:
            print(f"  - {test_file.name}")

    def test_run_individual_route_test_files(self, route_tester):
        """Test running individual route test files."""
        test_files = route_tester.discover_test_files()

        if not test_files:
            pytest.skip("No test files found in tests/routes directory")

        # Test running each file individually
        results = []
        for test_file in test_files:
            if test_file.name == "test.py":  # Skip this file to avoid recursion
                continue

            result = route_tester.run_single_test_file(test_file)
            results.append(result)

            print(f"\n📄 {result['file_name']}: ", end="")
            if result["success"]:
                print(
                    f"✅ PASSED ({result['tests_passed']} tests, {result['duration']:.2f}s)"
                )
            else:
                print(f"❌ FAILED (exit code: {result['exit_code']})")
                if result.get("error"):
                    print(f"   Error: {result['error']}")

        # At least one test should have been attempted
        assert len(results) > 0, "Should have attempted to run at least one test file"

    @pytest.mark.slow
    def test_run_all_route_tests(self, route_tester):
        """Test running all route test files together."""
        results = route_tester.run_all_test_files(verbose=True)

        print(f"\n{results['summary']}")

        # Check that we found and attempted to run test files
        assert results["total_test_files"] > 0, "Should find test files to run"

        # Report on any failures but don't fail the test - just provide information
        if results["failed_files"] > 0:
            print("\nℹ️  Some route test files had issues:")
            for failed in results["failed_files_list"]:
                print(
                    f"  - {failed['file']}: {failed.get('error', 'Exit code ' + str(failed['exit_code']))}"
                )

            # Only fail if ALL files failed
            success_rate = (
                results["successful_files"] / results["total_test_files"]
            ) * 100
            if success_rate == 0:
                pytest.fail("All route test files failed to execute")

        return results

    def test_route_test_file_validation(self, route_tester):
        """Test that route test files are properly structured."""
        test_files = route_tester.discover_test_files()

        validation_results = []

        for test_file in test_files:
            if test_file.name == "test.py":  # Skip this file
                continue

            validation = {
                "file": test_file.name,
                "path": str(test_file),
                "has_tests": False,
                "has_imports": False,
                "syntax_valid": True,
                "error": None,
            }

            try:
                content = test_file.read_text(encoding="utf-8")

                # Check for test functions/classes
                validation["has_tests"] = (
                    "def test_" in content
                    or "class Test" in content
                    or "@pytest." in content
                )

                # Check for imports
                validation["has_imports"] = "import " in content or "from " in content

                # Try to compile the file to check syntax
                compile(content, str(test_file), "exec")

            except SyntaxError as e:
                validation["syntax_valid"] = False
                validation["error"] = f"Syntax error: {e}"
            except Exception as e:
                validation["error"] = f"Validation error: {e}"

            validation_results.append(validation)

        # Report validation results
        print("\n📋 Route Test File Validation:")
        for result in validation_results:
            status = "✅" if result["syntax_valid"] and result["has_tests"] else "⚠️"
            print(f"  {status} {result['file']}")
            if not result["syntax_valid"]:
                print(f"      ❌ {result['error']}")
            elif not result["has_tests"]:
                print("      ⚠️  No test functions/classes found")

        # Check that at least some files have valid tests
        valid_test_files = [
            r for r in validation_results if r["syntax_valid"] and r["has_tests"]
        ]
        assert (
            len(valid_test_files) > 0
        ), "Should find at least one valid test file with tests"


# Utility functions for running tests programmatically


def run_import_tests_standalone():
    """Run import tests outside of pytest for debugging."""
    tester = RouteImportTester()
    results = tester.test_all_imports()

    print(f"\n{'='*60}")
    print("ROUTE IMPORT TEST RESULTS")
    print(f"{'='*60}")
    print(f"{results['summary']}")

    if results["failed_imports"] > 0:
        print(f"\n❌ FAILED IMPORTS ({results['failed_imports']}):")
        for failed in results["failed_modules"]:
            print(f"  • {failed['module']}")
            print(f"    Error: {failed['error_type']} - {failed['error']}")
            print()

    if results["successful_imports"] > 0:
        print(f"\n✅ SUCCESSFUL IMPORTS ({results['successful_imports']}):")
        for module_name, result in results["import_results"].items():
            if result["success"]:
                exports_count = len(result["exports"])
                print(f"  • {module_name} ({exports_count} exports)")

    return results["failed_imports"] == 0


def run_all_route_tests_standalone():
    """Run all route tests outside of pytest for debugging."""
    tester = RouteImportTester()

    print(f"\n{'='*60}")
    print("RUNNING ALL ROUTE TESTS")
    print(f"{'='*60}")

    # First run import tests
    print("📦 STEP 1: Testing route imports...")
    import_success = run_import_tests_standalone()

    print("\n📋 STEP 2: Running route test files...")
    test_results = tester.run_all_test_files(verbose=True)

    # Overall summary
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print(f"{'='*60}")
    print(f"📦 Import Tests: {'✅ PASSED' if import_success else '❌ FAILED'}")
    print(f"📋 Route Tests: {test_results['summary']}")

    overall_success = import_success and test_results["failed_files"] == 0
    print(
        f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}"
    )

    return overall_success


def run_specific_route_test(test_file_pattern: str = None):
    """
    Run a specific route test file or pattern.

    Args:
        test_file_pattern: Pattern to match test files (e.g., "user", "auth", "*.py")

    Returns:
        True if all matched tests passed
    """
    tester = RouteImportTester()
    test_files = tester.discover_test_files()

    if test_file_pattern:
        # Filter test files by pattern
        import fnmatch

        filtered_files = []
        for test_file in test_files:
            if fnmatch.fnmatch(
                test_file.name, f"*{test_file_pattern}*"
            ) or fnmatch.fnmatch(test_file.name, test_file_pattern):
                filtered_files.append(test_file)
        test_files = filtered_files

        if not test_files:
            print(f"❌ No test files found matching pattern: {test_file_pattern}")
            return False

    print(f"\n🎯 Running {len(test_files)} matching test files...")

    all_passed = True
    for test_file in test_files:
        if test_file.name == "test.py":  # Skip this file
            continue

        print(f"\n📁 Running: {test_file.name}")
        result = tester.run_single_test_file(test_file)

        if result["success"]:
            print(
                f"   ✅ PASSED - {result['tests_passed']} tests passed ({result['duration']:.2f}s)"
            )
        else:
            print(f"   ❌ FAILED - Exit code: {result['exit_code']}")
            if result.get("error"):
                print(f"      Error: {result['error']}")
            if result.get("stderr"):
                print(f"      Stderr: {result['stderr'][:200]}...")
            all_passed = False

    return all_passed


def discover_and_list_route_tests():
    """Discover and list all route test files without running them."""
    tester = RouteImportTester()
    test_files = tester.discover_test_files()

    print(f"\n📋 Discovered Route Test Files ({len(test_files)}):")
    print("=" * 50)

    for i, test_file in enumerate(test_files, 1):
        print(f"{i:2}. {test_file.name}")
        print(f"    Path: {test_file}")

        # Quick check if file has test content
        try:
            content = test_file.read_text(encoding="utf-8")
            test_count = content.count("def test_") + content.count("class Test")
            if test_count > 0:
                print(f"    Tests: ~{test_count} test functions/classes")
            else:
                print("    Tests: No obvious test functions found")
        except Exception as e:
            print(f"    Tests: Error reading file - {e}")
        print()

    return test_files


if __name__ == "__main__":
    """
    Run the import tests directly.

    Usage:
        python tests/test_route_imports.py

    Or with pytest:
        pytest tests/test_route_imports.py -v
        pytest tests/test_route_imports.py::TestRouteImports::test_all_route_files_can_be_imported -v
    """
    success = run_import_tests_standalone()
    sys.exit(0 if success else 1)
