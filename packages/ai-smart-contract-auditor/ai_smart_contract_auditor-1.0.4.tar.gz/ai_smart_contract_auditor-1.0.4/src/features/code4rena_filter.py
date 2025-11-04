#!/usr/bin/env python3
"""
Code4rena Validation Filter
Filter and prioritize findings based on Code4rena validation labels
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

class Code4renaFilter:
    """
    Filter for Code4rena validated findings
    """
    
    # Code4rena label mappings
    VALID_LABELS = {
        'high': ['3 (High Risk)', 'bug', 'sponsor confirmed', 'selected for report'],
        'medium': ['2 (Med Risk)', 'bug', 'sponsor confirmed', 'selected for report'],
        'low': ['QA (Quality Assurance)', 'sponsor confirmed'],
        'gas': ['G (Gas Optimization)', 'sponsor confirmed']
    }
    
    INVALID_LABELS = [
        'invalid',
        'sponsor disputed',
        'sponsor acknowledged',
        'duplicate',
        'insufficient quality report',
        'out of scope'
    ]
    
    def __init__(self, database_path: str = "database/vulnerability_db/vulnerabilities_database.json"):
        """
        Initialize Code4rena filter
        
        Args:
            database_path: Path to vulnerability database
        """
        self.database_path = Path(database_path)
        self.database = self._load_database()
        
        # Statistics
        self.stats = {
            'total_findings': 0,
            'code4rena_findings': 0,
            'validated_findings': 0,
            'invalid_findings': 0,
            'by_severity': defaultdict(int),
            'by_label': defaultdict(int)
        }
    
    def _load_database(self) -> Dict:
        """
        Load vulnerability database
        
        Returns:
            Database content
        """
        if not self.database_path.exists():
            print(f"⚠️ Database not found: {self.database_path}")
            return {'findings': []}
        
        with open(self.database_path) as f:
            return json.load(f)
    
    def filter_validated_findings(self, severity: Optional[str] = None) -> List[Dict]:
        """
        Filter for validated Code4rena findings
        
        Args:
            severity: Optional severity filter (high, medium, low, gas)
            
        Returns:
            List of validated findings
        """
        validated = []
        
        for finding in self.database.get('findings', []):
            self.stats['total_findings'] += 1
            
            # Check if from Code4rena
            source = finding.get('source', '').lower()
            if 'code4rena' not in source:
                continue
            
            self.stats['code4rena_findings'] += 1
            
            # Check labels
            labels = finding.get('labels', [])
            if isinstance(labels, str):
                labels = [labels]
            
            # Count label statistics
            for label in labels:
                self.stats['by_label'][label] += 1
            
            # Check if invalid
            if any(invalid in label.lower() for label in labels 
                  for invalid in self.INVALID_LABELS):
                self.stats['invalid_findings'] += 1
                continue
            
            # Check if validated
            finding_severity = finding.get('severity', '').lower()
            
            is_validated = False
            for sev, valid_labels in self.VALID_LABELS.items():
                if any(vl.lower() in label.lower() for label in labels 
                      for vl in valid_labels):
                    is_validated = True
                    self.stats['by_severity'][sev] += 1
                    break
            
            if not is_validated:
                continue
            
            self.stats['validated_findings'] += 1
            
            # Apply severity filter
            if severity and finding_severity != severity.lower():
                continue
            
            validated.append(finding)
        
        return validated
    
    def get_high_confidence_findings(self, min_confidence: float = 0.8) -> List[Dict]:
        """
        Get high-confidence validated findings
        
        Args:
            min_confidence: Minimum confidence score (0-1)
            
        Returns:
            List of high-confidence findings
        """
        validated = self.filter_validated_findings()
        
        high_confidence = []
        for finding in validated:
            # Calculate confidence based on labels
            labels = finding.get('labels', [])
            if isinstance(labels, str):
                labels = [labels]
            
            confidence = 0.5  # Base confidence
            
            # Boost confidence for certain labels
            if any('sponsor confirmed' in l.lower() for l in labels):
                confidence += 0.2
            if any('selected for report' in l.lower() for l in labels):
                confidence += 0.2
            if any('3 (high risk)' in l.lower() or '2 (med risk)' in l.lower() 
                  for l in labels):
                confidence += 0.1
            
            finding['confidence_score'] = confidence
            
            if confidence >= min_confidence:
                high_confidence.append(finding)
        
        return high_confidence
    
    def create_validated_subset(self, output_path: str = "database/code4rena_validated.json"):
        """
        Create validated subset database
        
        Args:
            output_path: Output path for validated subset
        """
        validated = self.filter_validated_findings()
        
        subset = {
            'metadata': {
                'source': 'Code4rena Validated Findings',
                'total_findings': len(validated),
                'filter_criteria': {
                    'source': 'Code4rena',
                    'labels': self.VALID_LABELS,
                    'excluded': self.INVALID_LABELS
                },
                'statistics': dict(self.stats)
            },
            'findings': validated
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(subset, f, indent=2)
        
        print(f"✅ Created validated subset: {output_path}")
        print(f"   Total findings: {len(validated)}")
        print(f"   High: {self.stats['by_severity']['high']}")
        print(f"   Medium: {self.stats['by_severity']['medium']}")
        print(f"   Low: {self.stats['by_severity']['low']}")
        
        return str(output_path)
    
    def generate_statistics_report(self) -> Dict:
        """
        Generate statistics report
        
        Returns:
            Statistics report
        """
        report = {
            'total_findings': self.stats['total_findings'],
            'code4rena_findings': self.stats['code4rena_findings'],
            'validated_findings': self.stats['validated_findings'],
            'invalid_findings': self.stats['invalid_findings'],
            'validation_rate': (
                self.stats['validated_findings'] / self.stats['code4rena_findings']
                if self.stats['code4rena_findings'] > 0 else 0
            ),
            'by_severity': dict(self.stats['by_severity']),
            'top_labels': sorted(
                self.stats['by_label'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        
        return report
    
    def print_statistics(self):
        """
        Print statistics
        """
        report = self.generate_statistics_report()
        
        print("\\n=== Code4rena Validation Statistics ===\\n")
        print(f"Total findings in database: {report['total_findings']:,}")
        print(f"Code4rena findings: {report['code4rena_findings']:,}")
        print(f"Validated findings: {report['validated_findings']:,}")
        print(f"Invalid findings: {report['invalid_findings']:,}")
        print(f"Validation rate: {report['validation_rate']:.1%}")
        
        print("\\nBy Severity:")
        for severity, count in report['by_severity'].items():
            print(f"  {severity.upper()}: {count:,}")
        
        print("\\nTop Labels:")
        for label, count in report['top_labels']:
            print(f"  {label}: {count:,}")


def example_usage():
    """
    Example usage of Code4rena filter
    """
    print("=== Code4rena Validation Filter ===\\n")
    
    # Initialize filter
    filter = Code4renaFilter()
    
    # Filter validated findings
    validated = filter.filter_validated_findings()
    print(f"✅ Found {len(validated)} validated findings")
    
    # Filter by severity
    high_severity = filter.filter_validated_findings(severity='high')
    print(f"✅ Found {len(high_severity)} high-severity validated findings")
    
    # Get high-confidence findings
    high_confidence = filter.get_high_confidence_findings(min_confidence=0.8)
    print(f"✅ Found {len(high_confidence)} high-confidence findings")
    
    # Create validated subset
    subset_path = filter.create_validated_subset()
    
    # Print statistics
    filter.print_statistics()
    
    print("\\n✅ Code4rena validation filter complete!")


if __name__ == "__main__":
    example_usage()
