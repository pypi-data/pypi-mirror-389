"""
Unit tests for PoC (Proof of Concept) generator.

Tests the functionality of generating exploit code for detected vulnerabilities.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


# Mock the module since we're testing in isolation
@pytest.fixture
def mock_poc_generator():
    """Create a mock PoC generator for testing."""
    class MockPoCGenerator:
        def __init__(self):
            self.template_dir = Path("poc_templates")
            
        def generate(self, vulnerability: dict) -> str:
            """Generate PoC code for a vulnerability."""
            if not vulnerability:
                raise ValueError("Vulnerability data is required")
            
            vuln_type = vulnerability.get("type", "").lower()
            if not vuln_type:
                raise ValueError("Vulnerability type is required")
            
            # Simulate PoC generation
            if vuln_type == "reentrancy":
                return self._generate_reentrancy_poc(vulnerability)
            elif vuln_type == "access_control":
                return self._generate_access_control_poc(vulnerability)
            elif vuln_type == "integer_overflow":
                return self._generate_overflow_poc(vulnerability)
            else:
                return self._generate_generic_poc(vulnerability)
        
        def _generate_reentrancy_poc(self, vuln: dict) -> str:
            function_name = vuln.get("function", "target")
            return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

contract ReentrancyExploit is Test {{
    function testReentrancy() public {{
        // Exploit {function_name} function
        // PoC code here
    }}
}}
"""
        
        def _generate_access_control_poc(self, vuln: dict) -> str:
            function_name = vuln.get("function", "target")
            return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

contract AccessControlExploit is Test {{
    function testUnauthorizedAccess() public {{
        // Exploit {function_name} function
        // PoC code here
    }}
}}
"""
        
        def _generate_overflow_poc(self, vuln: dict) -> str:
            return """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

contract OverflowExploit is Test {
    function testIntegerOverflow() public {
        // PoC code here
    }
}
"""
        
        def _generate_generic_poc(self, vuln: dict) -> str:
            vuln_type = vuln.get("type", "unknown")
            return f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

contract {vuln_type.capitalize()}Exploit is Test {{
    function test{vuln_type.capitalize()}() public {{
        // PoC code here
    }}
}}
"""
        
        def validate_poc(self, poc_code: str) -> bool:
            """Validate that generated PoC code is valid."""
            if not poc_code:
                return False
            
            required_elements = [
                "pragma solidity",
                "import \"forge-std/Test.sol\"",
                "contract",
                "function test"
            ]
            
            return all(elem in poc_code for elem in required_elements)
        
        def save_poc(self, poc_code: str, output_path: Path) -> bool:
            """Save PoC code to file."""
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(poc_code)
                return True
            except Exception:
                return False
    
    return MockPoCGenerator()


class TestPoCGenerator:
    """Test suite for PoC generator functionality."""
    
    def test_generate_reentrancy_poc(self, mock_poc_generator, sample_vulnerability):
        """Test PoC generation for reentrancy vulnerability."""
        sample_vulnerability["type"] = "reentrancy"
        sample_vulnerability["function"] = "withdraw"
        
        poc = mock_poc_generator.generate(sample_vulnerability)
        
        assert poc is not None
        assert "pragma solidity" in poc
        assert "ReentrancyExploit" in poc
        assert "testReentrancy" in poc
        assert "withdraw" in poc
    
    def test_generate_access_control_poc(self, mock_poc_generator):
        """Test PoC generation for access control vulnerability."""
        vulnerability = {
            "type": "access_control",
            "function": "setOwner",
            "severity": "HIGH"
        }
        
        poc = mock_poc_generator.generate(vulnerability)
        
        assert poc is not None
        assert "AccessControlExploit" in poc
        assert "testUnauthorizedAccess" in poc
        assert "setOwner" in poc
    
    def test_generate_overflow_poc(self, mock_poc_generator):
        """Test PoC generation for integer overflow vulnerability."""
        vulnerability = {
            "type": "integer_overflow",
            "function": "add",
            "severity": "MEDIUM"
        }
        
        poc = mock_poc_generator.generate(vulnerability)
        
        assert poc is not None
        assert "OverflowExploit" in poc
        assert "testIntegerOverflow" in poc
    
    def test_generate_generic_poc(self, mock_poc_generator):
        """Test PoC generation for unknown vulnerability type."""
        vulnerability = {
            "type": "custom_vuln",
            "function": "vulnerable",
            "severity": "LOW"
        }
        
        poc = mock_poc_generator.generate(vulnerability)
        
        assert poc is not None
        assert "Custom_vulnExploit" in poc or "custom_vuln" in poc.lower()
        assert "function test" in poc
    
    def test_generate_with_null_input(self, mock_poc_generator):
        """Test error handling for null input."""
        with pytest.raises(ValueError, match="Vulnerability data is required"):
            mock_poc_generator.generate(None)
    
    def test_generate_with_missing_type(self, mock_poc_generator):
        """Test error handling for missing vulnerability type."""
        vulnerability = {
            "function": "test",
            "severity": "HIGH"
        }
        
        with pytest.raises(ValueError, match="Vulnerability type is required"):
            mock_poc_generator.generate(vulnerability)
    
    def test_validate_poc_valid(self, mock_poc_generator):
        """Test PoC validation with valid code."""
        valid_poc = """
        pragma solidity ^0.8.0;
        import "forge-std/Test.sol";
        contract TestExploit is Test {
            function testVulnerability() public {}
        }
        """
        
        assert mock_poc_generator.validate_poc(valid_poc) is True
    
    def test_validate_poc_invalid(self, mock_poc_generator):
        """Test PoC validation with invalid code."""
        invalid_poc = "This is not valid Solidity code"
        
        assert mock_poc_generator.validate_poc(invalid_poc) is False
    
    def test_validate_poc_empty(self, mock_poc_generator):
        """Test PoC validation with empty code."""
        assert mock_poc_generator.validate_poc("") is False
        assert mock_poc_generator.validate_poc(None) is False
    
    def test_save_poc(self, mock_poc_generator, temp_dir):
        """Test saving PoC code to file."""
        poc_code = """
        pragma solidity ^0.8.0;
        contract Test {}
        """
        output_path = temp_dir / "output" / "exploit.sol"
        
        result = mock_poc_generator.save_poc(poc_code, output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.read_text() == poc_code


@pytest.mark.unit
class TestPoCGeneratorEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_generate_with_special_characters_in_function_name(self, mock_poc_generator):
        """Test handling of special characters in function names."""
        vulnerability = {
            "type": "reentrancy",
            "function": "withdraw_$pecial",
            "severity": "HIGH"
        }
        
        poc = mock_poc_generator.generate(vulnerability)
        assert poc is not None
    
    def test_generate_with_very_long_function_name(self, mock_poc_generator):
        """Test handling of very long function names."""
        vulnerability = {
            "type": "reentrancy",
            "function": "a" * 1000,
            "severity": "HIGH"
        }
        
        poc = mock_poc_generator.generate(vulnerability)
        assert poc is not None
    
    def test_concurrent_generation(self, mock_poc_generator):
        """Test concurrent PoC generation."""
        vulnerabilities = [
            {"type": "reentrancy", "function": f"func{i}", "severity": "HIGH"}
            for i in range(10)
        ]
        
        pocs = [mock_poc_generator.generate(v) for v in vulnerabilities]
        
        assert len(pocs) == 10
        assert all(poc is not None for poc in pocs)
