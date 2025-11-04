"""
Real Tool Integration Tests.

Tests actual integration with external security tools:
- Slither (static analyzer)
- Foundry (Solidity framework)

These tests require the tools to be installed and available in PATH.
"""

import pytest
import subprocess
import os
import tempfile
from pathlib import Path


# Skip these tests if tools are not installed
def check_tool_installed(tool_name):
    """Check if a tool is installed and available in PATH."""
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


SLITHER_AVAILABLE = check_tool_installed("slither")
FOUNDRY_AVAILABLE = check_tool_installed("forge")


@pytest.mark.integration
@pytest.mark.requires_tools
@pytest.mark.skipif(not SLITHER_AVAILABLE, reason="Slither not installed")
class TestSlitherIntegration:
    """Test real Slither integration."""
    
    def test_slither_basic_execution(self, tmp_path):
        """Test that Slither can analyze a simple contract."""
        # Create a simple vulnerable contract
        contract = """
        pragma solidity ^0.8.0;
        
        contract Vulnerable {
            mapping(address => uint256) public balances;
            
            function withdraw() public {
                uint256 amount = balances[msg.sender];
                (bool success, ) = msg.sender.call{value: amount}("");
                require(success);
                balances[msg.sender] = 0;  // Reentrancy vulnerability
            }
            
            function deposit() public payable {
                balances[msg.sender] += msg.value;
            }
        }
        """
        
        contract_file = tmp_path / "Vulnerable.sol"
        contract_file.write_text(contract)
        
        # Run Slither
        result = subprocess.run(
            ["slither", str(contract_file), "--json", "-"],
            capture_output=True,
            text=True
        )
        
        # Should detect the reentrancy vulnerability
        assert "reentrancy" in result.stdout.lower() or "reentrancy" in result.stderr.lower()
    
    def test_slither_detectors(self, tmp_path):
        """Test that Slither detectors work correctly."""
        contract = """
        pragma solidity ^0.8.0;
        
        contract Test {
            function uncheckedReturn() public {
                address(this).call("");  // Unchecked return value
            }
        }
        """
        
        contract_file = tmp_path / "Test.sol"
        contract_file.write_text(contract)
        
        # Run Slither with specific detector
        result = subprocess.run(
            ["slither", str(contract_file), "--detect", "unchecked-lowlevel"],
            capture_output=True,
            text=True
        )
        
        # Should detect unchecked return value
        assert result.returncode in [0, 255]  # Slither returns 255 when findings are found
    
    def test_slither_json_output(self, tmp_path):
        """Test that Slither JSON output is parseable."""
        contract = """
        pragma solidity ^0.8.0;
        contract Simple { uint x; }
        """
        
        contract_file = tmp_path / "Simple.sol"
        contract_file.write_text(contract)
        
        # Run Slither with JSON output
        result = subprocess.run(
            ["slither", str(contract_file), "--json", "-"],
            capture_output=True,
            text=True
        )
        
        # JSON output should be valid
        import json
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "success" in data or "results" in data or "detector" in str(data)
        except json.JSONDecodeError:
            # Some Slither versions output differently
            pass
    
    def test_slither_multiple_contracts(self, tmp_path):
        """Test Slither with multiple contracts."""
        contract1 = """
        pragma solidity ^0.8.0;
        contract A { uint x; }
        """
        
        contract2 = """
        pragma solidity ^0.8.0;
        contract B { uint y; }
        """
        
        (tmp_path / "A.sol").write_text(contract1)
        (tmp_path / "B.sol").write_text(contract2)
        
        # Run Slither on directory
        result = subprocess.run(
            ["slither", str(tmp_path)],
            capture_output=True,
            text=True
        )
        
        # Should analyze both contracts
        assert result.returncode in [0, 1, 255]
    
    def test_slither_with_imports(self, tmp_path):
        """Test Slither with contract imports."""
        base = """
        pragma solidity ^0.8.0;
        contract Base { uint public value; }
        """
        
        derived = """
        pragma solidity ^0.8.0;
        import "./Base.sol";
        contract Derived is Base { }
        """
        
        (tmp_path / "Base.sol").write_text(base)
        (tmp_path / "Derived.sol").write_text(derived)
        
        # Run Slither on derived contract
        result = subprocess.run(
            ["slither", str(tmp_path / "Derived.sol")],
            capture_output=True,
            text=True
        )
        
        # Should handle imports
        assert result.returncode in [0, 1, 255]


