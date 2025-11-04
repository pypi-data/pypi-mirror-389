"""
Tests Using Generated Test Data.

Demonstrates using the automated test data generation fixtures.
"""

import pytest


@pytest.mark.unit
class TestGeneratedContracts:
    """Test using generated contract data."""
    
    def test_sample_contract_structure(self, sample_contract):
        """Test that generated contracts have valid structure."""
        assert isinstance(sample_contract, str)
        assert len(sample_contract) > 0
        assert "pragma solidity" in sample_contract
        assert "contract" in sample_contract
    
    def test_vulnerable_contract_has_vulnerability(self, vulnerable_contract):
        """Test that vulnerable contracts contain vulnerability patterns."""
        assert isinstance(vulnerable_contract, str)
        assert "contract" in vulnerable_contract
        # Should contain reentrancy pattern
        assert "call{value:" in vulnerable_contract or "call()" in vulnerable_contract
    
    def test_contract_metadata_fields(self, contract_metadata):
        """Test that contract metadata has required fields."""
        required_fields = ["name", "version", "compiler", "license", "author", "created_at"]
        for field in required_fields:
            assert field in contract_metadata
            assert contract_metadata[field] is not None


@pytest.mark.unit
class TestGeneratedVulnerabilities:
    """Test using generated vulnerability data."""
    
    def test_vulnerability_structure(self, sample_vulnerability):
        """Test that generated vulnerabilities have valid structure."""
        required_fields = ["type", "severity", "confidence", "description", "line"]
        for field in required_fields:
            assert field in sample_vulnerability
    
    def test_vulnerability_severity(self, sample_vulnerability):
        """Test that vulnerability severity is valid."""
        valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert sample_vulnerability["severity"] in valid_severities
    
    def test_vulnerability_confidence_range(self, sample_vulnerability):
        """Test that confidence is in valid range."""
        assert 0.0 <= sample_vulnerability["confidence"] <= 1.0
    
    def test_multiple_vulnerabilities(self, sample_vulnerabilities):
        """Test generating multiple vulnerabilities."""
        assert isinstance(sample_vulnerabilities, list)
        assert len(sample_vulnerabilities) == 5
        assert all("severity" in v for v in sample_vulnerabilities)
    
    def test_critical_vulnerability_severity(self, critical_vulnerability):
        """Test that critical vulnerability has correct severity."""
        assert critical_vulnerability["severity"] == "CRITICAL"


@pytest.mark.unit
class TestGeneratedPoCs:
    """Test using generated PoC data."""
    
    def test_poc_structure(self, sample_poc):
        """Test that generated PoCs have valid structure."""
        required_fields = ["id", "vulnerability_type", "title", "code", "steps", "impact"]
        for field in required_fields:
            assert field in sample_poc
    
    def test_poc_code_validity(self, sample_poc):
        """Test that PoC code is valid Solidity."""
        assert isinstance(sample_poc["code"], str)
        assert len(sample_poc["code"]) > 0
        assert "contract" in sample_poc["code"]
    
    def test_poc_steps(self, sample_poc):
        """Test that PoC has exploitation steps."""
        assert isinstance(sample_poc["steps"], list)
        assert len(sample_poc["steps"]) > 0


@pytest.mark.unit
class TestGeneratedFixes:
    """Test using generated fix suggestion data."""
    
    def test_fix_structure(self, sample_fix):
        """Test that generated fixes have valid structure."""
        required_fields = ["id", "vulnerability_type", "original_code", "fixed_code", "explanation"]
        for field in required_fields:
            assert field in sample_fix
    
    def test_fix_confidence(self, sample_fix):
        """Test that fix confidence is in valid range."""
        assert 0.0 <= sample_fix["confidence"] <= 1.0


@pytest.mark.unit
class TestGeneratedReports:
    """Test using generated report data."""
    
    def test_report_structure(self, sample_report):
        """Test that generated reports have valid structure."""
        required_fields = ["id", "title", "contract", "auditor", "summary", "findings"]
        for field in required_fields:
            assert field in sample_report
    
    def test_report_summary(self, sample_report):
        """Test that report summary is accurate."""
        summary = sample_report["summary"]
        findings = sample_report["findings"]
        
        # Count should match
        assert summary["total_findings"] == len(findings)
        
        # Severity counts should sum to total
        total = summary["critical"] + summary["high"] + summary["medium"] + summary["low"]
        assert total == summary["total_findings"]
    
    def test_report_findings(self, sample_report):
        """Test that report findings are valid."""
        findings = sample_report["findings"]
        assert isinstance(findings, list)
        assert all("severity" in f for f in findings)


@pytest.mark.unit
class TestBatchGeneration:
    """Test batch data generation."""
    
    def test_batch_contracts(self, batch_contracts):
        """Test generating batch of contracts."""
        assert isinstance(batch_contracts, list)
        assert len(batch_contracts) == 10
        assert all("code" in c and "metadata" in c for c in batch_contracts)
    
    def test_batch_vulnerabilities(self, batch_vulnerabilities):
        """Test generating batch of vulnerabilities."""
        assert isinstance(batch_vulnerabilities, list)
        assert len(batch_vulnerabilities) == 50
        assert all("severity" in v for v in batch_vulnerabilities)


@pytest.mark.unit
class TestTestSuiteData:
    """Test complete test suite data generation."""
    
    def test_test_suite_completeness(self, test_suite_data):
        """Test that test suite has all components."""
        required_keys = ["contracts", "vulnerabilities", "pocs", "fixes", "reports"]
        for key in required_keys:
            assert key in test_suite_data
            assert isinstance(test_suite_data[key], list)
            assert len(test_suite_data[key]) > 0


@pytest.mark.unit
class TestEdgeCaseData:
    """Test edge case data generation."""
    
    def test_edge_case_completeness(self, edge_case_data):
        """Test that edge cases are generated."""
        required_keys = [
            "empty_contract", "minimal_contract", "large_contract",
            "unicode_contract", "special_chars",
            "no_vulnerabilities", "single_vulnerability", "many_vulnerabilities"
        ]
        for key in required_keys:
            assert key in edge_case_data
    
    def test_empty_contract(self, edge_case_data):
        """Test empty contract edge case."""
        assert edge_case_data["empty_contract"] == ""
    
    def test_minimal_contract(self, edge_case_data):
        """Test minimal contract edge case."""
        assert "contract" in edge_case_data["minimal_contract"]
        assert len(edge_case_data["minimal_contract"]) < 20
    
    def test_large_contract(self, edge_case_data):
        """Test large contract edge case."""
        assert len(edge_case_data["large_contract"]) > 1000
    
    def test_unicode_contract(self, edge_case_data):
        """Test unicode contract edge case."""
        assert "测试" in edge_case_data["unicode_contract"]
    
    def test_no_vulnerabilities(self, edge_case_data):
        """Test no vulnerabilities edge case."""
        assert edge_case_data["no_vulnerabilities"] == []
    
    def test_single_vulnerability(self, edge_case_data):
        """Test single vulnerability edge case."""
        assert len(edge_case_data["single_vulnerability"]) == 1
    
    def test_many_vulnerabilities(self, edge_case_data):
        """Test many vulnerabilities edge case."""
        assert len(edge_case_data["many_vulnerabilities"]) == 100
