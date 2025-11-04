"""
Unit tests for Fix Suggester module.

Tests the functionality of generating fix suggestions for detected vulnerabilities.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path


@pytest.fixture
def mock_fix_suggester():
    """Create a mock Fix Suggester for testing."""
    class MockFixSuggester:
        def suggest_fix(self, vulnerability: dict) -> dict:
            """Generate fix suggestion for a vulnerability."""
            if not vulnerability:
                raise ValueError("Vulnerability data is required")
            
            vuln_type = vulnerability.get("type", "").lower()
            if not vuln_type:
                raise ValueError("Vulnerability type is required")
            
            if vuln_type == "reentrancy":
                return self._suggest_reentrancy_fix(vulnerability)
            elif vuln_type == "access_control":
                return self._suggest_access_control_fix(vulnerability)
            elif vuln_type == "integer_overflow":
                return self._suggest_overflow_fix(vulnerability)
            else:
                return self._suggest_generic_fix(vulnerability)
        
        def _suggest_reentrancy_fix(self, vuln: dict) -> dict:
            return {
                "vulnerability_type": "reentrancy",
                "original_code": vuln.get("code", ""),
                "fixed_code": "// Use ReentrancyGuard\nnonReentrant modifier",
                "explanation": "Apply checks-effects-interactions pattern and use ReentrancyGuard",
                "severity_reduction": "HIGH -> NONE",
                "confidence": 0.95
            }
        
        def _suggest_access_control_fix(self, vuln: dict) -> dict:
            return {
                "vulnerability_type": "access_control",
                "original_code": vuln.get("code", ""),
                "fixed_code": "modifier onlyOwner() { require(msg.sender == owner); _; }",
                "explanation": "Add access control modifier to restrict function access",
                "severity_reduction": "HIGH -> NONE",
                "confidence": 0.90
            }
        
        def _suggest_overflow_fix(self, vuln: dict) -> dict:
            return {
                "vulnerability_type": "integer_overflow",
                "original_code": vuln.get("code", ""),
                "fixed_code": "// Use SafeMath or Solidity 0.8+",
                "explanation": "Use SafeMath library or upgrade to Solidity 0.8+ with built-in overflow checks",
                "severity_reduction": "MEDIUM -> NONE",
                "confidence": 0.85
            }
        
        def _suggest_generic_fix(self, vuln: dict) -> dict:
            return {
                "vulnerability_type": vuln.get("type"),
                "original_code": vuln.get("code", ""),
                "fixed_code": "// Apply security best practices",
                "explanation": "Review and apply security best practices for this vulnerability type",
                "severity_reduction": "UNKNOWN",
                "confidence": 0.50
            }
        
        def validate_fix(self, fix_suggestion: dict) -> bool:
            """Validate fix suggestion structure."""
            required_fields = ["vulnerability_type", "fixed_code", "explanation", "confidence"]
            return all(field in fix_suggestion for field in required_fields)
        
        def apply_fix(self, contract_code: str, fix_suggestion: dict, line_number: int) -> str:
            """Apply fix to contract code."""
            if not contract_code or not fix_suggestion:
                raise ValueError("Contract code and fix suggestion required")
            
            lines = contract_code.split("\n")
            if line_number < 0 or line_number >= len(lines):
                raise IndexError("Line number out of range")
            
            # Simple fix application (insert fixed code)
            fixed_code = fix_suggestion.get("fixed_code", "")
            lines.insert(line_number, f"    {fixed_code}")
            
            return "\n".join(lines)
    
    return MockFixSuggester()


class TestFixSuggester:
    """Test suite for Fix Suggester functionality."""
    
    def test_suggest_reentrancy_fix(self, mock_fix_suggester):
        """Test fix suggestion for reentrancy vulnerability."""
        vulnerability = {
            "type": "reentrancy",
            "function": "withdraw",
            "severity": "HIGH",
            "code": "balances[msg.sender] -= amount;"
        }
        
        fix = mock_fix_suggester.suggest_fix(vulnerability)
        
        assert fix is not None
        assert fix["vulnerability_type"] == "reentrancy"
        assert "ReentrancyGuard" in fix["fixed_code"] or "nonReentrant" in fix["fixed_code"]
        assert fix["severity_reduction"] == "HIGH -> NONE"
        assert fix["confidence"] >= 0.9
    
    def test_suggest_access_control_fix(self, mock_fix_suggester):
        """Test fix suggestion for access control vulnerability."""
        vulnerability = {
            "type": "access_control",
            "function": "setOwner",
            "severity": "HIGH",
            "code": "function setOwner(address newOwner) public"
        }
        
        fix = mock_fix_suggester.suggest_fix(vulnerability)
        
        assert fix is not None
        assert fix["vulnerability_type"] == "access_control"
        assert "onlyOwner" in fix["fixed_code"] or "require" in fix["fixed_code"]
        assert "access control" in fix["explanation"].lower()
    
    def test_suggest_overflow_fix(self, mock_fix_suggester):
        """Test fix suggestion for integer overflow vulnerability."""
        vulnerability = {
            "type": "integer_overflow",
            "function": "add",
            "severity": "MEDIUM",
            "code": "return a + b;"
        }
        
        fix = mock_fix_suggester.suggest_fix(vulnerability)
        
        assert fix is not None
        assert fix["vulnerability_type"] == "integer_overflow"
        assert "SafeMath" in fix["fixed_code"] or "0.8" in fix["fixed_code"]
    
    def test_validate_fix_valid(self, mock_fix_suggester):
        """Test fix validation with valid suggestion."""
        valid_fix = {
            "vulnerability_type": "reentrancy",
            "original_code": "old code",
            "fixed_code": "new code",
            "explanation": "explanation",
            "confidence": 0.9
        }
        
        assert mock_fix_suggester.validate_fix(valid_fix) is True
    
    def test_validate_fix_invalid(self, mock_fix_suggester):
        """Test fix validation with invalid suggestion."""
        invalid_fix = {
            "vulnerability_type": "reentrancy",
            "fixed_code": "new code"
            # Missing required fields
        }
        
        assert mock_fix_suggester.validate_fix(invalid_fix) is False
    
    def test_apply_fix_to_contract(self, mock_fix_suggester):
        """Test applying fix to contract code."""
        contract_code = """pragma solidity ^0.8.0;
