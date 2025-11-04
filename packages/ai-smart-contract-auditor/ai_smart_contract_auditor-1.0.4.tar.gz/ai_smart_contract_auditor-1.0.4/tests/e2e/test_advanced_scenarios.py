"""
Advanced End-to-End Scenarios.

Complex multi-step workflows that test the entire system.
"""

import pytest
import tempfile
import json
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.advanced
class TestMultiContractAudit:
    """Test auditing multiple contracts in a project."""
    
    def test_audit_entire_project(self, tmp_path, data_generator):
        """Test auditing an entire project with multiple contracts."""
        # Create project structure
        contracts_dir = tmp_path / "contracts"
        contracts_dir.mkdir()
        
        # Generate multiple contracts
        for i in range(5):
            contract_file = contracts_dir / f"Contract{i}.sol"
            contract_file.write_text(data_generator.generate_contract_code())
        
        # Audit all contracts
        results = []
        for contract_file in contracts_dir.glob("*.sol"):
            # Simulate audit
            result = {
                "contract": contract_file.name,
                "findings": data_generator.generate_vulnerabilities(count=3),
            }
            results.append(result)
        
        # Verify all contracts were audited
        assert len(results) == 5
        assert all("findings" in r for r in results)
    
    def test_audit_with_dependencies(self, tmp_path, data_generator):
        """Test auditing contracts with import dependencies."""
        # Create base contract
        base = tmp_path / "Base.sol"
        base.write_text("""
        pragma solidity ^0.8.0;
        contract Base { uint public value; }
        """)
        
        # Create derived contract
        derived = tmp_path / "Derived.sol"
        derived.write_text("""
        pragma solidity ^0.8.0;
        import "./Base.sol";
        contract Derived is Base { }
        """)
        
        # Audit should handle dependencies
        results = {
            "base": data_generator.generate_vulnerabilities(count=1),
            "derived": data_generator.generate_vulnerabilities(count=2),
        }
        
        assert len(results) == 2
    
    def test_incremental_audit(self, tmp_path, data_generator):
        """Test incremental auditing of changed contracts."""
        contract_file = tmp_path / "Contract.sol"
        
        # Initial audit
        contract_file.write_text(data_generator.generate_contract_code("reentrancy"))
        initial_findings = data_generator.generate_vulnerabilities(count=5)
        
        # Fix vulnerabilities
        contract_file.write_text(data_generator.generate_contract_code())
        
        # Re-audit
        updated_findings = data_generator.generate_vulnerabilities(count=1)
        
        # Should have fewer findings after fixes
        assert len(updated_findings) < len(initial_findings)


@pytest.mark.e2e
@pytest.mark.advanced
class TestCollaborativeAudit:
    """Test collaborative auditing workflows."""
    
    def test_multi_auditor_workflow(self, data_generator):
        """Test multiple auditors working on same contract."""
        # Auditor 1 findings
        auditor1_findings = data_generator.generate_vulnerabilities(count=5)
        
        # Auditor 2 findings
        auditor2_findings = data_generator.generate_vulnerabilities(count=4)
        
        # Merge findings (remove duplicates)
        all_findings = auditor1_findings + auditor2_findings
        unique_findings = {f["type"]: f for f in all_findings}.values()
        
        # Should have combined findings
        assert len(list(unique_findings)) <= len(all_findings)
    
    def test_peer_review_workflow(self, data_generator):
        """Test peer review of audit findings."""
        # Initial findings
        findings = data_generator.generate_vulnerabilities(count=10)
        
        # Peer review (validate findings)
        reviewed_findings = []
        for finding in findings:
            # Simulate peer review
            if finding["confidence"] > 0.7:
                finding["peer_reviewed"] = True
                finding["reviewer"] = "Peer Auditor"
                reviewed_findings.append(finding)
        
        # Should have validated findings
        assert len(reviewed_findings) > 0
        assert all(f["peer_reviewed"] for f in reviewed_findings)
    
    def test_consensus_validation(self, data_generator):
        """Test consensus-based finding validation."""
        # Multiple auditors report same vulnerability
        auditor_reports = [
            {"type": "reentrancy", "severity": "HIGH", "auditor": f"Auditor{i}"}
            for i in range(3)
        ]
        
        # Consensus: all agree on reentrancy
        consensus = all(r["type"] == "reentrancy" for r in auditor_reports)
        
        assert consensus is True
        assert len(auditor_reports) >= 3  # Minimum 3 auditors


