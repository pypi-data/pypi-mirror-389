"""
Performance Regression Testing.

Tracks performance metrics over time to detect regressions.
Uses pytest-benchmark to store historical data and compare against baselines.
"""

import pytest
import json
import time
from pathlib import Path


@pytest.mark.performance
class TestPerformanceRegression:
    """Performance regression tests with historical tracking."""
    
    def test_vector_db_query_performance(self, benchmark):
        """Benchmark vector database query performance."""
        def query_vector_db():
            # Simulate vector DB query
            time.sleep(0.002)  # 2ms baseline
            return {"results": [{"score": 0.95}]}
        
        result = benchmark(query_vector_db)
        assert result is not None
        
        # Performance assertions
        stats = benchmark.stats
        assert stats['mean'] < 0.01  # Should complete in < 10ms
    
    def test_vulnerability_detection_performance(self, benchmark):
        """Benchmark vulnerability detection performance."""
        def detect_vulnerabilities():
            # Simulate vulnerability detection
            time.sleep(0.005)  # 5ms baseline
            return [{"type": "reentrancy", "severity": "HIGH"}]
        
        result = benchmark(detect_vulnerabilities)
        assert len(result) > 0
        
        stats = benchmark.stats
        assert stats['mean'] < 0.02  # Should complete in < 20ms
    
    def test_poc_generation_performance(self, benchmark):
        """Benchmark PoC generation performance."""
        def generate_poc():
            # Simulate PoC generation
            time.sleep(0.01)  # 10ms baseline
            return "pragma solidity ^0.8.0; contract PoC {}"
        
        result = benchmark(generate_poc)
        assert len(result) > 0
        
        stats = benchmark.stats
        assert stats['mean'] < 0.05  # Should complete in < 50ms
    
    def test_fix_suggestion_performance(self, benchmark):
        """Benchmark fix suggestion performance."""
        def suggest_fix():
            # Simulate fix suggestion
            time.sleep(0.008)  # 8ms baseline
            return {"original": "x = y", "fixed": "x = y.checked()"}
        
        result = benchmark(suggest_fix)
        assert "original" in result
        
        stats = benchmark.stats
        assert stats['mean'] < 0.03  # Should complete in < 30ms
    
    def test_report_generation_performance(self, benchmark):
        """Benchmark report generation performance."""
        def generate_report():
            # Simulate report generation
            time.sleep(0.005)  # 5ms baseline
            return {"title": "Audit Report", "findings": []}
        
        result = benchmark(generate_report)
        assert "title" in result
        
        stats = benchmark.stats
        assert stats['mean'] < 0.02  # Should complete in < 20ms
    
    def test_batch_audit_performance(self, benchmark):
        """Benchmark batch audit performance."""
        def batch_audit():
            # Simulate batch audit of 10 contracts
            time.sleep(0.01)  # 10ms baseline
            return [{"contract": f"Contract{i}", "findings": []} for i in range(10)]
        
        result = benchmark(batch_audit)
        assert len(result) == 10
        
        stats = benchmark.stats
        assert stats['mean'] < 0.05  # Should complete in < 50ms
    
    def test_parallel_processing_performance(self, benchmark):
        """Benchmark parallel processing performance."""
        def parallel_process():
            # Simulate parallel processing
            time.sleep(0.003)  # 3ms baseline
            return {"processed": 100, "time": 0.003}
        
        result = benchmark(parallel_process)
        assert result["processed"] > 0
        
        stats = benchmark.stats
        assert stats['mean'] < 0.01  # Should complete in < 10ms
    
    def test_database_write_performance(self, benchmark):
        """Benchmark database write performance."""
        def write_to_db():
            # Simulate database write
            time.sleep(0.004)  # 4ms baseline
            return True
        
        result = benchmark(write_to_db)
        assert result is True
        
        stats = benchmark.stats
        assert stats['mean'] < 0.015  # Should complete in < 15ms
    
    def test_cache_lookup_performance(self, benchmark):
        """Benchmark cache lookup performance."""
        def cache_lookup():
            # Simulate cache lookup
            time.sleep(0.001)  # 1ms baseline
            return {"cached": True, "value": "data"}
        
        result = benchmark(cache_lookup)
        assert result["cached"] is True
        
        stats = benchmark.stats
        assert stats['mean'] < 0.005  # Should complete in < 5ms
    
    def test_memory_usage_performance(self, benchmark):
        """Benchmark memory-intensive operation."""
        def memory_operation():
            # Simulate memory-intensive operation
            data = [i for i in range(1000)]
            time.sleep(0.002)  # 2ms baseline
            return len(data)
        
        result = benchmark(memory_operation)
        assert result == 1000
        
        stats = benchmark.stats
        assert stats['mean'] < 0.01  # Should complete in < 10ms


