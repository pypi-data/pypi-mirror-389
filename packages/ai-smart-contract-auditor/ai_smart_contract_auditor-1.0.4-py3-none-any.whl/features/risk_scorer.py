#!/usr/bin/env python3
"""
Risk Scoring Module
Provides quantitative vulnerability assessment using CVSS-style scoring
"""

import json
from typing import Dict, List
from enum import Enum

class Severity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFORMATIONAL = 1

class ImpactCategory(Enum):
    """Impact categories for scoring"""
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"
    FINANCIAL = "financial"

class RiskScorer:
    """
    CVSS-style risk scoring for smart contract vulnerabilities
    """
    
    # Base score weights
    SEVERITY_WEIGHTS = {
        'CRITICAL': 10.0,
        'HIGH': 7.5,
        'MEDIUM': 5.0,
        'LOW': 2.5,
        'INFORMATIONAL': 1.0
    }
    
    # Exploitability factors
    EXPLOITABILITY_FACTORS = {
        'attack_vector': {
            'NETWORK': 1.0,      # Remote exploitation
            'ADJACENT': 0.8,     # Adjacent network
            'LOCAL': 0.6,        # Local access
            'PHYSICAL': 0.4      # Physical access
        },
        'attack_complexity': {
            'LOW': 1.0,          # Easy to exploit
            'MEDIUM': 0.7,       # Moderate complexity
            'HIGH': 0.4          # Difficult to exploit
        },
        'privileges_required': {
            'NONE': 1.0,         # No privileges needed
            'LOW': 0.7,          # Low privileges
            'HIGH': 0.4          # High privileges
        },
        'user_interaction': {
            'NONE': 1.0,         # No user interaction
            'REQUIRED': 0.7      # User interaction needed
        }
    }
    
    # Impact factors
    IMPACT_FACTORS = {
        'confidentiality': {
            'HIGH': 1.0,         # Total information disclosure
            'LOW': 0.5,          # Partial disclosure
            'NONE': 0.0          # No impact
        },
        'integrity': {
            'HIGH': 1.0,         # Total data modification
            'LOW': 0.5,          # Partial modification
            'NONE': 0.0          # No impact
        },
        'availability': {
            'HIGH': 1.0,         # Total service disruption
            'LOW': 0.5,          # Partial disruption
            'NONE': 0.0          # No impact
        },
        'financial': {
            'HIGH': 1.5,         # > $1M potential loss
            'MEDIUM': 1.0,       # $100K - $1M
            'LOW': 0.5,          # < $100K
            'NONE': 0.0          # No financial impact
        }
    }
    
    def __init__(self):
        """Initialize risk scorer"""
        pass
    
    def calculate_exploitability_score(self, vulnerability: Dict) -> float:
        """
        Calculate exploitability subscore
        
        Args:
            vulnerability: Dict with exploitability metrics
            
        Returns:
            Exploitability score (0-10)
        """
        attack_vector = vulnerability.get('attack_vector', 'NETWORK')
        attack_complexity = vulnerability.get('attack_complexity', 'LOW')
        privileges = vulnerability.get('privileges_required', 'NONE')
        user_interaction = vulnerability.get('user_interaction', 'NONE')
        
        exploitability = (
            self.EXPLOITABILITY_FACTORS['attack_vector'].get(attack_vector, 1.0) *
            self.EXPLOITABILITY_FACTORS['attack_complexity'].get(attack_complexity, 1.0) *
            self.EXPLOITABILITY_FACTORS['privileges_required'].get(privileges, 1.0) *
            self.EXPLOITABILITY_FACTORS['user_interaction'].get(user_interaction, 1.0)
        )
        
        return exploitability * 10.0
    
    def calculate_impact_score(self, vulnerability: Dict) -> float:
        """
        Calculate impact subscore
        
        Args:
            vulnerability: Dict with impact metrics
            
        Returns:
            Impact score (0-10)
        """
        confidentiality = vulnerability.get('confidentiality_impact', 'NONE')
        integrity = vulnerability.get('integrity_impact', 'NONE')
        availability = vulnerability.get('availability_impact', 'NONE')
        financial = vulnerability.get('financial_impact', 'NONE')
        
        impact = (
            self.IMPACT_FACTORS['confidentiality'].get(confidentiality, 0.0) +
            self.IMPACT_FACTORS['integrity'].get(integrity, 0.0) +
            self.IMPACT_FACTORS['availability'].get(availability, 0.0) +
            self.IMPACT_FACTORS['financial'].get(financial, 0.0)
        )
        
        # Normalize to 0-10 scale
        return min(impact * 2.5, 10.0)
    
    def calculate_base_score(self, vulnerability: Dict) -> float:
        """
        Calculate CVSS-style base score
        
        Args:
            vulnerability: Dict with vulnerability details
            
        Returns:
            Base score (0-10)
        """
        exploitability = self.calculate_exploitability_score(vulnerability)
        impact = self.calculate_impact_score(vulnerability)
        
        # CVSS v3.1 formula (simplified)
        if impact == 0:
            return 0.0
        
        base_score = min(
            (exploitability + impact) / 2.0,
            10.0
        )
        
        return round(base_score, 1)
    
    def calculate_temporal_score(self, base_score: float, vulnerability: Dict) -> float:
        """
        Calculate temporal score (considers exploit availability and remediation)
        
        Args:
            base_score: Base CVSS score
            vulnerability: Dict with temporal metrics
            
        Returns:
            Temporal score (0-10)
        """
        exploit_maturity = {
            'UNPROVEN': 0.85,
            'PROOF_OF_CONCEPT': 0.94,
            'FUNCTIONAL': 0.97,
            'HIGH': 1.0
        }
        
        remediation_level = {
            'OFFICIAL_FIX': 0.87,
            'TEMPORARY_FIX': 0.90,
            'WORKAROUND': 0.95,
            'UNAVAILABLE': 1.0
        }
        
        exploit = vulnerability.get('exploit_maturity', 'UNPROVEN')
        remediation = vulnerability.get('remediation_level', 'UNAVAILABLE')
        
        temporal = base_score * exploit_maturity.get(exploit, 1.0) * remediation_level.get(remediation, 1.0)
        
        return round(temporal, 1)
    
    def score_vulnerability(self, vulnerability: Dict) -> Dict:
        """
        Complete vulnerability risk scoring
        
        Args:
            vulnerability: Dict with all vulnerability details
            
        Returns:
            Dict with scores and risk rating
        """
        # Calculate scores
        base_score = self.calculate_base_score(vulnerability)
        temporal_score = self.calculate_temporal_score(base_score, vulnerability)
        
        # Determine risk rating
        if temporal_score >= 9.0:
            risk_rating = 'CRITICAL'
        elif temporal_score >= 7.0:
            risk_rating = 'HIGH'
        elif temporal_score >= 4.0:
            risk_rating = 'MEDIUM'
        elif temporal_score >= 0.1:
            risk_rating = 'LOW'
        else:
            risk_rating = 'INFORMATIONAL'
        
        return {
            'vulnerability': vulnerability.get('title', 'Unknown'),
            'base_score': base_score,
            'temporal_score': temporal_score,
            'risk_rating': risk_rating,
            'exploitability_score': self.calculate_exploitability_score(vulnerability),
            'impact_score': self.calculate_impact_score(vulnerability),
            'severity': vulnerability.get('severity', 'UNKNOWN')
        }
    
    def score_protocol(self, vulnerabilities: List[Dict]) -> Dict:
        """
        Calculate overall protocol risk score
        
        Args:
            vulnerabilities: List of vulnerability dicts
            
        Returns:
            Dict with protocol risk metrics
        """
        if not vulnerabilities:
            return {
                'protocol_risk_score': 0.0,
                'risk_rating': 'NONE',
                'total_vulnerabilities': 0,
                'by_severity': {}
            }
        
        # Score each vulnerability
        scored_vulns = [self.score_vulnerability(v) for v in vulnerabilities]
        
        # Calculate weighted average
        total_score = sum(v['temporal_score'] for v in scored_vulns)
        avg_score = total_score / len(scored_vulns)
        
        # Apply severity weighting
        severity_counts = {}
        for v in scored_vulns:
            severity = v['risk_rating']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Weighted protocol score
        weighted_score = avg_score
        if severity_counts.get('CRITICAL', 0) > 0:
            weighted_score = min(weighted_score * 1.5, 10.0)
        elif severity_counts.get('HIGH', 0) > 2:
            weighted_score = min(weighted_score * 1.2, 10.0)
        
        # Determine protocol risk rating
        if weighted_score >= 8.0:
            protocol_rating = 'CRITICAL'
        elif weighted_score >= 6.0:
            protocol_rating = 'HIGH'
        elif weighted_score >= 4.0:
            protocol_rating = 'MEDIUM'
        elif weighted_score >= 2.0:
            protocol_rating = 'LOW'
        else:
            protocol_rating = 'MINIMAL'
        
        return {
            'protocol_risk_score': round(weighted_score, 1),
            'risk_rating': protocol_rating,
            'total_vulnerabilities': len(vulnerabilities),
            'by_severity': severity_counts,
            'vulnerabilities': scored_vulns
        }


