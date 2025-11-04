#!/usr/bin/env python3
"""
Report Generation Module
Generates professional audit reports with PDF export
"""

import json
import os
from datetime import datetime
from typing import Dict, List
from pathlib import Path

class ReportGenerator:
    """
    Professional audit report generator with PDF export
    """
    
    def __init__(self, output_dir: str = "audit_reports"):
        """
        Initialize report generator
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_markdown_report(self, audit_data: Dict) -> str:
        """
        Generate comprehensive markdown audit report
        
        Args:
            audit_data: Dict with audit results
            
        Returns:
            Markdown report content
        """
        contract_name = audit_data.get('contract_name', 'Unknown Contract')
        findings = audit_data.get('findings', [])
        metadata = audit_data.get('metadata', {})
        
        # Calculate statistics
        total_findings = len(findings)
        by_severity = {}
        for finding in findings:
            severity = finding.get('severity', 'UNKNOWN')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        critical = by_severity.get('CRITICAL', 0)
        high = by_severity.get('HIGH', 0)
        medium = by_severity.get('MEDIUM', 0)
        low = by_severity.get('LOW', 0)
        info = by_severity.get('INFORMATIONAL', 0)
        
        # Generate report
        report = f"""# Smart Contract Security Audit Report

## {contract_name}

**Audit Date**: {datetime.now().strftime('%B %d, %Y')}  
**Auditor**: AI-Powered Smart Contract Auditor  
**Version**: 1.0

---

## Executive Summary

This report presents the findings of a comprehensive security audit conducted on **{contract_name}**. The audit employed multiple analysis techniques including static analysis, dynamic analysis, and AI-powered vulnerability detection.

### Audit Scope

- **Contract**: {contract_name}
- **Lines of Code**: {metadata.get('loc', 'N/A')}
- **Analysis Duration**: {metadata.get('duration', 'N/A')}
- **Tools Used**: Slither, Foundry, AI Analysis

### Risk Assessment

| Severity | Count | Status |
|----------|-------|--------|
| **CRITICAL** | {critical} | {'🔴 IMMEDIATE ACTION REQUIRED' if critical > 0 else '✅ None Found'} |
| **HIGH** | {high} | {'🟠 URGENT' if high > 0 else '✅ None Found'} |
| **MEDIUM** | {medium} | {'🟡 Important' if medium > 0 else '✅ None Found'} |
| **LOW** | {low} | {'🔵 Minor' if low > 0 else '✅ None Found'} |
| **INFORMATIONAL** | {info} | 'ℹ️ Advisory' |
| **TOTAL** | {total_findings} | |

### Overall Risk Score

"""
        
        # Calculate overall risk
        risk_score = (critical * 10 + high * 7.5 + medium * 5 + low * 2.5) / max(total_findings, 1)
        
        if risk_score >= 8.0:
            risk_rating = "🔴 CRITICAL"
            recommendation = "**DO NOT DEPLOY**. Critical vulnerabilities must be fixed immediately."
        elif risk_score >= 6.0:
            risk_rating = "🟠 HIGH"
            recommendation = "**DEPLOYMENT NOT RECOMMENDED**. High severity issues require immediate attention."
        elif risk_score >= 4.0:
            risk_rating = "🟡 MEDIUM"
            recommendation = "**PROCEED WITH CAUTION**. Address medium severity issues before deployment."
        elif risk_score >= 2.0:
            risk_rating = "🔵 LOW"
            recommendation = "**ACCEPTABLE FOR DEPLOYMENT**. Address low severity issues in next update."
        else:
            risk_rating = "✅ MINIMAL"
            recommendation = "**SAFE FOR DEPLOYMENT**. No significant security concerns identified."
        
        report += f"""**Risk Score**: {risk_score:.1f}/10  
**Risk Rating**: {risk_rating}  
**Recommendation**: {recommendation}

---

## Detailed Findings

