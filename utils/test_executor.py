"""
Test Execution Module
Runs generated test files and captures results.
"""

import subprocess
import sys
import os
from typing import Dict, Any, List
import json
import tempfile
from pathlib import Path


class TestExecutor:
    """
    Executes generated test files and captures results.
    """
    
    def __init__(self, workspace_path: str):
        """
        Initialize the test executor.
        
        Args:
            workspace_path: Path to the workspace directory containing test files
        """
        self.workspace_path = workspace_path
    
    def find_test_files(self) -> List[str]:
        """
        Find all test files in the workspace.
        
        Returns:
            List of test file paths
        """
        test_files = []
        workspace = Path(self.workspace_path)
        
        if workspace.exists():
            # Look for test files (test_*.py, *_test.py, test_suite.py)
            for pattern in ['test_*.py', '*_test.py', 'test_suite.py']:
                test_files.extend(workspace.glob(pattern))
        
        return [str(f) for f in test_files]
    
    def execute_unittest_file(self, test_file: str) -> Dict[str, Any]:
        """
        Execute a single test file using unittest and capture results.
        
        Args:
            test_file: Path to the test file
            
        Returns:
            Dictionary containing test results
        """
        try:
            # Extract just the filename (without extension) for unittest module import
            test_filename = os.path.basename(test_file)
            test_module = test_filename.replace('.py', '')
            
            # Prepare environment to prevent __pycache__ creation
            env = os.environ.copy()
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            
            # Run the test file with unittest in verbose mode
            result = subprocess.run(
                [sys.executable, '-m', 'unittest', test_module, '-v'],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                env=env
            )
            
            # Parse the output
            output = result.stdout + result.stderr
            
            # Extract test counts
            tests_run = 0
            failures = 0
            errors = 0
            skipped = 0
            
            # Parse unittest output for test counts
            for line in output.split('\n'):
                if 'Ran' in line and 'test' in line:
                    # Extract number of tests run
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'Ran' == part and i + 1 < len(parts):
                            try:
                                tests_run = int(parts[i + 1])
                            except (ValueError, IndexError):
                                pass
                
                if 'FAILED' in line:
                    # Extract failures and errors
                    if 'failures=' in line:
                        try:
                            failures = int(line.split('failures=')[1].split(')')[0].split(',')[0])
                        except (ValueError, IndexError):
                            pass
                    if 'errors=' in line:
                        try:
                            errors = int(line.split('errors=')[1].split(')')[0].split(',')[0])
                        except (ValueError, IndexError):
                            pass
            
            # Determine overall status
            if result.returncode == 0:
                status = 'passed'
            else:
                status = 'failed'
            
            return {
                'status': status,
                'tests_run': tests_run,
                'failures': failures,
                'errors': errors,
                'skipped': skipped,
                'output': output,
                'return_code': result.returncode,
                'file': os.path.basename(test_file)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'output': f'Test execution timed out after 30 seconds',
                'return_code': -1,
                'file': os.path.basename(test_file)
            }
        except Exception as e:
            return {
                'status': 'error',
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'output': f'Error executing tests: {str(e)}',
                'return_code': -1,
                'file': os.path.basename(test_file)
            }
    
    def execute_pytest_file(self, test_file: str) -> Dict[str, Any]:
        """
        Execute a single test file using pytest and capture results.
        
        Args:
            test_file: Path to the test file
            
        Returns:
            Dictionary containing test results
        """
        try:
            # Prepare environment to prevent __pycache__ creation
            env = os.environ.copy()
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            
            # Check if pytest is available
            pytest_check = subprocess.run(
                [sys.executable, '-m', 'pytest', '--version'],
                capture_output=True,
                text=True,
                env=env
            )
            
            if pytest_check.returncode != 0:
                # Pytest not available, fall back to unittest
                return self.execute_unittest_file(test_file)
            
            # Run pytest with JSON report
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            output = result.stdout + result.stderr
            
            # Parse pytest output
            tests_run = 0
            failures = 0
            errors = 0
            skipped = 0
            
            for line in output.split('\n'):
                if 'passed' in line or 'failed' in line:
                    # Extract test counts from pytest summary
                    if 'passed' in line:
                        try:
                            passed_count = int(line.split('passed')[0].strip().split()[-1])
                            tests_run += passed_count
                        except (ValueError, IndexError):
                            pass
                    if 'failed' in line:
                        try:
                            failed_count = int(line.split('failed')[0].strip().split()[-1])
                            failures += failed_count
                            tests_run += failed_count
                        except (ValueError, IndexError):
                            pass
                    if 'error' in line:
                        try:
                            error_count = int(line.split('error')[0].strip().split()[-1])
                            errors += error_count
                        except (ValueError, IndexError):
                            pass
                    if 'skipped' in line:
                        try:
                            skip_count = int(line.split('skipped')[0].strip().split()[-1])
                            skipped += skip_count
                        except (ValueError, IndexError):
                            pass
            
            status = 'passed' if result.returncode == 0 else 'failed'
            
            return {
                'status': status,
                'tests_run': tests_run,
                'failures': failures,
                'errors': errors,
                'skipped': skipped,
                'output': output,
                'return_code': result.returncode,
                'file': os.path.basename(test_file)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'output': f'Test execution timed out after 30 seconds',
                'return_code': -1,
                'file': os.path.basename(test_file)
            }
        except Exception as e:
            return {
                'status': 'error',
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'output': f'Error executing tests: {str(e)}',
                'return_code': -1,
                'file': os.path.basename(test_file)
            }
    
    def execute_all_tests(self) -> Dict[str, Any]:
        """
        Execute all test files in the workspace.
        
        Returns:
            Dictionary containing aggregated test results
        """
        test_files = self.find_test_files()
        
        if not test_files:
            return {
                'status': 'no_tests',
                'message': 'No test files found in workspace',
                'total_tests': 0,
                'total_passed': 0,
                'total_failed': 0,
                'total_errors': 0,
                'test_results': []
            }
        
        test_results = []
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        
        for test_file in test_files:
            # Try unittest first (most common for generated tests)
            result = self.execute_unittest_file(test_file)
            test_results.append(result)
            
            # Aggregate counts
            total_tests += result['tests_run']
            
            # Calculate passed tests correctly regardless of file status
            # passed = run - failed - errors
            passed_in_file = result['tests_run'] - result['failures'] - result['errors']
            if passed_in_file < 0: passed_in_file = 0
            
            total_passed += passed_in_file
            total_failed += result['failures']
            total_errors += result['errors']
        
        # Determine overall status
        overall_status = 'passed'
        if total_errors > 0 or total_failed > 0:
            overall_status = 'failed'
        elif total_tests == 0:
            overall_status = 'no_tests'
        
        return {
            'status': overall_status,
            'message': f'Executed {len(test_files)} test file(s)',
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_errors': total_errors,
            'test_results': test_results
        }


def run_tests_in_workspace(workspace_path: str) -> Dict[str, Any]:
    """
    Convenience function to run all tests in a workspace.
    
    Args:
        workspace_path: Path to the workspace directory
        
    Returns:
        Test execution results
    """
    executor = TestExecutor(workspace_path)
    return executor.execute_all_tests()




