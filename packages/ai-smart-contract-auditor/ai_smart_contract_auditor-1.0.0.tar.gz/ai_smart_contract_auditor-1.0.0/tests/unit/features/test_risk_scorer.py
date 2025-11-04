"""Unit tests for Risk Scorer module."""

import pytest


@pytest.fixture
def mock_risk_scorer():
    """Create a mock Risk Scorer for testing."""
    class MockRiskScorer:
        SEVERITY_WEIGHTS = {"HIGH": 10, "MEDIUM": 5, "LOW": 2, "INFO": 1}
        
        def calculate_risk_score(self, findings: list) -> float:
            """Calculate overall risk score from findings."""
            if not findings:
                return 0.0
            
            total_score = 0.0
            for finding in findings:
                severity = finding.get("severity", "LOW")
                confidence = finding.get("confidence", 0.5)
                weight = self.SEVERITY_WEIGHTS.get(severity, 1)
                total_score += weight * confidence
            
            # Normalize to 0-10 scale
            max_possible = len(findings) * 10
            normalized = (total_score / max_possible) * 10 if max_possible > 0 else 0
            return min(10.0, max(0.0, normalized))
        
        def categorize_risk(self, risk_score: float) -> str:
            """Categorize risk level based on score."""
            if risk_score >= 8.0:
                return "CRITICAL"
            elif risk_score >= 6.0:
                return "HIGH"
            elif risk_score >= 4.0:
                return "MEDIUM"
            elif risk_score >= 2.0:
                return "LOW"
            else:
                return "MINIMAL"
    
    return MockRiskScorer()


class TestRiskScorer:
    """Test suite for Risk Scorer functionality."""
    
    def test_calculate_risk_score(self, mock_risk_scorer, sample_findings):
        """Test basic risk score calculation."""
        score = mock_risk_scorer.calculate_risk_score(sample_findings)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0
    
    def test_severity_weighting(self, mock_risk_scorer):
        """Test that severity affects risk score."""
        high_severity = [{"severity": "HIGH", "confidence": 1.0}]
        low_severity = [{"severity": "LOW", "confidence": 1.0}]
        
        high_score = mock_risk_scorer.calculate_risk_score(high_severity)
        low_score = mock_risk_scorer.calculate_risk_score(low_severity)
        
        assert high_score > low_score
    
    def test_confidence_adjustment(self, mock_risk_scorer):
        """Test that confidence affects risk score."""
        high_conf = [{"severity": "HIGH", "confidence": 0.95}]
        low_conf = [{"severity": "HIGH", "confidence": 0.50}]
        
        high_score = mock_risk_scorer.calculate_risk_score(high_conf)
        low_score = mock_risk_scorer.calculate_risk_score(low_conf)
        
        assert high_score > low_score
    
    def test_multiple_vulnerabilities_score(self, mock_risk_scorer):
        """Test score with multiple vulnerabilities."""
        findings = [
            {"severity": "HIGH", "confidence": 0.9},
            {"severity": "MEDIUM", "confidence": 0.8},
            {"severity": "LOW", "confidence": 0.7}
        ]
        
        score = mock_risk_scorer.calculate_risk_score(findings)
        assert 0.0 < score <= 10.0
    
    def test_risk_score_bounds(self, mock_risk_scorer):
        """Test that risk score stays within bounds."""
        many_high = [{"severity": "HIGH", "confidence": 1.0} for _ in range(100)]
        
        score = mock_risk_scorer.calculate_risk_score(many_high)
        assert score <= 10.0
    
    def test_risk_categorization(self, mock_risk_scorer):
        """Test risk level categorization."""
        assert mock_risk_scorer.categorize_risk(9.0) == "CRITICAL"
        assert mock_risk_scorer.categorize_risk(7.0) == "HIGH"
        assert mock_risk_scorer.categorize_risk(5.0) == "MEDIUM"
        assert mock_risk_scorer.categorize_risk(3.0) == "LOW"
        assert mock_risk_scorer.categorize_risk(1.0) == "MINIMAL"