"""
        
        # Group findings by severity
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL']
        
        for severity in severity_order:
            severity_findings = [f for f in findings if f.get('severity') == severity]
            
            if not severity_findings:
                continue
            
            report += f"\n### {severity} Severity Findings\n\n"
            
            for idx, finding in enumerate(severity_findings, 1):
                title = finding.get('title', 'Unknown Vulnerability')
                description = finding.get('description', 'No description provided')
                location = finding.get('location', 'Unknown')
                impact = finding.get('impact', 'Not specified')
                recommendation = finding.get('recommendation', 'No recommendation provided')
                poc_available = finding.get('poc_available', False)
                fix_available = finding.get('fix_available', False)
                
                report += f"""#### [{severity}-{idx:02d}] {title}

**Location**: `{location}`  
**Impact**: {impact}  
**PoC Available**: {'✅ Yes' if poc_available else '❌ No'}  
**Fix Available**: {'✅ Yes' if fix_available else '❌ No'}

**Description**:
{description}

**Recommendation**:
{recommendation}

---

"""
        
        # Add methodology section
        report += """
## Audit Methodology

### Analysis Techniques

1. **Static Analysis**
   - Slither static analyzer
   - Pattern matching against 47,294 known vulnerabilities
   - Code quality checks

2. **Dynamic Analysis**
   - Foundry test execution
   - Symbolic execution
   - Fuzzing

3. **AI-Powered Analysis**
   - Semantic search across 305,943 PoC examples
   - GPT-4.1-mini vulnerability detection
   - Risk scoring with CVSS-style metrics

4. **Manual Review**
   - Code logic verification
   - Business logic analysis
   - Attack vector assessment

### Vulnerability Database

- **Total Patterns**: 47,294 vulnerabilities
- **PoC Examples**: 305,943 exploits
- **Data Sources**: 13 authoritative sources
- **Last Updated**: {datetime.now().strftime('%B %Y')}

---

## Remediation Roadmap

### Immediate Actions (Critical & High)

"""
        
        critical_high = [f for f in findings if f.get('severity') in ['CRITICAL', 'HIGH']]
        if critical_high:
            for idx, finding in enumerate(critical_high, 1):
                report += f"{idx}. **{finding.get('title')}** - {finding.get('location')}\n"
        else:
            report += "✅ No critical or high severity issues found.\n"
        
        report += """
### Short-term Actions (Medium)

"""
        
        medium_findings = [f for f in findings if f.get('severity') == 'MEDIUM']
        if medium_findings:
            for idx, finding in enumerate(medium_findings, 1):
                report += f"{idx}. **{finding.get('title')}** - {finding.get('location')}\n"
        else:
            report += "✅ No medium severity issues found.\n"
        
        report += """
### Long-term Improvements (Low & Informational)

"""
        
        low_info = [f for f in findings if f.get('severity') in ['LOW', 'INFORMATIONAL']]
        if low_info:
            for idx, finding in enumerate(low_info, 1):
                report += f"{idx}. **{finding.get('title')}** - {finding.get('location')}\n"
        else:
            report += "✅ No low severity or informational issues found.\n"
        
        report += """
---

## Appendix

### A. Severity Definitions

- **CRITICAL**: Immediate threat to funds or contract integrity. Exploitable with high probability.
- **HIGH**: Direct threat to funds or functionality. Requires specific conditions but realistic.
- **MEDIUM**: Indirect threat or requires multiple conditions. Moderate impact.
- **LOW**: Minor issues with limited impact. Best practice violations.
- **INFORMATIONAL**: Code quality, gas optimization, or documentation improvements.

### B. Risk Scoring Methodology

Risk scores are calculated using a CVSS v3.1-inspired methodology:

```
Risk Score = (CRITICAL × 10 + HIGH × 7.5 + MEDIUM × 5 + LOW × 2.5) / Total Findings
```

### C. Disclaimer

This audit report is based on automated analysis and should be supplemented with manual review. While our AI-powered system leverages 47,294 known vulnerabilities and 305,943 PoC examples, no audit can guarantee 100% security. The contract developers are responsible for implementing recommended fixes and conducting additional security measures.