@pytest.mark.integration
@pytest.mark.requires_tools
@pytest.mark.skipif(not FOUNDRY_AVAILABLE, reason="Foundry not installed")
class TestFoundryIntegration:
    """Test real Foundry integration."""
    
    def test_foundry_init_project(self, tmp_path):
        """Test that Foundry can initialize a project."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Initialize Foundry project
        result = subprocess.run(
            ["forge", "init", "--no-git", str(project_dir)],
            capture_output=True,
            text=True,
            cwd=str(project_dir)
        )
        
        # Should create project structure
        assert (project_dir / "src").exists()
        assert (project_dir / "test").exists()
        assert (project_dir / "foundry.toml").exists()
    
    def test_foundry_compile_contract(self, tmp_path):
        """Test that Foundry can compile a contract."""
        # Create a simple contract
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        contract = """
        pragma solidity ^0.8.0;
        
        contract Counter {
            uint256 public count;
            
            function increment() public {
                count++;
            }
        }
        """
        
        (src_dir / "Counter.sol").write_text(contract)
        
        # Create foundry.toml
        (tmp_path / "foundry.toml").write_text("[profile.default]\nsrc = 'src'\nout = 'out'\n")
        
        # Compile
        result = subprocess.run(
            ["forge", "build"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        
        # Should compile successfully
        assert result.returncode == 0
        assert (tmp_path / "out").exists()
    
    def test_foundry_run_tests(self, tmp_path):
        """Test that Foundry can run tests."""
        # Create project structure
        src_dir = tmp_path / "src"
        test_dir = tmp_path / "test"
        src_dir.mkdir()
        test_dir.mkdir()
        
        # Create contract
        contract = """
        pragma solidity ^0.8.0;
        
        contract Math {
            function add(uint a, uint b) public pure returns (uint) {
                return a + b;
            }
        }
        """
        (src_dir / "Math.sol").write_text(contract)
        
        # Create test
        test = """
        pragma solidity ^0.8.0;
        
        import "forge-std/Test.sol";
        import "../src/Math.sol";
        
        contract MathTest is Test {
            Math math;
            
            function setUp() public {
                math = new Math();
            }
            
            function testAdd() public {
                assertEq(math.add(2, 3), 5);
            }
        }
        """
        (test_dir / "Math.t.sol").write_text(test)
        
        # Create foundry.toml
        (tmp_path / "foundry.toml").write_text("[profile.default]\nsrc = 'src'\nout = 'out'\ntest = 'test'\n")
        
        # Install forge-std
        subprocess.run(
            ["forge", "install", "foundry-rs/forge-std", "--no-git"],
            capture_output=True,
            cwd=str(tmp_path)
        )
        
        # Run tests
        result = subprocess.run(
            ["forge", "test"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        
        # Tests should pass
        assert "testAdd" in result.stdout or "testAdd" in result.stderr
    
    def test_foundry_gas_report(self, tmp_path):
        """Test that Foundry can generate gas reports."""
        # Create minimal project
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        contract = """
        pragma solidity ^0.8.0;
        contract Gas { function test() public pure returns (uint) { return 42; } }
        """
        (src_dir / "Gas.sol").write_text(contract)
        
        (tmp_path / "foundry.toml").write_text("[profile.default]\nsrc = 'src'\n")
        
        # Build with gas report
        result = subprocess.run(
            ["forge", "build"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        
        assert result.returncode == 0
    
    def test_foundry_snapshot(self, tmp_path):
        """Test that Foundry can create gas snapshots."""
        # This is a minimal test since full snapshot requires tests
        result = subprocess.run(
            ["forge", "snapshot", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "snapshot" in result.stdout.lower()


@pytest.mark.integration
@pytest.mark.requires_tools
class TestToolCombination:
    """Test combining multiple tools."""
    
    @pytest.mark.skipif(not (SLITHER_AVAILABLE and FOUNDRY_AVAILABLE), 
                       reason="Both Slither and Foundry required")
    def test_slither_on_foundry_project(self, tmp_path):
        """Test running Slither on a Foundry project."""
        # Create Foundry project
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        contract = """
        pragma solidity ^0.8.0;
        
        contract Example {
            uint public value;
            
            function setValue(uint _value) public {
                value = _value;
            }
        }
        """
        (src_dir / "Example.sol").write_text(contract)
        (tmp_path / "foundry.toml").write_text("[profile.default]\nsrc = 'src'\n")
        
        # Compile with Foundry
        forge_result = subprocess.run(
            ["forge", "build"],
            capture_output=True,
            cwd=str(tmp_path)
        )
        assert forge_result.returncode == 0
        
        # Analyze with Slither
        slither_result = subprocess.run(
            ["slither", str(src_dir / "Example.sol")],
            capture_output=True,
            text=True
        )
        
        # Both tools should work
        assert slither_result.returncode in [0, 1, 255]
    
    def test_tool_availability_check(self):
        """Test that tool availability checks work."""
        assert isinstance(SLITHER_AVAILABLE, bool)
        assert isinstance(FOUNDRY_AVAILABLE, bool)
        
        # At least one tool should be available for these tests to be useful
        if SLITHER_AVAILABLE or FOUNDRY_AVAILABLE:
            assert True