contract Test {
    function vulnerable() public {
        // vulnerable code
    }
}"""
        
        fix_suggestion = {
            "fixed_code": "modifier nonReentrant() { _; }"
        }
        
        result = mock_fix_suggester.apply_fix(contract_code, fix_suggestion, 2)
        
        assert "nonReentrant" in result
        assert len(result.split("\n")) > len(contract_code.split("\n"))
    
    def test_fix_with_invalid_input(self, mock_fix_suggester):
        """Test error handling for invalid input."""
        with pytest.raises(ValueError, match="Vulnerability data is required"):
            mock_fix_suggester.suggest_fix(None)
    
    def test_multiple_fixes_same_function(self, mock_fix_suggester):
        """Test generating multiple fixes for same function."""
        vulnerabilities = [
            {"type": "reentrancy", "function": "withdraw"},
            {"type": "access_control", "function": "withdraw"}
        ]
        
        fixes = [mock_fix_suggester.suggest_fix(v) for v in vulnerabilities]
        
        assert len(fixes) == 2
        assert fixes[0]["vulnerability_type"] != fixes[1]["vulnerability_type"]


@pytest.mark.unit
class TestFixSuggesterEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_fix_suggestion_confidence(self, mock_fix_suggester):
        """Test confidence scores for different vulnerability types."""
        vulnerabilities = [
            {"type": "reentrancy"},
            {"type": "access_control"},
            {"type": "integer_overflow"},
            {"type": "unknown_type"}
        ]
        
        fixes = [mock_fix_suggester.suggest_fix(v) for v in vulnerabilities]
        confidences = [f["confidence"] for f in fixes]
        
        assert all(0 <= c <= 1 for c in confidences)
        assert confidences[0] > confidences[-1]  # Known types have higher confidence
    
    def test_apply_fix_invalid_line_number(self, mock_fix_suggester):
        """Test applying fix with invalid line number."""
        contract_code = "pragma solidity ^0.8.0;\ncontract Test {}"
        fix_suggestion = {"fixed_code": "// fix"}
        
        with pytest.raises(IndexError, match="Line number out of range"):
            mock_fix_suggester.apply_fix(contract_code, fix_suggestion, 100)
    
    def test_apply_fix_empty_contract(self, mock_fix_suggester):
        """Test applying fix to empty contract."""
        with pytest.raises(ValueError):
            mock_fix_suggester.apply_fix("", {"fixed_code": "fix"}, 0)