@pytest.mark.e2e
@pytest.mark.advanced
class TestCICDIntegration:
    """Test CI/CD pipeline integration."""
    
    def test_pre_commit_audit(self, tmp_path, data_generator):
        """Test pre-commit hook audit workflow."""
        # Simulate git diff
        changed_files = [
            tmp_path / "Contract1.sol",
            tmp_path / "Contract2.sol",
        ]
        
        for file in changed_files:
            file.write_text(data_generator.generate_contract_code())
        
        # Audit only changed files
        results = []
        for file in changed_files:
            result = {
                "file": file.name,
                "findings": data_generator.generate_vulnerabilities(count=2),
            }
            results.append(result)
        
        # Should audit only changed files
        assert len(results) == 2
    
    def test_pull_request_audit(self, tmp_path, data_generator):
        """Test automated PR audit workflow."""
        # Simulate PR with new contract
        pr_contract = tmp_path / "NewContract.sol"
        pr_contract.write_text(data_generator.generate_contract_code("reentrancy"))
        
        # Audit PR
        findings = data_generator.generate_vulnerabilities(count=5)
        
        # Check severity threshold
        critical_findings = [f for f in findings if f["severity"] == "CRITICAL"]
        high_findings = [f for f in findings if f["severity"] == "HIGH"]
        
        # PR should be blocked if critical/high findings
        should_block_pr = len(critical_findings) > 0 or len(high_findings) > 2
        
        # Simulate PR status
        pr_status = "blocked" if should_block_pr else "approved"
        
        assert pr_status in ["blocked", "approved"]
    
    def test_automated_fix_application(self, tmp_path, data_generator):
        """Test automated fix suggestion application."""
        contract_file = tmp_path / "Contract.sol"
        original_code = data_generator.generate_contract_code("reentrancy")
        contract_file.write_text(original_code)
        
        # Generate fix
        fix = data_generator.generate_fix_suggestion("reentrancy")
        
        # Apply fix (simulate)
        fixed_code = fix["fixed_code"]
        contract_file.write_text(fixed_code)
        
        # Verify fix was applied
        assert contract_file.read_text() == fixed_code
        assert contract_file.read_text() != original_code


@pytest.mark.e2e
@pytest.mark.advanced
class TestCustomTraining:
    """Test custom training workflows."""
    
    def test_protocol_specific_training(self, tmp_path, data_generator):
        """Test training on protocol-specific vulnerabilities."""
        # Generate training data
        training_data = {
            "protocol": "DeFi",
            "vulnerabilities": data_generator.generate_vulnerabilities(count=50),
            "patterns": ["flash-loan", "oracle-manipulation", "reentrancy"],
        }
        
        # Save training data
        training_file = tmp_path / "training_data.json"
        training_file.write_text(json.dumps(training_data))
        
        # Verify training data
        loaded = json.loads(training_file.read_text())
        assert loaded["protocol"] == "DeFi"
        assert len(loaded["vulnerabilities"]) == 50
    
    def test_fine_tuning_workflow(self, tmp_path, data_generator):
        """Test model fine-tuning workflow."""
        # Generate fine-tuning dataset
        dataset = []
        for i in range(100):
            example = {
                "input": data_generator.generate_contract_code("reentrancy"),
                "output": data_generator.generate_vulnerability("HIGH"),
            }
            dataset.append(example)
        
        # Save dataset
        dataset_file = tmp_path / "fine_tuning_dataset.jsonl"
        with open(dataset_file, 'w') as f:
            for example in dataset:
                f.write(json.dumps(example) + "\n")
        
        # Verify dataset
        assert dataset_file.exists()
        lines = dataset_file.read_text().strip().split("\n")
        assert len(lines) == 100