def main():
    """
    Example usage of risk scorer
    """
    print("=== Risk Scoring Module ===\n")
    
    # Initialize scorer
    scorer = RiskScorer()
    
    # Example vulnerabilities
    vulnerabilities = [
        {
            'title': 'Reentrancy in withdraw function',
            'severity': 'HIGH',
            'attack_vector': 'NETWORK',
            'attack_complexity': 'LOW',
            'privileges_required': 'NONE',
            'user_interaction': 'NONE',
            'confidentiality_impact': 'NONE',
            'integrity_impact': 'HIGH',
            'availability_impact': 'NONE',
            'financial_impact': 'HIGH',
            'exploit_maturity': 'FUNCTIONAL',
            'remediation_level': 'UNAVAILABLE'
        },
        {
            'title': 'Missing input validation',
            'severity': 'MEDIUM',
            'attack_vector': 'NETWORK',
            'attack_complexity': 'MEDIUM',
            'privileges_required': 'LOW',
            'user_interaction': 'NONE',
            'confidentiality_impact': 'LOW',
            'integrity_impact': 'LOW',
            'availability_impact': 'NONE',
            'financial_impact': 'LOW',
            'exploit_maturity': 'PROOF_OF_CONCEPT',
            'remediation_level': 'WORKAROUND'
        }
    ]
    
    # Score protocol
    protocol_score = scorer.score_protocol(vulnerabilities)
    
    print(f"Protocol Risk Score: {protocol_score['protocol_risk_score']}/10")
    print(f"Risk Rating: {protocol_score['risk_rating']}")
    print(f"Total Vulnerabilities: {protocol_score['total_vulnerabilities']}")
    print(f"\nBy Severity:")
    for severity, count in protocol_score['by_severity'].items():
        print(f"  {severity}: {count}")
    
    print(f"\nIndividual Vulnerability Scores:")
    for vuln in protocol_score['vulnerabilities']:
        print(f"  - {vuln['vulnerability']}: {vuln['temporal_score']}/10 ({vuln['risk_rating']})")


if __name__ == "__main__":
    main()
