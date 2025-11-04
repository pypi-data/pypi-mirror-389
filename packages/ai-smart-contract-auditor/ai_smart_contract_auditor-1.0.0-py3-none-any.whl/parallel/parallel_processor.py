#!/usr/bin/env python3
"""
Parallel Processing Framework for AI Smart Contract Auditor
Provides thread-safe and process-safe parallel execution capabilities
"""

import os
import time
import json
import logging
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from functools import partial
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ParallelTask:
    """Represents a single task for parallel execution"""
    task_id: str
    input_data: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ParallelResult:
    """Represents the result of a parallel task"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class ParallelProcessor:
    """
    Main parallel processing engine
    Supports both thread-based and process-based parallelism
    """
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        Initialize parallel processor
        
        Args:
            max_workers: Maximum number of workers (default: CPU count)
            use_processes: Use ProcessPoolExecutor instead of ThreadPoolExecutor
        """
        self.max_workers = max_workers or cpu_count()
        self.use_processes = use_processes
        self.executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        
        logger.info(f"Initialized ParallelProcessor: {self.max_workers} workers, "
                   f"mode={'processes' if use_processes else 'threads'}")
    
    def execute(
        self,
        func: Callable,
        tasks: List[ParallelTask],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ParallelResult]:
        """
        Execute tasks in parallel
        
        Args:
            func: Function to execute for each task
            tasks: List of tasks to execute
            progress_callback: Optional callback for progress updates (completed, total)
            
        Returns:
            List of ParallelResult objects
        """
        results = []
        total_tasks = len(tasks)
        
        logger.info(f"Starting parallel execution of {total_tasks} tasks")
        start_time = time.time()
        
        with self.executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._execute_task, func, task): task
                for task in tasks
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, total_tasks)
                        
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    results.append(ParallelResult(
                        task_id=task.task_id,
                        success=False,
                        error=str(e)
                    ))
                    completed += 1
        
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        
        logger.info(f"Parallel execution complete: {success_count}/{total_tasks} succeeded "
                   f"in {total_time:.2f}s ({total_tasks/total_time:.2f} tasks/sec)")
        
        return results
    
    @staticmethod
    def _execute_task(func: Callable, task: ParallelTask) -> ParallelResult:
        """Execute a single task and return result"""
        start_time = time.time()
        
        try:
            result = func(task.input_data)
            execution_time = time.time() - start_time
            
            return ParallelResult(
                task_id=task.task_id,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata=task.metadata
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Task {task.task_id} failed after {execution_time:.2f}s: {e}")
            
            return ParallelResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata=task.metadata
            )
    
    def execute_batch(
        self,
        func: Callable,
        inputs: List[Any],
        batch_size: int = 100,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ParallelResult]:
        """
        Execute tasks in batches for better memory management
        
        Args:
            func: Function to execute
            inputs: List of input data
            batch_size: Number of tasks per batch
            progress_callback: Optional progress callback
            
        Returns:
            List of all results
        """
        all_results = []
        total_inputs = len(inputs)
        
        for i in range(0, total_inputs, batch_size):
            batch = inputs[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_inputs + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} tasks)")
            
            tasks = [
                ParallelTask(task_id=f"batch{batch_num}_task{j}", input_data=inp)
                for j, inp in enumerate(batch)
            ]
            
            batch_results = self.execute(func, tasks, progress_callback)
            all_results.extend(batch_results)
        
        return all_results


class ParallelAuditEngine:
    """Parallel execution engine for contract auditing"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.processor = ParallelProcessor(max_workers=max_workers, use_processes=False)
    
    def audit_contracts(self, contract_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Audit multiple contracts in parallel
        
        Args:
            contract_paths: List of contract file paths
            
        Returns:
            List of audit results
        """
        logger.info(f"Starting parallel audit of {len(contract_paths)} contracts")
        
        tasks = [
            ParallelTask(task_id=f"audit_{os.path.basename(path)}", input_data=path)
            for path in contract_paths
        ]
        
        results = self.processor.execute(self._audit_single_contract, tasks)
        
        return [
            {
                "contract": r.task_id,
                "success": r.success,
                "findings": r.result if r.success else [],
                "error": r.error,
                "time": r.execution_time
            }
            for r in results
        ]
    
    @staticmethod
    def _audit_single_contract(contract_path: str) -> Dict[str, Any]:
        """Audit a single contract (placeholder implementation)"""
        # This would call the actual audit logic
        # For now, return a placeholder
        time.sleep(0.1)  # Simulate work
        return {
            "contract": contract_path,
            "vulnerabilities": [],
            "status": "completed"
        }