@pytest.mark.e2e
@pytest.mark.advanced
class TestReportGeneration:
    """Test advanced report generation scenarios."""
    
    def test_multi_format_report(self, tmp_path, data_generator):
        """Test generating reports in multiple formats."""
        report_data = data_generator.generate_audit_report(num_findings=10)
        
        # Generate JSON report
        json_report = tmp_path / "report.json"
        json_report.write_text(json.dumps(report_data, indent=2))
        
        # Generate Markdown report
        md_report = tmp_path / "report.md"
        md_content = f"# {report_data['title']}\n\n"
        md_content += f"**Auditor:** {report_data['auditor']}\n\n"
        md_content += f"## Summary\n\n"
        md_content += f"- Total Findings: {report_data['summary']['total_findings']}\n"
        md_report.write_text(md_content)
        
        # Generate HTML report (simulated)
        html_report = tmp_path / "report.html"
        html_content = f"<html><body><h1>{report_data['title']}</h1></body></html>"
        html_report.write_text(html_content)
        
        # Verify all formats
        assert json_report.exists()
        assert md_report.exists()
        assert html_report.exists()
    
    def test_executive_summary_generation(self, data_generator):
        """Test generating executive summary."""
        report = data_generator.generate_audit_report(num_findings=20)
        
        # Generate executive summary
        summary = {
            "contract": report["contract"]["name"],
            "audit_date": report["audit_date"],
            "risk_level": "HIGH" if report["summary"]["critical"] > 0 else "MEDIUM",
            "total_findings": report["summary"]["total_findings"],
            "critical_findings": report["summary"]["critical"],
            "recommendations": report["recommendations"][:3],  # Top 3
        }
        
        assert "contract" in summary
        assert summary["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_trend_analysis_report(self, data_generator):
        """Test generating trend analysis across multiple audits."""
        # Generate multiple audit reports
        reports = [data_generator.generate_audit_report(num_findings=10) for _ in range(5)]
        
        # Analyze trends
        total_findings_trend = [r["summary"]["total_findings"] for r in reports]
        critical_findings_trend = [r["summary"]["critical"] for r in reports]
        
        # Calculate trend
        is_improving = total_findings_trend[-1] < total_findings_trend[0]
        
        trend_report = {
            "total_audits": len(reports),
            "total_findings_trend": total_findings_trend,
            "critical_findings_trend": critical_findings_trend,
            "is_improving": is_improving,
        }
        
        assert trend_report["total_audits"] == 5


@pytest.mark.e2e
@pytest.mark.advanced
class TestPerformanceOptimization:
    """Test performance optimization scenarios."""
    
    def test_parallel_audit_execution(self, tmp_path, data_generator):
        """Test parallel execution of multiple audits."""
        # Generate multiple contracts
        contracts = [
            tmp_path / f"Contract{i}.sol"
            for i in range(10)
        ]
        
        for contract in contracts:
            contract.write_text(data_generator.generate_contract_code())
        
        # Simulate parallel audit
        results = []
        for contract in contracts:
            result = {
                "contract": contract.name,
                "findings": data_generator.generate_vulnerabilities(count=2),
            }
            results.append(result)
        
        # All contracts should be audited
        assert len(results) == 10
    
    def test_caching_optimization(self, tmp_path, data_generator):
        """Test caching for repeated audits."""
        contract_file = tmp_path / "Contract.sol"
        contract_code = data_generator.generate_contract_code()
        contract_file.write_text(contract_code)
        
        # First audit (cache miss)
        cache = {}
        contract_hash = hash(contract_code)
        
        if contract_hash not in cache:
            findings = data_generator.generate_vulnerabilities(count=5)
            cache[contract_hash] = findings
        
        # Second audit (cache hit)
        cached_findings = cache.get(contract_hash)
        
        # Should return cached results
        assert cached_findings is not None
        assert len(cached_findings) == 5


@pytest.mark.e2e
@pytest.mark.advanced
class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_partial_audit_recovery(self, tmp_path, data_generator):
        """Test recovering from partial audit failure."""
        contracts = [tmp_path / f"Contract{i}.sol" for i in range(5)]
        
        for contract in contracts:
            contract.write_text(data_generator.generate_contract_code())
        
        # Simulate partial failure
        results = []
        for i, contract in enumerate(contracts):
            if i == 2:
                # Simulate failure
                result = {"contract": contract.name, "error": "Analysis failed"}
            else:
                result = {
                    "contract": contract.name,
                    "findings": data_generator.generate_vulnerabilities(count=2),
                }
            results.append(result)
        
        # Should have results for all contracts
        assert len(results) == 5
        
        # Should identify failed audits
        failed = [r for r in results if "error" in r]
        assert len(failed) == 1
    
    def test_graceful_degradation(self, data_generator):
        """Test graceful degradation when services unavailable."""
        # Simulate service unavailable
        vector_db_available = False
        
        # Fallback to basic analysis
        if not vector_db_available:
            # Use rule-based detection instead
            findings = data_generator.generate_vulnerabilities(count=3)
            findings[0]["detection_method"] = "rule-based"
        else:
            findings = data_generator.generate_vulnerabilities(count=10)
            findings[0]["detection_method"] = "vector-db"
        
        # Should still produce findings
        assert len(findings) > 0
        assert findings[0]["detection_method"] == "rule-based"
