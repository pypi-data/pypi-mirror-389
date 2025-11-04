"""
Slither Tool Wrapper
Provides interface for running Slither static analysis and parsing results
"""

import subprocess
import json
import os
from typing import Dict, List, Any


class SlitherWrapper:
    """Wrapper for Slither static analysis tool"""
    
    def __init__(self):
        self.tool_name = "slither"
        self.version = self._get_version()
    
    def _get_version(self) -> str:
        """Get Slither version"""
        try:
            result = subprocess.run(
                ['slither', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Unknown (Error: {e})"
    
    def analyze(self, contract_path: str, output_format: str = "json") -> Dict[str, Any]:
        """
        Run Slither analysis on a contract
        
        Args:
            contract_path: Path to the Solidity contract or project
            output_format: Output format (json, text)
            
        Returns:
            Dictionary containing analysis results
        """
        if not os.path.exists(contract_path):
            return {
                "success": False,
                "error": f"Contract path does not exist: {contract_path}"
            }
        
        try:
            # Run Slither with JSON output
            cmd = ['slither', contract_path, '--json', '-']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse JSON output
            if result.stdout:
                try:
                    analysis_data = json.loads(result.stdout)
                    return {
                        "success": True,
                        "tool": "slither",
                        "version": self.version,
                        "contract": contract_path,
                        "raw_output": result.stdout,
                        "findings": self._parse_findings(analysis_data),
                        "stderr": result.stderr
                    }
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Failed to parse JSON output: {e}",
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
            else:
                return {
                    "success": False,
                    "error": "No output from Slither",
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Slither analysis timed out after 120 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Slither analysis failed: {str(e)}"
            }
    
    def _parse_findings(self, analysis_data: Dict) -> List[Dict]:
        """
        Parse Slither findings from JSON output
        
        Args:
            analysis_data: Raw JSON data from Slither
            
        Returns:
            List of parsed findings
        """
        findings = []
        
        if not analysis_data or 'results' not in analysis_data:
            return findings
        
        detectors = analysis_data.get('results', {}).get('detectors', [])
        
        for detector in detectors:
            finding = {
                "detector": detector.get('check', 'unknown'),
                "impact": detector.get('impact', 'unknown'),
                "confidence": detector.get('confidence', 'unknown'),
                "description": detector.get('description', ''),
                "elements": [],
                "severity": self._map_severity(detector.get('impact', 'unknown'))
            }
            
            # Extract code elements
            for element in detector.get('elements', []):
                finding['elements'].append({
                    "type": element.get('type', ''),
                    "name": element.get('name', ''),
                    "source_mapping": element.get('source_mapping', {}),
                    "type_specific_fields": element.get('type_specific_fields', {})
                })
            
            findings.append(finding)
        
        return findings
    
    def _map_severity(self, impact: str) -> str:
        """
        Map Slither impact to severity level
        
        Args:
            impact: Slither impact level
            
        Returns:
            Severity level (HIGH, MEDIUM, LOW, INFORMATIONAL)
        """
        impact_map = {
            'High': 'HIGH',
            'Medium': 'MEDIUM',
            'Low': 'LOW',
            'Informational': 'INFORMATIONAL',
            'Optimization': 'INFORMATIONAL'
        }
        return impact_map.get(impact, 'UNKNOWN')
    
    def filter_findings(self, 
                       findings: List[Dict],
                       min_severity: str = 'LOW',
                       min_confidence: str = 'Low') -> List[Dict]:
        """
        Filter findings by severity and confidence
        
        Args:
            findings: List of findings
            min_severity: Minimum severity level
            min_confidence: Minimum confidence level
            
        Returns:
            Filtered list of findings
        """
        severity_order = ['INFORMATIONAL', 'LOW', 'MEDIUM', 'HIGH']
        confidence_order = ['Low', 'Medium', 'High']
        
        min_sev_idx = severity_order.index(min_severity) if min_severity in severity_order else 0
        min_conf_idx = confidence_order.index(min_confidence) if min_confidence in confidence_order else 0
        
        filtered = []
        for finding in findings:
            sev = finding.get('severity', 'INFORMATIONAL')
            conf = finding.get('confidence', 'Low')
            
            sev_idx = severity_order.index(sev) if sev in severity_order else 0
            conf_idx = confidence_order.index(conf) if conf in confidence_order else 0
            
            if sev_idx >= min_sev_idx and conf_idx >= min_conf_idx:
                filtered.append(finding)
        
        return filtered
    
    def generate_report(self, analysis_result: Dict) -> str:
        """
        Generate a human-readable report from analysis results
        
        Args:
            analysis_result: Analysis results dictionary
            
        Returns:
            Formatted report string
        """
        if not analysis_result.get('success'):
            return f"Analysis failed: {analysis_result.get('error', 'Unknown error')}"
        
        findings = analysis_result.get('findings', [])
        
        report = f"""
=== Slither Static Analysis Report ===
Tool: {analysis_result.get('tool', 'slither')}
Version: {analysis_result.get('version', 'unknown')}
Contract: {analysis_result.get('contract', 'unknown')}

Total Findings: {len(findings)}
"""
        
        # Count by severity
        severity_counts = {}
        for finding in findings:
            sev = finding.get('severity', 'UNKNOWN')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        report += "\nFindings by Severity:\n"
        for sev in ['HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL']:
            count = severity_counts.get(sev, 0)
            if count > 0:
                report += f"  {sev}: {count}\n"
        
        # List findings
        report += "\nDetailed Findings:\n"
        for i, finding in enumerate(findings, 1):
            report += f"\n{i}. [{finding.get('severity', 'UNKNOWN')}] {finding.get('detector', 'unknown')}\n"
            report += f"   Confidence: {finding.get('confidence', 'unknown')}\n"
            report += f"   Description: {finding.get('description', 'No description')[:200]}\n"
        
        return report


if __name__ == "__main__":
    # Test the wrapper
    wrapper = SlitherWrapper()
    print(f"Slither version: {wrapper.version}")
