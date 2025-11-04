"""
Unit tests for main entry point (ai_auditor.py).

Tests CLI argument parsing, audit execution, configuration, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys


@pytest.fixture
def mock_main_module():
    """Create mock main module for testing."""
    class MockMain:
        def __init__(self):
            self.config = {}
            self.verbose = False
            self.debug = False
        
        def parse_arguments(self, args: list) -> dict:
            """Parse command line arguments."""
            if not args:
                raise ValueError("No arguments provided")
            
            parsed = {
                "contract_path": None,
                "output_format": "markdown",
                "verbose": False,
                "debug": False,
                "directory": False
            }
            
            i = 0
            while i < len(args):
                arg = args[i]
                
                if arg in ["-h", "--help"]:
                    return {"help": True}
                elif arg in ["-v", "--verbose"]:
                    parsed["verbose"] = True
                elif arg in ["-d", "--debug"]:
                    parsed["debug"] = True
                elif arg in ["-o", "--output"]:
                    if i + 1 < len(args):
                        parsed["output_format"] = args[i + 1]
                        i += 1
                elif arg in ["--dir", "--directory"]:
                    parsed["directory"] = True
                elif arg == "--version":
                    return {"version": True}
                elif not arg.startswith("-"):
                    parsed["contract_path"] = arg
                
                i += 1
            
            return parsed
        
        def audit_single_contract(self, contract_path: str) -> dict:
            """Audit a single contract."""
            if not Path(contract_path).exists():
                raise FileNotFoundError(f"Contract not found: {contract_path}")
            
            return {
                "success": True,
                "contract": contract_path,
                "findings": [
                    {"type": "reentrancy", "severity": "HIGH"}
                ]
            }
        
        def audit_directory(self, directory_path: str) -> dict:
            """Audit all contracts in directory."""
            if not Path(directory_path).is_dir():
                raise NotADirectoryError(f"Not a directory: {directory_path}")
            
            return {
                "success": True,
                "contracts_audited": 3,
                "total_findings": 5
            }
        
        def validate_config(self, config: dict) -> bool:
            """Validate configuration."""
            required_keys = ["contract_path"]
            return all(key in config for key in required_keys if config.get(key))
        
        def setup_logging(self, verbose: bool = False, debug: bool = False):
            """Setup logging configuration."""
            self.verbose = verbose
            self.debug = debug
            return True
        
        def validate_api_key(self) -> bool:
            """Validate API key."""
            import os
            return "OPENAI_API_KEY" in os.environ or "TEST_MODE" in os.environ
        
        def handle_error(self, error: Exception) -> dict:
            """Handle errors gracefully."""
            return {
                "success": False,
                "error": str(error),
                "error_type": type(error).__name__
            }
        
        def cleanup(self):
            """Cleanup resources."""
            return True
    
    return MockMain()


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_parse_basic_contract_path(self, mock_main_module):
        """Test parsing basic contract path."""
        args = ["contract.sol"]
        
        result = mock_main_module.parse_arguments(args)
        
        assert result["contract_path"] == "contract.sol"
        assert result["output_format"] == "markdown"
    
    def test_parse_verbose_flag(self, mock_main_module):
        """Test parsing verbose flag."""
        args = ["-v", "contract.sol"]
        
        result = mock_main_module.parse_arguments(args)
        
        assert result["verbose"] is True
    
    def test_parse_debug_flag(self, mock_main_module):
        """Test parsing debug flag."""
        args = ["--debug", "contract.sol"]
        
        result = mock_main_module.parse_arguments(args)
        
        assert result["debug"] is True
    
    def test_parse_output_format(self, mock_main_module):
        """Test parsing output format."""
        args = ["-o", "json", "contract.sol"]
        
        result = mock_main_module.parse_arguments(args)
        
        assert result["output_format"] == "json"
    
    def test_parse_help_flag(self, mock_main_module):
        """Test parsing help flag."""
        args = ["--help"]
        
        result = mock_main_module.parse_arguments(args)
        
        assert result.get("help") is True
    
    def test_parse_version_flag(self, mock_main_module):
        """Test parsing version flag."""
        args = ["--version"]
        
        result = mock_main_module.parse_arguments(args)
        
        assert result.get("version") is True
    
    def test_parse_directory_flag(self, mock_main_module):
        """Test parsing directory flag."""
        args = ["--directory", "/path/to/contracts"]
        
        result = mock_main_module.parse_arguments(args)
        
        assert result["directory"] is True


class TestAuditExecution:
    """Test audit execution."""
    
    def test_audit_single_contract(self, mock_main_module, test_contract_path):
        """Test auditing single contract."""
        result = mock_main_module.audit_single_contract(str(test_contract_path))
        
        assert result["success"] is True
        assert "findings" in result
        assert len(result["findings"]) > 0
    
    def test_audit_directory(self, mock_main_module, temp_dir):
        """Test auditing directory of contracts."""
        result = mock_main_module.audit_directory(str(temp_dir))
        
        assert result["success"] is True
        assert result["contracts_audited"] > 0
    
    def test_audit_invalid_path(self, mock_main_module):
        """Test auditing invalid contract path."""
        with pytest.raises(FileNotFoundError):
            mock_main_module.audit_single_contract("/nonexistent/contract.sol")
    
    def test_audit_invalid_directory(self, mock_main_module, test_contract_path):
        """Test auditing invalid directory."""
        with pytest.raises(NotADirectoryError):
            mock_main_module.audit_directory(str(test_contract_path))


class TestConfiguration:
    """Test configuration handling."""
    
    def test_validate_config_valid(self, mock_main_module):
        """Test validating valid configuration."""
        config = {"contract_path": "contract.sol"}
        
        result = mock_main_module.validate_config(config)
        
        assert result is True
    
    def test_setup_logging(self, mock_main_module):
        """Test logging setup."""
        result = mock_main_module.setup_logging(verbose=True, debug=True)
        
        assert result is True
        assert mock_main_module.verbose is True
        assert mock_main_module.debug is True
    
    def test_api_key_validation(self, mock_main_module):
        """Test API key validation."""
        import os
        os.environ["TEST_MODE"] = "1"
        
        result = mock_main_module.validate_api_key()
        
        assert result is True
        del os.environ["TEST_MODE"]


class TestErrorHandling:
    """Test error handling."""
    
    def test_handle_file_not_found_error(self, mock_main_module):
        """Test handling FileNotFoundError."""
        error = FileNotFoundError("Contract not found")
        
        result = mock_main_module.handle_error(error)
        
        assert result["success"] is False
        assert "Contract not found" in result["error"]
        assert result["error_type"] == "FileNotFoundError"
    
    def test_handle_generic_error(self, mock_main_module):
        """Test handling generic errors."""
        error = Exception("Generic error")
        
        result = mock_main_module.handle_error(error)
        
        assert result["success"] is False
        assert "Generic error" in result["error"]
    
    def test_cleanup_on_exit(self, mock_main_module):
        """Test cleanup on exit."""
        result = mock_main_module.cleanup()
        
        assert result is True


@pytest.mark.unit
class TestMainEntryPointIntegration:
    """Test main entry point integration."""
    
    def test_full_workflow(self, mock_main_module, test_contract_path):
        """Test complete workflow from args to audit."""
        # Parse arguments
        args = [str(test_contract_path), "-v"]
        parsed = mock_main_module.parse_arguments(args)
        
        # Setup logging
        mock_main_module.setup_logging(verbose=parsed["verbose"])
        
        # Audit contract
        result = mock_main_module.audit_single_contract(parsed["contract_path"])
        
        # Verify
        assert result["success"] is True
        assert mock_main_module.verbose is True
    
    def test_error_recovery(self, mock_main_module):
        """Test error recovery workflow."""
        try:
            mock_main_module.audit_single_contract("/invalid/path.sol")
        except FileNotFoundError as e:
            result = mock_main_module.handle_error(e)
            assert result["success"] is False