class ParallelDatabaseQuery:
    """Parallel database query engine"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.processor = ParallelProcessor(max_workers=max_workers, use_processes=False)
    
    def batch_query(self, queries: List[str], db_path: str) -> List[Dict[str, Any]]:
        """
        Execute multiple database queries in parallel
        
        Args:
            queries: List of query strings
            db_path: Path to database
            
        Returns:
            List of query results
        """
        logger.info(f"Executing {len(queries)} queries in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"query_{i}",
                input_data={"query": q, "db_path": db_path}
            )
            for i, q in enumerate(queries)
        ]
        
        results = self.processor.execute(self._execute_query, tasks)
        
        return [
            {
                "query": r.metadata.get("query") if r.metadata else "",
                "success": r.success,
                "results": r.result if r.success else [],
                "error": r.error,
                "time": r.execution_time
            }
            for r in results
        ]
    
    @staticmethod
    def _execute_query(query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a single database query"""
        # Placeholder - would use actual database query logic
        time.sleep(0.05)  # Simulate query
        return []


class ParallelPoCGenerator:
    """Parallel PoC generation engine"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.processor = ParallelProcessor(max_workers=max_workers, use_processes=False)
    
    def generate_pocs(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate PoCs for multiple vulnerabilities in parallel
        
        Args:
            vulnerabilities: List of vulnerability data
            
        Returns:
            List of generated PoCs
        """
        logger.info(f"Generating PoCs for {len(vulnerabilities)} vulnerabilities in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"poc_{vuln.get('id', i)}",
                input_data=vuln,
                metadata={"vulnerability_type": vuln.get("type")}
            )
            for i, vuln in enumerate(vulnerabilities)
        ]
        
        results = self.processor.execute(self._generate_single_poc, tasks)
        
        return [
            {
                "vulnerability_id": r.task_id,
                "success": r.success,
                "poc_code": r.result if r.success else None,
                "error": r.error,
                "time": r.execution_time
            }
            for r in results
        ]
    
    @staticmethod
    def _generate_single_poc(vulnerability: Dict[str, Any]) -> str:
        """Generate PoC for a single vulnerability"""
        # Placeholder - would use actual PoC generation logic
        time.sleep(0.2)  # Simulate PoC generation
        return "// PoC code placeholder"


def progress_printer(completed: int, total: int):
    """Simple progress callback"""
    percentage = (completed / total) * 100
    print(f"Progress: {completed}/{total} ({percentage:.1f}%)")


if __name__ == "__main__":
    # Example usage
    print("=== Parallel Processing Framework Test ===\n")
    
    # Test 1: Basic parallel execution
    print("Test 1: Basic parallel execution")
    processor = ParallelProcessor(max_workers=4)
    
    def square(x):
        time.sleep(0.1)
        return x * x
    
    tasks = [ParallelTask(task_id=f"task_{i}", input_data=i) for i in range(10)]
    results = processor.execute(square, tasks, progress_callback=progress_printer)
    
    print(f"Results: {[r.result for r in results if r.success]}\n")
    
    # Test 2: Parallel audit engine
    print("Test 2: Parallel audit engine")
    audit_engine = ParallelAuditEngine(max_workers=4)
    contracts = ["contract1.sol", "contract2.sol", "contract3.sol"]
    audit_results = audit_engine.audit_contracts(contracts)
    print(f"Audited {len(audit_results)} contracts\n")
    
    # Test 3: Parallel database queries
    print("Test 3: Parallel database queries")
    db_query = ParallelDatabaseQuery(max_workers=4)
    queries = ["reentrancy", "overflow", "access control"]
    query_results = db_query.batch_query(queries, "database/vulnerability_db")
    print(f"Executed {len(query_results)} queries\n")
    
    # Test 4: Parallel PoC generation
    print("Test 4: Parallel PoC generation")
    poc_gen = ParallelPoCGenerator(max_workers=4)
    vulns = [{"id": f"vuln_{i}", "type": "reentrancy"} for i in range(5)]
    poc_results = poc_gen.generate_pocs(vulns)
    print(f"Generated {len(poc_results)} PoCs\n")
    
    print("=== All tests complete ===")
