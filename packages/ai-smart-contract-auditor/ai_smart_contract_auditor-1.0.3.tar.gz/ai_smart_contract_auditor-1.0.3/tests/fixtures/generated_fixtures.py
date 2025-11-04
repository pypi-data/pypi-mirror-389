"""
Generated Test Fixtures.

Pytest fixtures that use the data generator to create test data.
"""

import pytest
from .data_generator import TestDataGenerator


@pytest.fixture
def data_generator():
    """Provide a test data generator instance."""
    return TestDataGenerator(seed=42)  # Reproducible


@pytest.fixture
def sample_contract(data_generator):
    """Generate a sample contract."""
    return data_generator.generate_contract_code()


@pytest.fixture
def vulnerable_contract(data_generator):
    """Generate a contract with reentrancy vulnerability."""
    return data_generator.generate_contract_code("reentrancy")


@pytest.fixture
def contract_metadata(data_generator):
    """Generate contract metadata."""
    return data_generator.generate_contract_metadata()


@pytest.fixture
def sample_vulnerability(data_generator):
    """Generate a single vulnerability."""
    return data_generator.generate_vulnerability()


@pytest.fixture
def sample_vulnerabilities(data_generator):
    """Generate multiple vulnerabilities."""
    return data_generator.generate_vulnerabilities(count=5)


@pytest.fixture
def critical_vulnerability(data_generator):
    """Generate a critical severity vulnerability."""
    return data_generator.generate_vulnerability(severity="CRITICAL")


@pytest.fixture
def sample_poc(data_generator):
    """Generate a sample PoC."""
    return data_generator.generate_poc("reentrancy")


@pytest.fixture
def sample_fix(data_generator):
    """Generate a sample fix suggestion."""
    return data_generator.generate_fix_suggestion("reentrancy")


@pytest.fixture
def sample_report(data_generator):
    """Generate a sample audit report."""
    return data_generator.generate_audit_report(num_findings=10)


@pytest.fixture
def batch_contracts(data_generator):
    """Generate a batch of contracts."""
    return data_generator.generate_batch_contracts(count=10)


@pytest.fixture
def batch_vulnerabilities(data_generator):
    """Generate a batch of vulnerabilities."""
    return data_generator.generate_batch_vulnerabilities(count=50)


@pytest.fixture
def test_suite_data(data_generator):
    """Generate complete test suite data."""
    return data_generator.generate_test_suite_data()


@pytest.fixture
def edge_case_data(data_generator):
    """Generate edge case test data."""
    return data_generator.generate_edge_case_data()
