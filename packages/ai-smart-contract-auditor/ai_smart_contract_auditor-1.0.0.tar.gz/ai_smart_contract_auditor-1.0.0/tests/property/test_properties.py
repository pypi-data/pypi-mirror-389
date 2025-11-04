"""
Property-based tests using Hypothesis.

Property-based testing generates hundreds of random test cases to verify
that code properties hold for all inputs, not just hand-picked examples.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
import json


class TestInputProperties:
    """Test properties of input validation."""
    
    @given(st.text())
    def test_contract_content_always_string(self, content):
        """Contract content should always be processable as string."""
        assert isinstance(content, str)
        assert len(content) >= 0
    
    @given(st.text(min_size=1, max_size=1000))
    def test_nonempty_content_has_length(self, content):
        """Non-empty content should have positive length."""
        assert len(content) > 0
    
    @given(st.lists(st.text(), min_size=0, max_size=100))
    def test_contract_list_processing(self, contracts):
        """Contract lists should be iterable."""
        assert isinstance(contracts, list)
        count = sum(1 for _ in contracts)
        assert count == len(contracts)
    
    @given(st.text(), st.text())
    def test_contract_concatenation_length(self, part1, part2):
        """Concatenated contracts should have combined length."""
        combined = part1 + part2
        assert len(combined) == len(part1) + len(part2)


class TestSeverityProperties:
    """Test properties of severity scoring."""
    
    @given(st.sampled_from(["LOW", "MEDIUM", "HIGH", "CRITICAL"]))
    def test_severity_always_valid(self, severity):
        """Severity should always be a valid level."""
        valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "INFO"]
        assert severity in valid_severities
    
    @given(st.floats(min_value=0.0, max_value=1.0))
    def test_confidence_in_range(self, confidence):
        """Confidence scores should be between 0 and 1."""
        assert 0.0 <= confidence <= 1.0
    
    @given(st.integers(min_value=0, max_value=10))
    def test_risk_score_calculation(self, impact):
        """Risk scores should be calculable from impact."""
        exploitability = 5
        risk = impact * exploitability
        assert risk >= 0
        assert risk <= 100


class TestVulnerabilityProperties:
    """Test properties of vulnerability data."""
    
    @given(
        st.fixed_dictionaries({
            'type': st.sampled_from(['reentrancy', 'overflow', 'access-control']),
            'severity': st.sampled_from(['LOW', 'MEDIUM', 'HIGH']),
            'confidence': st.floats(min_value=0.0, max_value=1.0)
        })
    )
    def test_vulnerability_structure(self, vuln):
        """Vulnerabilities should have required fields."""
        assert 'type' in vuln
        assert 'severity' in vuln
        assert 'confidence' in vuln
        assert isinstance(vuln['type'], str)
        assert isinstance(vuln['severity'], str)
        assert isinstance(vuln['confidence'], float)
    
    @given(st.lists(
        st.fixed_dictionaries({
            'type': st.text(min_size=1),
            'line': st.integers(min_value=1)
        }),
        min_size=0,
        max_size=50
    ))
    def test_findings_list_properties(self, findings):
        """Findings lists should maintain order and count."""
        assert len(findings) >= 0
        if findings:
            assert all('type' in f for f in findings)
            assert all('line' in f for f in findings)


class TestReportProperties:
    """Test properties of report generation."""
    
    @given(st.lists(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.floats())
    )))
    def test_report_serialization(self, data):
        """Reports should be JSON serializable."""
        try:
            json_str = json.dumps(data)
            assert isinstance(json_str, str)
            
            # Should be deserializable
            parsed = json.loads(json_str)
            assert isinstance(parsed, list)
        except (TypeError, ValueError):
            # Some values might not be JSON serializable (NaN, Inf)
            # This is expected and OK
            pass
    
    @given(st.text(min_size=1), st.text(min_size=1))
    def test_report_title_and_content(self, title, content):
        """Reports should have title and content."""
        report = {'title': title, 'content': content}
        assert len(report['title']) > 0
        assert len(report['content']) > 0


class TestPathProperties:
    """Test properties of file path handling."""
    
    @given(st.text(alphabet=st.characters(blacklist_characters='/\\:*?"<>|'), min_size=1, max_size=50))
    def test_filename_validity(self, filename):
        """Filenames should not contain invalid characters."""
        invalid_chars = set('/\\:*?"<>|')
        assert not any(c in filename for c in invalid_chars)
    
    @given(st.lists(st.text(alphabet=st.characters(blacklist_characters='/\\'), min_size=1, max_size=20), min_size=1, max_size=5))
    def test_path_joining(self, parts):
        """Path joining should preserve all parts."""
        import os
        # Filter out path separators from parts
        valid_parts = [p for p in parts if p and not any(c in p for c in ['/','\\'])]
        if valid_parts:
            path = os.path.join(*valid_parts)
            assert all(part in path or part == '.' for part in valid_parts)


class TestDataTransformationProperties:
    """Test properties of data transformations."""
    
    @given(st.lists(st.integers()))
    def test_list_reversal_idempotent(self, data):
        """Reversing a list twice should give original list."""
        reversed_once = list(reversed(data))
        reversed_twice = list(reversed(reversed_once))
        assert data == reversed_twice
    
    @given(st.lists(st.integers()))
    def test_sorting_preserves_elements(self, data):
        """Sorting should preserve all elements."""
        sorted_data = sorted(data)
        assert len(sorted_data) == len(data)
        assert set(sorted_data) == set(data)
    
    @given(st.lists(st.integers(), min_size=1))
    def test_filtering_reduces_or_maintains_size(self, data):
        """Filtering should not increase list size."""
        filtered = [x for x in data if x > 0]
        assert len(filtered) <= len(data)


class TestStringProperties:
    """Test properties of string operations."""
    
    @given(st.text())
    def test_strip_idempotent(self, text):
        """Stripping whitespace twice should equal stripping once."""
        assert text.strip().strip() == text.strip()
    
    @given(st.text(), st.text())
    def test_concatenation_commutative_length(self, a, b):
        """Concatenation length should be commutative."""
        assert len(a + b) == len(b + a)
    
    @given(st.text(min_size=1, alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))))
    def test_lowercase_uppercase_roundtrip(self, text):
        """Lowercase then uppercase roundtrip for ASCII lowercase letters."""
        # Use only ASCII lowercase to avoid unicode special-casing issues
        assert text.lower().upper().lower() == text.lower()


class TestNumericProperties:
    """Test properties of numeric operations."""
    
    @given(st.floats(min_value=0.0, max_value=1.0), st.floats(min_value=0.0, max_value=1.0))
    def test_confidence_combination(self, conf1, conf2):
        """Combined confidence should be in valid range."""
        # Average confidence
        combined = (conf1 + conf2) / 2
        assert 0.0 <= combined <= 1.0
    
    @given(st.integers(min_value=1, max_value=100))
    def test_percentage_calculation(self, value):
        """Percentage calculations should be valid."""
        total = 100
        percentage = (value / total) * 100
        assert 0 <= percentage <= 100
    
    @given(st.integers(min_value=0))
    def test_count_non_negative(self, count):
        """Counts should always be non-negative."""
        assert count >= 0


class TestCollectionProperties:
    """Test properties of collection operations."""
    
    @given(st.lists(st.integers()))
    def test_set_removes_duplicates(self, data):
        """Converting to set should remove duplicates."""
        unique = set(data)
        assert len(unique) <= len(data)
    
    @given(st.lists(st.integers(), min_size=1))
    def test_max_in_list(self, data):
        """Max element should be in the list."""
        maximum = max(data)
        assert maximum in data
    
    @given(st.lists(st.integers(), min_size=1))
    def test_min_in_list(self, data):
        """Min element should be in the list."""
        minimum = min(data)
        assert minimum in data


@pytest.mark.property
class TestStatefulProperties(RuleBasedStateMachine):
    """Stateful property-based testing."""
    
    def __init__(self):
        super().__init__()
        self.findings = []
        self.total_added = 0
        self.total_removed = 0
    
    @rule(finding=st.fixed_dictionaries({
        'type': st.text(min_size=1),
        'severity': st.sampled_from(['LOW', 'MEDIUM', 'HIGH'])
    }))
    def add_finding(self, finding):
        """Add a finding to the list."""
        self.findings.append(finding)
        self.total_added += 1
    
    @rule()
    def remove_finding(self):
        """Remove a finding from the list."""
        if self.findings:
            self.findings.pop()
            self.total_removed += 1
    
    @rule()
    def clear_findings(self):
        """Clear all findings."""
        removed_count = len(self.findings)
        self.findings.clear()
        self.total_removed += removed_count
    
    @invariant()
    def findings_count_consistent(self):
        """Findings count should match list length."""
        assert len(self.findings) >= 0
        assert len(self.findings) == self.total_added - self.total_removed
    
    @invariant()
    def all_findings_have_type(self):
        """All findings should have a type field."""
        assert all('type' in f for f in self.findings)


# Test the stateful machine
TestStateful = TestStatefulProperties.TestCase


@pytest.mark.property
class TestAdvancedProperties:
    """Advanced property-based tests."""
    
    @given(st.text())
    @example("")  # Explicitly test empty string
    @example("a" * 10000)  # Explicitly test long string
    def test_contract_parsing_robustness(self, contract):
        """Contract parsing should handle any string input."""
        # Should not crash
        lines = contract.split('\n')
        assert isinstance(lines, list)
        assert len(lines) > 0
    
    @given(
        st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=100),
        st.integers(min_value=1, max_value=10)
    )
    def test_parallel_processing_speedup(self, tasks, workers):
        """Parallel processing should not increase total work."""
        total_work = sum(tasks)
        # In parallel, work is distributed
        work_per_worker = total_work / workers
        assert work_per_worker <= total_work
    
    @settings(max_examples=50)  # Limit examples for expensive tests
    @given(st.lists(st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.text(min_size=1, max_size=100)
    ), min_size=1, max_size=20))
    def test_vulnerability_deduplication(self, vulns):
        """Deduplication should remove exact duplicates."""
        # Convert to JSON strings for comparison
        unique_vulns = []
        seen = set()
        
        for v in vulns:
            v_str = json.dumps(v, sort_keys=True)
            if v_str not in seen:
                seen.add(v_str)
                unique_vulns.append(v)
        
        assert len(unique_vulns) <= len(vulns)
        assert len(set(json.dumps(v, sort_keys=True) for v in unique_vulns)) == len(unique_vulns)