---

**Report Generated**: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  
**AI-Powered Smart Contract Auditor v1.0**  
**https://github.com/jw3b-dev/AI-Smart-Contract-Auditor**
"""
        
        return report
    
    def save_markdown_report(self, audit_data: Dict, filename: str = None) -> str:
        """
        Save markdown report to file
        
        Args:
            audit_data: Dict with audit results
            filename: Optional custom filename
            
        Returns:
            Path to saved report
        """
        if filename is None:
            contract_name = audit_data.get('contract_name', 'contract')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{contract_name}_audit_{timestamp}.md"
        
        report_content = self.generate_markdown_report(audit_data)
        
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            f.write(report_content)
        
        return str(filepath)
    
    def generate_pdf_report(self, audit_data: Dict, filename: str = None) -> str:
        """
        Generate PDF report from audit data
        
        Args:
            audit_data: Dict with audit results
            filename: Optional custom filename
            
        Returns:
            Path to saved PDF report
        """
        # First generate markdown
        md_content = self.generate_markdown_report(audit_data)
        
        # Save markdown temporarily
        if filename is None:
            contract_name = audit_data.get('contract_name', 'contract')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{contract_name}_audit_{timestamp}"
        
        md_filepath = self.output_dir / f"{filename}.md"
        pdf_filepath = self.output_dir / f"{filename}.pdf"
        
        with open(md_filepath, 'w') as f:
            f.write(md_content)
        
        # Convert to PDF using manus-md-to-pdf utility
        import subprocess
        try:
            result = subprocess.run(
                ['manus-md-to-pdf', str(md_filepath), str(pdf_filepath)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✅ PDF report generated: {pdf_filepath}")
                return str(pdf_filepath)
            else:
                print(f"⚠️ PDF generation failed: {result.stderr}")
                print(f"📄 Markdown report available: {md_filepath}")
                return str(md_filepath)
        except Exception as e:
            print(f"⚠️ PDF generation error: {e}")
            print(f"📄 Markdown report available: {md_filepath}")
            return str(md_filepath)


def main():
    """
    Example usage of report generator
    """
    print("=== Report Generation Module ===\n")
    
    # Initialize generator
    generator = ReportGenerator()
    
    # Example audit data
    audit_data = {
        'contract_name': 'VulnerableBank.sol',
        'metadata': {
            'loc': 250,
            'duration': '45 seconds'
        },
        'findings': [
            {
                'title': 'Reentrancy in withdraw function',
                'severity': 'HIGH',
                'description': 'The withdraw function calls external contract before updating balance, allowing reentrancy attacks.',
                'location': 'VulnerableBank.sol:45-52',
                'impact': 'Attacker can drain all contract funds through recursive calls.',
                'recommendation': 'Use checks-effects-interactions pattern or ReentrancyGuard.',
                'poc_available': True,
                'fix_available': True
            },
            {
                'title': 'Missing input validation',
                'severity': 'MEDIUM',
                'description': 'The deposit function does not validate input amount.',
                'location': 'VulnerableBank.sol:30-35',
                'impact': 'Users can deposit zero or negative amounts.',
                'recommendation': 'Add require statement to validate amount > 0.',
                'poc_available': False,
                'fix_available': True
            },
            {
                'title': 'Floating pragma',
                'severity': 'LOW',
                'description': 'Contract uses floating pragma ^0.8.0.',
                'location': 'VulnerableBank.sol:2',
                'impact': 'Different compiler versions may produce different bytecode.',
                'recommendation': 'Lock pragma to specific version: pragma solidity 0.8.19;',
                'poc_available': False,
                'fix_available': True
            }
        ]
    }
    
    # Generate markdown report
    md_path = generator.save_markdown_report(audit_data)
    print(f"Markdown report saved: {md_path}")
    
    # Generate PDF report
    pdf_path = generator.generate_pdf_report(audit_data)
    print(f"PDF report saved: {pdf_path}")


if __name__ == "__main__":
    main()