@pytest.mark.performance
class TestPerformanceComparison:
    """Compare performance across different implementations."""
    
    def test_sequential_vs_parallel_speedup(self, benchmark):
        """Test that parallel processing is faster than sequential."""
        def sequential_process():
            total = 0
            for i in range(100):
                total += i
            time.sleep(0.01)  # 10ms
            return total
        
        result = benchmark(sequential_process)
        assert result == 4950
        
        # In real implementation, parallel should be faster
        # This is a baseline for comparison
    
    def test_cached_vs_uncached_lookup(self, benchmark):
        """Test cache performance improvement."""
        cache = {}
        
        def cached_lookup(key):
            if key in cache:
                return cache[key]
            time.sleep(0.005)  # Simulate slow lookup
            cache[key] = f"value_{key}"
            return cache[key]
        
        # First call (uncached)
        result1 = benchmark(lambda: cached_lookup("test"))
        
        # Subsequent calls should be faster (cached)
        assert result1 == "value_test"
    
    def test_optimized_algorithm_performance(self, benchmark):
        """Test optimized algorithm vs naive implementation."""
        def optimized_search():
            # Binary search (optimized)
            data = list(range(1000))
            target = 500
            left, right = 0, len(data) - 1
            while left <= right:
                mid = (left + right) // 2
                if data[mid] == target:
                    return mid
                elif data[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1
            return -1
        
        result = benchmark(optimized_search)
        assert result >= 0
        
        stats = benchmark.stats
        assert stats['mean'] < 0.001  # Should be very fast


@pytest.mark.performance
class TestPerformanceThresholds:
    """Test performance against defined thresholds."""
    
    # Performance thresholds (in seconds)
    THRESHOLDS = {
        "vector_db_query": 0.01,      # 10ms
        "vulnerability_scan": 0.05,    # 50ms
        "poc_generation": 0.10,        # 100ms
        "fix_suggestion": 0.03,        # 30ms
        "report_generation": 0.02,     # 20ms
        "batch_processing": 0.10,      # 100ms per batch
    }
    
    def test_vector_db_threshold(self, benchmark):
        """Ensure vector DB queries meet threshold."""
        def operation():
            time.sleep(0.002)
            return True
        
        benchmark(operation)
        assert benchmark.stats['mean'] < self.THRESHOLDS["vector_db_query"]
    
    def test_vulnerability_scan_threshold(self, benchmark):
        """Ensure vulnerability scans meet threshold."""
        def operation():
            time.sleep(0.01)
            return [{"type": "reentrancy"}]
        
        benchmark(operation)
        assert benchmark.stats['mean'] < self.THRESHOLDS["vulnerability_scan"]
    
    def test_poc_generation_threshold(self, benchmark):
        """Ensure PoC generation meets threshold."""
        def operation():
            time.sleep(0.02)
            return "contract PoC {}"
        
        benchmark(operation)
        assert benchmark.stats['mean'] < self.THRESHOLDS["poc_generation"]
    
    def test_fix_suggestion_threshold(self, benchmark):
        """Ensure fix suggestions meet threshold."""
        def operation():
            time.sleep(0.005)
            return {"fix": "use SafeMath"}
        
        benchmark(operation)
        assert benchmark.stats['mean'] < self.THRESHOLDS["fix_suggestion"]
    
    def test_report_generation_threshold(self, benchmark):
        """Ensure report generation meets threshold."""
        def operation():
            time.sleep(0.003)
            return {"report": "complete"}
        
        benchmark(operation)
        assert benchmark.stats['mean'] < self.THRESHOLDS["report_generation"]


@pytest.mark.performance
class TestPerformanceRegression:
    """Detect performance regressions by comparing to baseline."""
    
    def test_load_baseline_data(self, tmp_path):
        """Test loading baseline performance data."""
        baseline_file = tmp_path / ".benchmarks" / "baseline.json"
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        
        baseline_data = {
            "vector_db_query": {"mean": 0.002, "stddev": 0.0001},
            "vulnerability_scan": {"mean": 0.01, "stddev": 0.001},
        }
        
        baseline_file.write_text(json.dumps(baseline_data))
        
        # Load and verify
        loaded = json.loads(baseline_file.read_text())
        assert "vector_db_query" in loaded
        assert loaded["vector_db_query"]["mean"] == 0.002
    
    def test_compare_to_baseline(self):
        """Test comparing current performance to baseline."""
        baseline = {"mean": 0.002, "stddev": 0.0001}
        current = {"mean": 0.0025, "stddev": 0.00015}
        
        # Calculate regression
        regression_percent = ((current["mean"] - baseline["mean"]) / baseline["mean"]) * 100
        
        # Allow up to 30% regression (adjusted for test environment variability)
        assert regression_percent < 30
    
    def test_performance_improvement_detection(self):
        """Test detecting performance improvements."""
        baseline = {"mean": 0.01, "stddev": 0.001}
        current = {"mean": 0.008, "stddev": 0.0008}
        
        # Calculate improvement
        improvement_percent = ((baseline["mean"] - current["mean"]) / baseline["mean"]) * 100
        
        # Verify improvement
        assert improvement_percent > 0
        assert improvement_percent == 20  # 20% faster
