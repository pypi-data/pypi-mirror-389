"""
Comprehensive tests for src/parallel/parallel_audit.py
Target: Increase coverage from 20.15% to 75%+
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import json
import subprocess

from src.parallel.parallel_audit import (
    ParallelSlitherAnalyzer,
    ParallelFoundryTester
)
from src.parallel.parallel_processor import ParallelTask, ParallelResult


class TestParallelSlitherAnalyzer:
    """Tests for ParallelSlitherAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self):
        """Create ParallelSlitherAnalyzer instance"""
        return ParallelSlitherAnalyzer(max_workers=4)
    
    def test_init(self):
        """Test analyzer initialization"""
        analyzer = ParallelSlitherAnalyzer(max_workers=4)
        assert analyzer.processor is not None
        assert analyzer.slither_path == "slither"
        assert analyzer.processor.max_workers == 4
    
    def test_init_custom_workers(self):
        """Test initialization with custom worker count"""
        analyzer = ParallelSlitherAnalyzer(max_workers=8)
        assert analyzer.processor.max_workers == 8
    
    @patch('src.parallel.parallel_audit.ParallelProcessor.execute')
    def test_analyze_contracts_success(self, mock_execute, analyzer):
        """Test successful contract analysis"""
        mock_execute.return_value = [
            ParallelResult(
                task_id="slither_Contract1",
                success=True,
                result={
                    "contract": "Contract1.sol",
                    "success": True,
                    "results": {"detectors": []},
                    "detector_count": 0
                },
                execution_time=1.5
            )
        ]
        
        contract_paths = ["Contract1.sol"]
        results = analyzer.analyze_contracts(contract_paths)
        
        assert len(results) == 1
        assert results[0]["contract"] == "Contract1.sol"
        assert results[0]["success"] is True
    
    @patch('subprocess.run')
    def test_run_slither_success(self, mock_run, analyzer):
        """Test successful Slither execution"""
        # Mock successful Slither output
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({
                "results": {
                    "detectors": [
                        {"check": "reentrancy", "impact": "High"}
                    ]
                }
            }),
            stderr=""
        )
        
        result = analyzer._run_slither("test.sol")
        
        assert result["success"] is True
        assert result["contract"] == "test.sol"
        assert result["detector_count"] == 1
        assert "results" in result
    
    @patch('subprocess.run')
    def test_run_slither_json_parse_error(self, mock_run, analyzer):
        """Test Slither with invalid JSON output"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="invalid json",
            stderr=""
        )
        
        result = analyzer._run_slither("test.sol")
        
        assert result["success"] is False
        assert "parse" in result["error"].lower()
    
    @patch('subprocess.run')
    def test_run_slither_command_failure(self, mock_run, analyzer):
        """Test Slither command failure"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Slither error: File not found"
        )
        
        result = analyzer._run_slither("nonexistent.sol")
        
        assert result["success"] is False
        assert "error" in result["error"].lower() or "not found" in result["error"].lower()
    
    @patch('subprocess.run')
    def test_run_slither_timeout(self, mock_run, analyzer):
        """Test Slither timeout handling"""
        mock_run.side_effect = subprocess.TimeoutExpired("slither", 60)
        
        result = analyzer._run_slither("slow.sol")
        
        assert result["success"] is False
        assert "timed out" in result["error"].lower()
    
    @patch('subprocess.run')
    def test_run_slither_exception(self, mock_run, analyzer):
        """Test Slither unexpected exception"""
        mock_run.side_effect = Exception("Unexpected error")
        
        result = analyzer._run_slither("error.sol")
        
        assert result["success"] is False
        assert "Unexpected error" in result["error"]
    
    def test_format_result_success(self, analyzer):
        """Test result formatting for successful analysis"""
        parallel_result = ParallelResult(
            task_id="slither_test",
            success=True,
            result={
                "contract": "test.sol",
                "success": True,
                "results": {"detectors": []},
                "detector_count": 0
            },
            execution_time=1.0
        )
        
        formatted = analyzer._format_result(parallel_result)
        
        assert formatted["contract"] == "test.sol"
        assert formatted["success"] is True
        assert formatted["execution_time"] == 1.0
    
    def test_format_result_failure(self, analyzer):
        """Test result formatting for failed analysis"""
        parallel_result = ParallelResult(
            task_id="slither_test",
            success=False,
            result=None,
            execution_time=0.5,
            error="Analysis failed"
        )
        
        formatted = analyzer._format_result(parallel_result)
        
        assert formatted["success"] is False
        assert formatted["error"] == "Analysis failed"
    
    @patch('src.parallel.parallel_audit.ParallelProcessor.execute')
    def test_analyze_multiple_contracts(self, mock_execute, analyzer):
        """Test analyzing multiple contracts"""
        mock_execute.return_value = [
            ParallelResult(
                task_id=f"slither_Contract{i}",
                success=True,
                result={
                    "contract": f"Contract{i}.sol",
                    "success": True,
                    "results": {},
                    "detector_count": i
                },
                execution_time=1.0
            )
            for i in range(3)
        ]
        
        results = analyzer.analyze_contracts([f"Contract{i}.sol" for i in range(3)])
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["contract"] == f"Contract{i}.sol"
            assert result["detector_count"] == i


