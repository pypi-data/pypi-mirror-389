"""
Foundry Tool Wrapper
Provides interface for running Foundry tests and executing PoCs
"""

import subprocess
import os
import json
from typing import Dict, List, Any


class FoundryWrapper:
    """Wrapper for Foundry (Forge) testing framework"""
    
    def __init__(self):
        self.tool_name = "forge"
        self.version = self._get_version()
    
    def _get_version(self) -> str:
        """Get Forge version"""
        try:
            result = subprocess.run(
                ['forge', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Unknown (Error: {e})"
    
    def init_project(self, project_path: str) -> Dict[str, Any]:
        """
        Initialize a new Foundry project
        
        Args:
            project_path: Path where to create the project
            
        Returns:
            Dictionary with initialization result
        """
        try:
            os.makedirs(project_path, exist_ok=True)
            
            result = subprocess.run(
                ['forge', 'init', '--force'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "project_path": project_path,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to initialize project: {str(e)}"
            }
    
    def compile(self, project_path: str) -> Dict[str, Any]:
        """
        Compile contracts in a Foundry project
        
        Args:
            project_path: Path to the Foundry project
            
        Returns:
            Dictionary with compilation result
        """
        try:
            result = subprocess.run(
                ['forge', 'build'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Compilation timed out after 120 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Compilation failed: {str(e)}"
            }
    
    def run_tests(self, 
                  project_path: str,
                  test_pattern: str = None,
                  verbosity: int = 2,
                  fork_url: str = None) -> Dict[str, Any]:
        """
        Run tests in a Foundry project
        
        Args:
            project_path: Path to the Foundry project
            test_pattern: Pattern to match test names (e.g., "testReentrancy")
            verbosity: Verbosity level (0-5)
            fork_url: RPC URL for forking mainnet
            
        Returns:
            Dictionary with test results
        """
        try:
            cmd = ['forge', 'test']
            
            if test_pattern:
                cmd.extend(['--match-test', test_pattern])
            
            # Add verbosity flags
            if verbosity > 0:
                cmd.append('-' + 'v' * min(verbosity, 5))
            
            if fork_url:
                cmd.extend(['--fork-url', fork_url])
            
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse test results
            test_results = self._parse_test_output(result.stdout)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "tests": test_results,
                "all_passed": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tests timed out after 300 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}"
            }
    
    def _parse_test_output(self, output: str) -> List[Dict]:
        """
        Parse Forge test output to extract test results
        
        Args:
            output: Raw test output
            
        Returns:
            List of test results
        """
        tests = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for test result lines
            if '[PASS]' in line or '[FAIL]' in line:
                passed = '[PASS]' in line
                
                # Extract test name
                parts = line.split()
                test_name = None
                for i, part in enumerate(parts):
                    if part in ['[PASS]', '[FAIL]']:
                        if i + 1 < len(parts):
                            test_name = parts[i + 1]
                        break
                
                if test_name:
                    tests.append({
                        "name": test_name,
                        "passed": passed,
                        "line": line
                    })
        
        return tests
    
    def run_poc(self, 
                project_path: str,
                poc_test_name: str,
                fork_url: str = None) -> Dict[str, Any]:
        """
        Run a specific PoC test
        
        Args:
            project_path: Path to the Foundry project
            poc_test_name: Name of the PoC test
            fork_url: RPC URL for forking mainnet
            
        Returns:
            Dictionary with PoC execution results
        """
        result = self.run_tests(
            project_path=project_path,
            test_pattern=poc_test_name,
            verbosity=3,
            fork_url=fork_url
        )
        
        if result.get('success'):
            tests = result.get('tests', [])
            poc_test = next((t for t in tests if poc_test_name in t['name']), None)
            
            if poc_test:
                result['poc_executed'] = True
                result['poc_passed'] = poc_test['passed']
                result['exploitation_successful'] = poc_test['passed']
            else:
                result['poc_executed'] = False
                result['error'] = f"PoC test '{poc_test_name}' not found"
        
        return result
    
    def create_poc_file(self,
                       project_path: str,
                       poc_name: str,
                       poc_code: str) -> Dict[str, Any]:
        """
        Create a PoC test file
        
        Args:
            project_path: Path to the Foundry project
            poc_name: Name of the PoC
            poc_code: Solidity code for the PoC
            
        Returns:
            Dictionary with file creation result
        """
        try:
            test_dir = os.path.join(project_path, 'test')
            os.makedirs(test_dir, exist_ok=True)
            
            poc_file = os.path.join(test_dir, f"{poc_name}.t.sol")
            
            with open(poc_file, 'w') as f:
                f.write(poc_code)
            
            return {
                "success": True,
                "poc_file": poc_file,
                "poc_name": poc_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create PoC file: {str(e)}"
            }
    
    def generate_report(self, test_result: Dict) -> str:
        """
        Generate a human-readable report from test results
        
        Args:
            test_result: Test results dictionary
            
        Returns:
            Formatted report string
        """
        if not test_result.get('success'):
            return f"Test execution failed: {test_result.get('error', 'Unknown error')}"
        
        tests = test_result.get('tests', [])
        passed = sum(1 for t in tests if t['passed'])
        failed = len(tests) - passed
        
        report = f"""
=== Foundry Test Report ===
Total Tests: {len(tests)}
Passed: {passed}
Failed: {failed}

Test Results:
"""
        
        for test in tests:
            status = "✓ PASS" if test['passed'] else "✗ FAIL"
            report += f"  {status} - {test['name']}\n"
        
        if test_result.get('poc_executed'):
            report += f"\nPoC Execution: {'SUCCESS' if test_result.get('exploitation_successful') else 'FAILED'}\n"
        
        return report


if __name__ == "__main__":
    # Test the wrapper
    wrapper = FoundryWrapper()
    print(f"Forge version: {wrapper.version}")
