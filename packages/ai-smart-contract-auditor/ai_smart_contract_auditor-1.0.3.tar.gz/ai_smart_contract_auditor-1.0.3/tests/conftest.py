"""
Shared pytest fixtures and configuration for all tests.

This file is automatically loaded by pytest and provides fixtures
that are available to all test files.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock

import pytest


# ============================================================================
# Test Environment Setup
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    yield
    os.environ.pop("TESTING", None)
    os.environ.pop("OPENAI_API_KEY", None)


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_contract_path(temp_dir):
    """Create a test Solidity contract file."""
    contract_code = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    contract TestContract {
        mapping(address => uint256) public balances;
        
        function deposit() public payable {
            balances[msg.sender] += msg.value;
        }
        
        function withdraw(uint256 amount) public {
            require(balances[msg.sender] >= amount, "Insufficient balance");
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success, "Transfer failed");
            balances[msg.sender] -= amount;
        }
    }
    """
    contract_path = temp_dir / "TestContract.sol"
    contract_path.write_text(contract_code)
    yield contract_path


@pytest.fixture
def vulnerable_contract_path(temp_dir):
    """Create a vulnerable Solidity contract for testing."""
    contract_code = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    contract VulnerableContract {
        mapping(address => uint256) public balances;
        
        function deposit() public payable {
            balances[msg.sender] += msg.value;
        }
        
        // Vulnerable to reentrancy
        function withdraw(uint256 amount) public {
            require(balances[msg.sender] >= amount);
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success);
            balances[msg.sender] -= amount;  // State update after external call
        }
        
        // Vulnerable to integer overflow (if using old Solidity)
        function unsafeAdd(uint256 a, uint256 b) public pure returns (uint256) {
            return a + b;
        }
    }
    """
    contract_path = temp_dir / "VulnerableContract.sol"
    contract_path.write_text(contract_code)
    yield contract_path


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def sample_vulnerability():
    """Sample vulnerability data for testing."""
    return {
        "type": "reentrancy",
        "severity": "HIGH",
        "function": "withdraw",
        "line": 15,
        "description": "Potential reentrancy vulnerability in withdraw function",
        "recommendation": "Use checks-effects-interactions pattern",
        "confidence": 0.95
    }


@pytest.fixture
def sample_findings():
    """Sample list of vulnerability findings."""
    return [
        {
            "type": "reentrancy",
            "severity": "HIGH",
            "function": "withdraw",
            "line": 15,
            "description": "Reentrancy vulnerability",
            "confidence": 0.95
        },
        {
            "type": "access_control",
            "severity": "MEDIUM",
            "function": "setOwner",
            "line": 25,
            "description": "Missing access control",
            "confidence": 0.85
        },
        {
            "type": "integer_overflow",
            "severity": "LOW",
            "function": "add",
            "line": 35,
            "description": "Potential integer overflow",
            "confidence": 0.70
        }
    ]


@pytest.fixture
def sample_audit_report():
    """Sample complete audit report."""
    return {
        "contract": "TestContract.sol",
        "timestamp": "2025-11-03T12:00:00Z",
        "findings": [
            {
                "id": "VULN-001",
                "type": "reentrancy",
                "severity": "HIGH",
                "function": "withdraw",
                "line": 15,
                "description": "Reentrancy vulnerability detected",
                "recommendation": "Use ReentrancyGuard or checks-effects-interactions",
                "confidence": 0.95,
                "poc_available": True
            }
        ],
        "statistics": {
            "total_findings": 1,
            "high_severity": 1,
            "medium_severity": 0,
            "low_severity": 0
        },
        "risk_score": 8.5
    }


# ============================================================================
# Mock API Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "vulnerabilities": [
                            {
                                "type": "reentrancy",
                                "severity": "HIGH",
                                "description": "Reentrancy vulnerability in withdraw function"
                            }
                        ]
                    })
                }
            }
        ]
    }


@pytest.fixture
def mock_vector_db():
    """Mock vector database for testing."""
    mock_db = Mock()
    mock_db.query.return_value = [
        {
            "id": "vuln-001",
            "type": "reentrancy",
            "severity": "HIGH",
            "description": "Similar reentrancy case",
            "distance": 0.15
        }
    ]
    return mock_db


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_poc_code():
    """Sample PoC code for testing."""
    return """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    import "forge-std/Test.sol";
    import "../VulnerableContract.sol";
    
    contract ReentrancyExploit is Test {
        VulnerableContract target;
        
        function setUp() public {
            target = new VulnerableContract();
        }
        
        function testReentrancy() public {
            // Exploit code here
        }
    }
    """


@pytest.fixture
def sample_fix_suggestion():
    """Sample fix suggestion for testing."""
    return {
        "vulnerability_type": "reentrancy",
        "original_code": "balances[msg.sender] -= amount;",
        "fixed_code": """
        balances[msg.sender] -= amount;  // Move before external call
        (bool success, ) = msg.sender.call{value: amount}("");
        """,
        "explanation": "Move state update before external call to prevent reentrancy",
        "severity_reduction": "HIGH -> NONE"
    }


# ============================================================================
# Tool Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_slither_output():
    """Mock Slither analysis output."""
    return {
        "success": True,
        "results": {
            "detectors": [
                {
                    "check": "reentrancy-eth",
                    "impact": "High",
                    "confidence": "Medium",
                    "description": "Reentrancy in withdraw(uint256)",
                    "elements": [
                        {
                            "type": "function",
                            "name": "withdraw",
                            "source_mapping": {
                                "start": 100,
                                "length": 200,
                                "filename_relative": "TestContract.sol",
                                "lines": [15, 16, 17, 18]
                            }
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def mock_foundry_output():
    """Mock Foundry test output."""
    return {
        "success": True,
        "test_results": [
            {
                "name": "testReentrancy",
                "status": "PASS",
                "gas_used": 50000,
                "logs": ["Reentrancy exploit successful"]
            }
        ]
    }


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def sample_vulnerability_db_entry():
    """Sample vulnerability database entry."""
    return {
        "id": "solodit-001",
        "title": "Reentrancy in withdraw function",
        "severity": "HIGH",
        "protocol": "ExampleDeFi",
        "audit_firm": "Sherlock",
        "description": "The withdraw function is vulnerable to reentrancy attacks...",
        "recommendation": "Implement ReentrancyGuard or use checks-effects-interactions pattern",
        "poc_available": True,
        "poc_code": "// PoC code here",
        "tags": ["reentrancy", "defi", "high-severity"],
        "source": "solodit",
        "url": "https://solodit.xyz/issues/001"
    }


@pytest.fixture
def sample_processed_findings():
    """Sample processed findings data."""
    return {
        "total_findings": 47891,
        "by_severity": {
            "HIGH": 12453,
            "MEDIUM": 18234,
            "LOW": 17204
        },
        "by_type": {
            "reentrancy": 3421,
            "access_control": 5234,
            "integer_overflow": 2134,
            "unchecked_return": 4532
        },
        "sources": {
            "solodit": 25432,
            "sherlock": 15234,
            "code4rena": 7225
        }
    }


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, multiple components)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (slowest, full workflows)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests requiring API keys"
    )
    config.addinivalue_line(
        "markers", "requires_db: Tests requiring database"
    )
    config.addinivalue_line(
        "markers", "requires_tools: Tests requiring external tools"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
pytest_plugins = ['tests.fixtures.generated_fixtures']
