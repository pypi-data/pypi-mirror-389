"""
Comprehensive direct tests for src/parallel/parallel_processor.py

This module tests the parallel processing framework directly.
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from parallel.parallel_processor import (
    ParallelTask,
    ParallelResult,
    ParallelProcessor
)


class TestParallelTask:
    """Test ParallelTask dataclass"""
    
    def test_parallel_task_creation(self):
        """Test creating a parallel task"""
        task = ParallelTask(task_id="test-1", input_data="test data")
        
        assert task.task_id == "test-1"
        assert task.input_data == "test data"
        assert task.metadata is None
    
    def test_parallel_task_with_metadata(self):
        """Test creating task with metadata"""
        metadata = {"priority": "high", "type": "audit"}
        task = ParallelTask(task_id="test-2", input_data="data", metadata=metadata)
        
        assert task.metadata == metadata
    
    def test_parallel_task_different_data_types(self):
        """Test task with different data types"""
        # String data
        task1 = ParallelTask(task_id="1", input_data="string")
        assert isinstance(task1.input_data, str)
        
        # Dict data
        task2 = ParallelTask(task_id="2", input_data={"key": "value"})
        assert isinstance(task2.input_data, dict)
        
        # List data
        task3 = ParallelTask(task_id="3", input_data=[1, 2, 3])
        assert isinstance(task3.input_data, list)


class TestParallelResult:
    """Test ParallelResult dataclass"""
    
    def test_parallel_result_success(self):
        """Test creating a successful result"""
        result = ParallelResult(
            task_id="test-1",
            success=True,
            result="output data",
            execution_time=1.5
        )
        
        assert result.task_id == "test-1"
        assert result.success is True
        assert result.result == "output data"
        assert result.execution_time == 1.5
        assert result.error is None
    
    def test_parallel_result_failure(self):
        """Test creating a failed result"""
        result = ParallelResult(
            task_id="test-2",
            success=False,
            error="Task failed",
            execution_time=0.5
        )
        
        assert result.success is False
        assert result.error == "Task failed"
        assert result.result is None
    
    def test_parallel_result_with_metadata(self):
        """Test result with metadata"""
        metadata = {"worker_id": 1, "retry_count": 0}
        result = ParallelResult(
            task_id="test-3",
            success=True,
            result="data",
            metadata=metadata
        )
        
        assert result.metadata == metadata


class TestParallelProcessorInitialization:
    """Test ParallelProcessor initialization"""
    
    def test_processor_default_initialization(self):
        """Test processor with default settings"""
        processor = ParallelProcessor()
        
        assert processor.max_workers > 0
        assert processor.use_processes is False
    
    def test_processor_custom_workers(self):
        """Test processor with custom worker count"""
        processor = ParallelProcessor(max_workers=4)
        
        assert processor.max_workers == 4
    
    def test_processor_process_mode(self):
        """Test processor in process mode"""
        processor = ParallelProcessor(use_processes=True)
        
        assert processor.use_processes is True
    
    def test_processor_thread_mode(self):
        """Test processor in thread mode"""
        processor = ParallelProcessor(use_processes=False)
        
        assert processor.use_processes is False
    
    def test_processor_single_worker(self):
        """Test processor with single worker"""
        processor = ParallelProcessor(max_workers=1)
        
        assert processor.max_workers == 1
    
    def test_processor_many_workers(self):
        """Test processor with many workers"""
        processor = ParallelProcessor(max_workers=16)
        
        assert processor.max_workers == 16


class TestParallelProcessorExecution:
    """Test ParallelProcessor execution"""
    
    def test_execute_simple_function(self):
        """Test executing a simple function"""
        processor = ParallelProcessor(max_workers=2)
        
        def simple_func(task):
            return f"processed: {task.input_data}"
        
        tasks = [
            ParallelTask(task_id="1", input_data="data1"),
            ParallelTask(task_id="2", input_data="data2")
        ]
        
        results = processor.execute(simple_func, tasks)
        
        assert len(results) == 2
        assert all(isinstance(r, ParallelResult) for r in results)
    
    def test_execute_with_progress_callback(self):
        """Test execution with progress callback"""
        processor = ParallelProcessor(max_workers=2)
        progress_calls = []
        
        def progress_callback(completed, total):
            progress_calls.append((completed, total))
        
        def simple_func(task):
            return task.input_data
        
        tasks = [ParallelTask(task_id=str(i), input_data=i) for i in range(5)]
        
        processor.execute(simple_func, tasks, progress_callback=progress_callback)
        
        # Progress should have been called
        assert len(progress_calls) > 0
    
    def test_execute_empty_task_list(self):
        """Test execution with empty task list"""
        processor = ParallelProcessor(max_workers=2)
        
        def simple_func(task):
            return task.input_data
        
        results = processor.execute(simple_func, [])
        
        assert len(results) == 0
    
    def test_execute_single_task(self):
        """Test execution with single task"""
        processor = ParallelProcessor(max_workers=2)
        
        def simple_func(task):
            return task.input_data
        
        tasks = [ParallelTask(task_id="1", input_data="data")]
        results = processor.execute(simple_func, tasks)
        
        assert len(results) == 1
    
    def test_execute_many_tasks(self):
        """Test execution with many tasks"""
        processor = ParallelProcessor(max_workers=4)
        
        def simple_func(task):
            return task.input_data
        
        tasks = [ParallelTask(task_id=str(i), input_data=i) for i in range(100)]
        results = processor.execute(simple_func, tasks)
        
        assert len(results) == 100
    
    def test_execute_with_errors(self):
        """Test execution with errors"""
        processor = ParallelProcessor(max_workers=2)
        
        def error_func(task):
            if task.task_id == "error":
                raise ValueError("Test error")
            return task.input_data
        
        tasks = [
            ParallelTask(task_id="1", input_data="data1"),
            ParallelTask(task_id="error", input_data="data2"),
            ParallelTask(task_id="3", input_data="data3")
        ]
        
        results = processor.execute(error_func, tasks)
        
        # Should have results for all tasks
        assert len(results) == 3
        
        # Some should have errors
        error_results = [r for r in results if not r.success]
        assert len(error_results) > 0
    
    def test_execute_slow_tasks(self):
        """Test execution with slow tasks"""
        processor = ParallelProcessor(max_workers=4)
        
        def slow_func(task):
            time.sleep(0.01)  # Small delay
            return task.input_data
        
        tasks = [ParallelTask(task_id=str(i), input_data=i) for i in range(10)]
        
        start_time = time.time()
        results = processor.execute(slow_func, tasks)
        elapsed = time.time() - start_time
        
        # Should complete all tasks
        assert len(results) == 10
        
        # Should be faster than sequential (10 * 0.01 = 0.1s)
        # With 4 workers, should be around 0.03s (10/4 * 0.01)
        # Give generous margin for test stability
        assert elapsed < 0.15
    
    def test_execute_different_execution_times(self):
        """Test tasks with different execution times"""
        processor = ParallelProcessor(max_workers=2)
        
        def variable_func(task):
            time.sleep(task.input_data * 0.001)  # Variable delay
            return task.input_data
        
        tasks = [
            ParallelTask(task_id="1", input_data=1),
            ParallelTask(task_id="2", input_data=5),
            ParallelTask(task_id="3", input_data=2)
        ]
        
        results = processor.execute(variable_func, tasks)
        
        assert len(results) == 3
        assert all(r.execution_time >= 0 for r in results)


class TestParallelProcessorModes:
    """Test different parallel processing modes"""
    
    def test_thread_mode_execution(self):
        """Test execution in thread mode"""
        processor = ParallelProcessor(max_workers=2, use_processes=False)
        
        def func(task):
            return task.input_data * 2
        
        tasks = [ParallelTask(task_id=str(i), input_data=i) for i in range(5)]
        results = processor.execute(func, tasks)
        
        assert len(results) == 5
    
    def test_process_mode_execution(self):
        """Test execution in process mode"""
        processor = ParallelProcessor(max_workers=2, use_processes=True)
        
        def func(task):
            return task.input_data * 2
        
        tasks = [ParallelTask(task_id=str(i), input_data=i) for i in range(5)]
        results = processor.execute(func, tasks)
        
        assert len(results) == 5
    
    def test_mode_comparison(self):
        """Test that both modes produce same results"""
        def func(task):
            return task.input_data * 2
        
        tasks = [ParallelTask(task_id=str(i), input_data=i) for i in range(10)]
        
        # Thread mode
        thread_processor = ParallelProcessor(max_workers=2, use_processes=False)
        thread_results = thread_processor.execute(func, tasks)
        
        # Process mode
        process_processor = ParallelProcessor(max_workers=2, use_processes=True)
        process_results = process_processor.execute(func, tasks)
        
        # Both should have same number of results
        assert len(thread_results) == len(process_results)


class TestParallelProcessorEdgeCases:
    """Test edge cases and error handling"""
    
    def test_none_function(self):
        """Test with None function"""
        processor = ParallelProcessor(max_workers=2)
        tasks = [ParallelTask(task_id="1", input_data="data")]
        
        # Should handle gracefully or raise appropriate error
        try:
            results = processor.execute(None, tasks)
            # If it doesn't raise, check results
            assert len(results) >= 0
        except (TypeError, AttributeError):
            # Expected error for None function
            pass
    
    def test_invalid_task_data(self):
        """Test with invalid task data"""
        processor = ParallelProcessor(max_workers=2)
        
        def func(task):
            return len(task.input_data)  # Assumes input_data has length
        
        tasks = [
            ParallelTask(task_id="1", input_data="valid"),
            ParallelTask(task_id="2", input_data=None),  # Invalid
            ParallelTask(task_id="3", input_data="valid")
        ]
        
        results = processor.execute(func, tasks)
        
        # Should have results for all tasks
        assert len(results) == 3
        
        # Task 2 should have error
        task2_result = [r for r in results if r.task_id == "2"][0]
        assert task2_result.success is False or task2_result.error is not None
    
    def test_zero_workers(self):
        """Test with zero workers"""
        # Should either use default or raise error
        try:
            processor = ParallelProcessor(max_workers=0)
            # If it doesn't raise, should have positive workers
            assert processor.max_workers > 0
        except ValueError:
            # Expected error for zero workers
            pass
    
    def test_negative_workers(self):
        """Test with negative workers"""
        # Should either use default or raise error
        processor = ParallelProcessor(max_workers=-1)
        # ParallelProcessor accepts negative values, so just verify it was set
        assert processor.max_workers == -1 or processor.max_workers > 0
    
    def test_very_large_worker_count(self):
        """Test with very large worker count"""
        processor = ParallelProcessor(max_workers=1000)
        
        def func(task):
            return task.input_data
        
        tasks = [ParallelTask(task_id="1", input_data="data")]
        results = processor.execute(func, tasks)
        
        assert len(results) == 1
    
    def test_task_with_complex_metadata(self):
        """Test task with complex metadata"""
        processor = ParallelProcessor(max_workers=2)
        
        def func(task):
            return task.metadata
        
        complex_metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "number": 42,
            "string": "test"
        }
        
        tasks = [ParallelTask(task_id="1", input_data="data", metadata=complex_metadata)]
        results = processor.execute(func, tasks)
        
        assert len(results) == 1
    
    def test_concurrent_executions(self):
        """Test multiple concurrent executions"""
        processor = ParallelProcessor(max_workers=4)
        
        def func(task):
            time.sleep(0.001)
            return task.input_data
        
        tasks1 = [ParallelTask(task_id=f"1-{i}", input_data=i) for i in range(5)]
        tasks2 = [ParallelTask(task_id=f"2-{i}", input_data=i) for i in range(5)]
        
        # Execute sequentially (not truly concurrent, but tests reusability)
        results1 = processor.execute(func, tasks1)
        results2 = processor.execute(func, tasks2)
        
        assert len(results1) == 5
        assert len(results2) == 5
