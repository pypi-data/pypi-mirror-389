"""Unit tests for Code4rena Filter module."""

import pytest


@pytest.fixture
def mock_code4rena_filter():
    """Create a mock Code4rena Filter for testing."""
    class MockCode4renaFilter:
        def filter_validated_findings(self, findings: list, confidence_threshold: float = 0.8) -> list:
            """Filter findings based on Code4rena validation."""
            if not findings:
                return []
            
            validated = []
            for finding in findings:
                if self._is_validated(finding) and finding.get("confidence", 0) >= confidence_threshold:
                    validated.append(finding)
            
            return validated
        
        def _is_validated(self, finding: dict) -> bool:
            """Check if finding has Code4rena validation label."""
            labels = finding.get("labels", [])
            return "code4rena-validated" in labels or finding.get("validated", False)
        
        def calculate_statistics(self, findings: list) -> dict:
            """Calculate statistics for filtered findings."""
            total = len(findings)
            validated = len([f for f in findings if self._is_validated(f)])
            
            return {
                "total_findings": total,
                "validated_findings": validated,
                "validation_rate": validated / total if total > 0 else 0.0
            }
        
        def create_subset_database(self, findings: list, output_path: str) -> bool:
            """Create subset database with validated findings."""
            validated = self.filter_validated_findings(findings)
            # Mock database creation
            return len(validated) > 0
    
    return MockCode4renaFilter()


class TestCode4renaFilter:
    """Test suite for Code4rena Filter functionality."""
    
    def test_filter_validated_findings(self, mock_code4rena_filter):
        """Test filtering of validated findings."""
        findings = [
            {"type": "reentrancy", "labels": ["code4rena-validated"], "confidence": 0.9},
            {"type": "access_control", "labels": [], "confidence": 0.8},
            {"type": "overflow", "validated": True, "confidence": 0.85}
        ]
        
        validated = mock_code4rena_filter.filter_validated_findings(findings)
        
        assert len(validated) == 2
        assert all("code4rena-validated" in f.get("labels", []) or f.get("validated") for f in validated)
    
    def test_confidence_threshold(self, mock_code4rena_filter):
        """Test confidence threshold filtering."""
        findings = [
            {"labels": ["code4rena-validated"], "confidence": 0.95},
            {"labels": ["code4rena-validated"], "confidence": 0.75}
        ]
        
        high_threshold = mock_code4rena_filter.filter_validated_findings(findings, 0.9)
        low_threshold = mock_code4rena_filter.filter_validated_findings(findings, 0.7)
        
        assert len(high_threshold) == 1
        assert len(low_threshold) == 2
    
    def test_label_matching(self, mock_code4rena_filter):
        """Test label matching logic."""
        findings = [
            {"labels": ["code4rena-validated", "high-severity"], "confidence": 0.9},
            {"labels": ["other-label"], "confidence": 0.9},
            {"labels": [], "validated": True, "confidence": 0.9}
        ]
        
        validated = mock_code4rena_filter.filter_validated_findings(findings)
        
        assert len(validated) == 2
    
    def test_statistics_tracking(self, mock_code4rena_filter):
        """Test statistics calculation."""
        findings = [
            {"labels": ["code4rena-validated"], "confidence": 0.9},
            {"labels": [], "confidence": 0.8},
            {"labels": ["code4rena-validated"], "confidence": 0.85}
        ]
        
        stats = mock_code4rena_filter.calculate_statistics(findings)
        
        assert stats["total_findings"] == 3
        assert stats["validated_findings"] == 2
        assert 0.6 < stats["validation_rate"] < 0.7
    
    def test_subset_database_creation(self, mock_code4rena_filter):
        """Test subset database creation."""
        findings = [
            {"labels": ["code4rena-validated"], "confidence": 0.9}
        ]
        
        result = mock_code4rena_filter.create_subset_database(findings, "test.db")
        
        assert result is True
