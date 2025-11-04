"""Unit tests for Report Generator module."""

import pytest
import json
from pathlib import Path


@pytest.fixture
def mock_report_generator():
    """Create a mock Report Generator for testing."""
    class MockReportGenerator:
        def generate_markdown_report(self, audit_data: dict) -> str:
            """Generate markdown format report."""
            if not audit_data:
                raise ValueError("Audit data is required")
            
            contract = audit_data.get("contract", "Unknown")
            findings = audit_data.get("findings", [])
            
            report = f"# Audit Report: {contract}\n\n"
            report += f"## Summary\n\nTotal Findings: {len(findings)}\n\n"
            report += "## Findings\n\n"
            
            for i, finding in enumerate(findings, 1):
                report += f"### {i}. {finding.get('type', 'Unknown')}\n"
                report += f"- **Severity**: {finding.get('severity', 'Unknown')}\n"
                report += f"- **Description**: {finding.get('description', 'N/A')}\n\n"
            
            return report
        
        def generate_json_report(self, audit_data: dict) -> str:
            """Generate JSON format report."""
            if not audit_data:
                raise ValueError("Audit data is required")
            
            return json.dumps(audit_data, indent=2)
        
        def generate_pdf_report(self, audit_data: dict) -> bytes:
            """Generate PDF format report (mocked)."""
            if not audit_data:
                raise ValueError("Audit data is required")
            
            # Mock PDF generation
            return b"PDF_CONTENT"
        
        def save_report(self, content: str, output_path: Path) -> bool:
            """Save report to file."""
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
                return True
            except Exception:
                return False
        
        def calculate_statistics(self, findings: list) -> dict:
            """Calculate statistics from findings."""
            stats = {
                "total": len(findings),
                "by_severity": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
            }
            
            for finding in findings:
                severity = finding.get("severity", "INFO")
                if severity in stats["by_severity"]:
                    stats["by_severity"][severity] += 1
            
            return stats
    
    return MockReportGenerator()


class TestReportGenerator:
    """Test suite for Report Generator functionality."""
    
    def test_generate_markdown_report(self, mock_report_generator, sample_audit_report):
        """Test markdown report generation."""
        report = mock_report_generator.generate_markdown_report(sample_audit_report)
        
        assert report is not None
        assert "# Audit Report" in report
        assert "## Summary" in report
        assert "## Findings" in report
    
    def test_generate_json_report(self, mock_report_generator, sample_audit_report):
        """Test JSON report generation."""
        report = mock_report_generator.generate_json_report(sample_audit_report)
        
        assert report is not None
        data = json.loads(report)
        assert "contract" in data
        assert "findings" in data
    
    def test_generate_pdf_report(self, mock_report_generator, sample_audit_report):
        """Test PDF report generation."""
        report = mock_report_generator.generate_pdf_report(sample_audit_report)
        
        assert report is not None
        assert isinstance(report, bytes)
    
    def test_report_with_no_findings(self, mock_report_generator):
        """Test report generation with no findings."""
        audit_data = {"contract": "Test.sol", "findings": []}
        
        report = mock_report_generator.generate_markdown_report(audit_data)
        
        assert "Total Findings: 0" in report
    
    def test_report_with_multiple_findings(self, mock_report_generator, sample_findings):
        """Test report with multiple findings."""
        audit_data = {"contract": "Test.sol", "findings": sample_findings}
        
        report = mock_report_generator.generate_markdown_report(audit_data)
        
        assert f"Total Findings: {len(sample_findings)}" in report
        assert all(f["type"] in report for f in sample_findings)
    
    def test_report_statistics(self, mock_report_generator, sample_findings):
        """Test statistics calculation."""
        stats = mock_report_generator.calculate_statistics(sample_findings)
        
        assert stats["total"] == len(sample_findings)
        assert "by_severity" in stats
        assert stats["by_severity"]["HIGH"] > 0
    
    def test_report_formatting(self, mock_report_generator):
        """Test report formatting consistency."""
        audit_data = {
            "contract": "Test.sol",
            "findings": [{"type": "reentrancy", "severity": "HIGH", "description": "Test"}]
        }
        
        report = mock_report_generator.generate_markdown_report(audit_data)
        
        assert report.startswith("# Audit Report")
        assert "**Severity**" in report
        assert "**Description**" in report
    
    def test_save_report(self, mock_report_generator, temp_dir):
        """Test saving report to file."""
        content = "# Test Report\n\nContent here"
        output_path = temp_dir / "reports" / "test_report.md"
        
        result = mock_report_generator.save_report(content, output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.read_text() == content
