#!/usr/bin/env python3
"""
Parallel Audit Engine - Integrates with existing audit tools
Enables parallel execution of Slither, Foundry tests, and database queries
"""

import os
import sys
import json
import subprocess
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .parallel_processor import ParallelProcessor, ParallelTask, ParallelResult

logger = logging.getLogger(__name__)


class ParallelSlitherAnalyzer:
    """Run Slither analysis on multiple contracts in parallel"""
    
    def __init__(self, max_workers: int = 4):
        self.processor = ParallelProcessor(max_workers=max_workers)
        self.slither_path = "slither"
    
    def analyze_contracts(self, contract_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple contracts with Slither in parallel
        
        Args:
            contract_paths: List of Solidity contract file paths
            
        Returns:
            List of analysis results
        """
        logger.info(f"Analyzing {len(contract_paths)} contracts with Slither in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"slither_{Path(path).stem}",
                input_data=path,
                metadata={"contract_name": Path(path).name}
            )
            for path in contract_paths
        ]
        
        results = self.processor.execute(self._run_slither, tasks)
        
        return [self._format_result(r) for r in results]
    
    def _run_slither(self, contract_path: str) -> Dict[str, Any]:
        """Run Slither on a single contract"""
        try:
            # Run Slither with JSON output
            cmd = [self.slither_path, contract_path, "--json", "-"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 or result.stdout:
                # Parse JSON output
                try:
                    data = json.loads(result.stdout)
                    return {
                        "contract": contract_path,
                        "success": True,
                        "results": data.get("results", {}),
                        "detector_count": len(data.get("results", {}).get("detectors", []))
                    }
                except json.JSONDecodeError:
                    return {
                        "contract": contract_path,
                        "success": False,
                        "error": "Failed to parse Slither JSON output"
                    }
            else:
                return {
                    "contract": contract_path,
                    "success": False,
                    "error": result.stderr or "Slither analysis failed"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "contract": contract_path,
                "success": False,
                "error": "Slither analysis timed out (60s)"
            }
        except Exception as e:
            return {
                "contract": contract_path,
                "success": False,
                "error": str(e)
            }
    
    def _format_result(self, result: ParallelResult) -> Dict[str, Any]:
        """Format parallel result for output"""
        if result.success and result.result:
            return {
                **result.result,
                "execution_time": result.execution_time,
                "task_id": result.task_id
            }
        else:
            return {
                "contract": result.metadata.get("contract_name", "unknown") if result.metadata else "unknown",
                "success": False,
                "error": result.error,
                "execution_time": result.execution_time
            }


class ParallelFoundryTester:
    """Run Foundry tests on multiple contracts in parallel"""
    
    def __init__(self, max_workers: int = 4):
        self.processor = ParallelProcessor(max_workers=max_workers)
        self.forge_path = "forge"
    
    def run_tests(self, test_contracts: List[str], project_root: str) -> List[Dict[str, Any]]:
        """
        Run Foundry tests in parallel
        
        Args:
            test_contracts: List of test contract names
            project_root: Root directory of Foundry project
            
        Returns:
            List of test results
        """
        logger.info(f"Running {len(test_contracts)} Foundry tests in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"forge_test_{test}",
                input_data={"test": test, "project_root": project_root},
                metadata={"test_name": test}
            )
            for test in test_contracts
        ]
        
        results = self.processor.execute(self._run_forge_test, tasks)
        
        return [self._format_result(r) for r in results]
    
    def _run_forge_test(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single Foundry test"""
        test_name = test_data["test"]
        project_root = test_data["project_root"]
        
        try:
            cmd = [
                self.forge_path, "test",
                "--match-contract", test_name,
                "--json"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse test results
            passed = "PASS" in result.stdout or result.returncode == 0
            
            return {
                "test": test_name,
                "success": True,
                "passed": passed,
                "output": result.stdout[:500]  # Truncate output
            }
            
        except subprocess.TimeoutExpired:
            return {
                "test": test_name,
                "success": False,
                "error": "Test timed out (120s)"
            }
        except Exception as e:
            return {
                "test": test_name,
                "success": False,
                "error": str(e)
            }
    
    def _format_result(self, result: ParallelResult) -> Dict[str, Any]:
        """Format parallel result"""
        if result.success and result.result:
            return {
                **result.result,
                "execution_time": result.execution_time
            }
        else:
            return {
                "test": result.metadata.get("test_name", "unknown") if result.metadata else "unknown",
                "success": False,
                "error": result.error,
                "execution_time": result.execution_time
            }


class ParallelVulnerabilityAnalyzer:
    """Analyze multiple vulnerabilities in parallel"""
    
    def __init__(self, max_workers: int = 4):
        self.processor = ParallelProcessor(max_workers=max_workers)
    
    def analyze_vulnerabilities(
        self,
        vulnerabilities: List[Dict[str, Any]],
        contract_code: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple vulnerabilities in parallel
        
        Args:
            vulnerabilities: List of detected vulnerabilities
            contract_code: Source code of the contract
            
        Returns:
            List of analysis results with severity and impact
        """
        logger.info(f"Analyzing {len(vulnerabilities)} vulnerabilities in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"analyze_{vuln.get('check', 'unknown')}_{i}",
                input_data={"vulnerability": vuln, "code": contract_code},
                metadata={"vuln_type": vuln.get("check")}
            )
            for i, vuln in enumerate(vulnerabilities)
        ]
        
        results = self.processor.execute(self._analyze_single_vulnerability, tasks)
        
        return [r.result for r in results if r.success and r.result]
    
    def _analyze_single_vulnerability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single vulnerability for severity and exploitability"""
        vuln = data["vulnerability"]
        code = data["code"]
        
        # Extract vulnerability details
        check = vuln.get("check", "unknown")
        impact = vuln.get("impact", "Unknown")
        confidence = vuln.get("confidence", "Unknown")
        description = vuln.get("description", "")
        
        # Determine severity based on impact and exploitability
        severity = self._calculate_severity(check, impact, confidence, description, code)
        
        # Check if PoC is needed
        needs_poc = severity in ["HIGH", "CRITICAL"]
        
        return {
            "check": check,
            "impact": impact,
            "confidence": confidence,
            "severity": severity,
            "description": description,
            "needs_poc": needs_poc,
            "exploitable": self._is_exploitable(check, code)
        }
    
    def _calculate_severity(
        self,
        check: str,
        impact: str,
        confidence: str,
        description: str,
        code: str
    ) -> str:
        """Calculate vulnerability severity"""
        # High-impact vulnerabilities
        high_impact_checks = [
            "reentrancy-eth",
            "reentrancy-no-eth",
            "arbitrary-send-eth",
            "controlled-delegatecall",
            "unprotected-upgrade"
        ]
        
        # Medium-impact vulnerabilities
        medium_impact_checks = [
            "unchecked-lowlevel",
            "unchecked-send",
            "tx-origin",
            "timestamp"
        ]
        
        if check in high_impact_checks and impact == "High":
            return "HIGH"
        elif check in medium_impact_checks:
            return "MEDIUM"
        elif impact == "High":
            return "MEDIUM"
        elif impact == "Medium":
            return "LOW"
        else:
            return "INFORMATIONAL"
    
    def _is_exploitable(self, check: str, code: str) -> bool:
        """Determine if vulnerability is exploitable"""
        # Simplified exploitability check
        exploitable_checks = [
            "reentrancy-eth",
            "arbitrary-send-eth",
            "controlled-delegatecall"
        ]
        return check in exploitable_checks


def demo_parallel_audit():
    """Demonstrate parallel audit capabilities"""
    print("=== Parallel Audit Engine Demo ===\n")
    
    # Demo 1: Parallel Slither analysis
    print("1. Parallel Slither Analysis")
    slither = ParallelSlitherAnalyzer(max_workers=4)
    
    # Create dummy contracts for testing
    test_contracts = ["tests/VulnerableBank.sol"]
    if os.path.exists(test_contracts[0]):
        results = slither.analyze_contracts(test_contracts)
        print(f"   Analyzed {len(results)} contracts")
        for r in results:
            print(f"   - {r.get('contract', 'unknown')}: "
                  f"{'SUCCESS' if r.get('success') else 'FAILED'}")
    else:
        print("   Skipped (test contract not found)")
    
    print()
    
    # Demo 2: Parallel vulnerability analysis
    print("2. Parallel Vulnerability Analysis")
    analyzer = ParallelVulnerabilityAnalyzer(max_workers=4)
    
    sample_vulns = [
        {"check": "reentrancy-eth", "impact": "High", "confidence": "High", "description": "Reentrancy vulnerability"},
        {"check": "unchecked-lowlevel", "impact": "Medium", "confidence": "Medium", "description": "Unchecked call"},
        {"check": "timestamp", "impact": "Low", "confidence": "Medium", "description": "Timestamp dependency"}
    ]
    
    results = analyzer.analyze_vulnerabilities(sample_vulns, "// Sample contract code")
    print(f"   Analyzed {len(results)} vulnerabilities")
    for r in results:
        print(f"   - {r['check']}: Severity={r['severity']}, PoC needed={r['needs_poc']}")
    
    print("\n=== Demo complete ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_parallel_audit()