class TestParallelFoundryTester:
    """Tests for ParallelFoundryTester class"""
    
    @pytest.fixture
    def tester(self):
        """Create ParallelFoundryTester instance"""
        return ParallelFoundryTester(max_workers=4)
    
    def test_init(self):
        """Test tester initialization"""
        tester = ParallelFoundryTester(max_workers=4)
        assert tester.processor is not None
        assert tester.forge_path == "forge"
    
    @patch('src.parallel.parallel_audit.ParallelProcessor.execute')
    def test_run_tests_success(self, mock_execute, tester, tmp_path):
        """Test successful test execution"""
        mock_execute.return_value = [
            ParallelResult(
                task_id="forge_test_TestContract",
                success=True,
                result={
                    "test": "TestContract",
                    "success": True,
                    "passed": True,
                    "output": "Test passed"
                },
                execution_time=5.0
            )
        ]
        
        results = tester.run_tests(["TestContract"], str(tmp_path))
        
        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["passed"] is True
    
    @patch('subprocess.run')
    def test_run_forge_test_success(self, mock_run, tester):
        """Test successful Forge test execution"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="[PASS] testExample",
            stderr=""
        )
        
        test_data = {"test": "TestContract", "project_root": "/tmp"}
        result = tester._run_forge_test(test_data)
        
        assert result["success"] is True
        assert result["test"] == "TestContract"
        assert result["passed"] is True
    
    @patch('subprocess.run')
    def test_run_forge_test_failure(self, mock_run, tester):
        """Test Forge test failure"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="[FAIL] testExample",
            stderr="Forge error: Tests failed"
        )
        
        test_data = {"test": "FailingTest", "project_root": "/tmp"}
        result = tester._run_forge_test(test_data)
        
        assert result["success"] is True  # Command succeeded
        assert result["passed"] is False  # But test failed
    
    @patch('subprocess.run')
    def test_run_forge_test_timeout(self, mock_run, tester):
        """Test Forge test timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("forge", 120)
        
        test_data = {"test": "SlowTest", "project_root": "/tmp"}
        result = tester._run_forge_test(test_data)
        
        assert result["success"] is False
        assert "timed out" in result["error"].lower()
    
    @patch('subprocess.run')
    def test_run_forge_test_exception(self, mock_run, tester):
        """Test Forge test exception handling"""
        mock_run.side_effect = Exception("Forge not found")
        
        test_data = {"test": "TestContract", "project_root": "/tmp"}
        result = tester._run_forge_test(test_data)
        
        assert result["success"] is False
        assert "Forge not found" in result["error"]


class TestIntegration:
    """Integration tests for parallel audit operations"""
    
    @pytest.mark.integration
    def test_slither_analyzer_workflow(self, tmp_path):
        """Test complete Slither analysis workflow"""
        # Create test contract file
        contract_file = tmp_path / "Test.sol"
        contract_file.write_text("contract Test { function test() public {} }")
        
        analyzer = ParallelSlitherAnalyzer(max_workers=2)
        
        # Test that analyzer is properly initialized
        assert analyzer.processor is not None
        assert analyzer.slither_path == "slither"
    
    @pytest.mark.integration
    def test_foundry_tester_workflow(self):
        """Test complete Foundry testing workflow"""
        tester = ParallelFoundryTester(max_workers=2)
        
        # Test that tester is properly initialized
        assert tester.processor is not None
        assert tester.forge_path == "forge"
    
    @pytest.mark.integration
    @patch('subprocess.run')
    def test_end_to_end_audit(self, mock_run, tmp_path):
        """Test end-to-end audit process"""
        # Create test contract
        contract_file = tmp_path / "Vulnerable.sol"
        contract_file.write_text("""
        contract Vulnerable {
            function withdraw() public {
                msg.sender.call.value(balance)("");
                balance = 0;
            }
        }
        """)
        
        # Mock Slither finding reentrancy
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({
                "results": {
                    "detectors": [
                        {
                            "check": "reentrancy-eth",
                            "impact": "High",
                            "confidence": "High"
                        }
                    ]
                }
            }),
            stderr=""
        )
        
        analyzer = ParallelSlitherAnalyzer(max_workers=1)
        result = analyzer._run_slither(str(contract_file))
        
        assert result["success"] is True
        assert result["detector_count"] == 1
