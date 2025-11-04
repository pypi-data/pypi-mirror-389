#!/usr/bin/env python3
"""
Parallel Database Operations
Enables parallel querying and batch operations on the vulnerability database
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .parallel_processor import ParallelProcessor, ParallelTask

logger = logging.getLogger(__name__)


class ParallelVulnerabilityDB:
    """Parallel operations on vulnerability database"""
    
    def __init__(self, db_path: str, max_workers: int = 8):
        self.db_path = db_path
        self.processor = ParallelProcessor(max_workers=max_workers)
        self._db_client = None
    
    def batch_search(self, queries: List[str], n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute multiple semantic searches in parallel
        
        Args:
            queries: List of search queries
            n_results: Number of results per query
            
        Returns:
            List of search results
        """
        logger.info(f"Executing {len(queries)} database searches in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"search_{i}",
                input_data={"query": q, "n_results": n_results, "db_path": self.db_path},
                metadata={"query_text": q}
            )
            for i, q in enumerate(queries)
        ]
        
        results = self.processor.execute(self._execute_search, tasks)
        
        return [
            {
                "query": r.metadata.get("query_text") if r.metadata else "",
                "success": r.success,
                "results": r.result if r.success else [],
                "count": len(r.result) if r.success and r.result else 0,
                "time": r.execution_time
            }
            for r in results
        ]
    
    @staticmethod
    def _execute_search(search_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a single database search"""
        try:
            import chromadb
            
            query = search_data["query"]
            n_results = search_data["n_results"]
            db_path = search_data["db_path"]
            
            # Create client and get collection
            client = chromadb.PersistentClient(path=db_path)
            collection = client.get_collection("vulnerabilities")
            
            # Execute search
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            if results and results["documents"]:
                return [
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0
                    }
                    for i in range(len(results["documents"][0]))
                ]
            return []
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def batch_filter(
        self,
        filters: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple filtered queries in parallel
        
        Args:
            filters: List of filter dictionaries
            limit: Maximum results per query
            
        Returns:
            List of filtered results
        """
        logger.info(f"Executing {len(filters)} filtered queries in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"filter_{i}",
                input_data={"filter": f, "limit": limit, "db_path": self.db_path},
                metadata={"filter_desc": str(f)}
            )
            for i, f in enumerate(filters)
        ]
        
        results = self.processor.execute(self._execute_filter, tasks)
        
        return [
            {
                "filter": r.metadata.get("filter_desc") if r.metadata else "",
                "success": r.success,
                "results": r.result if r.success else [],
                "count": len(r.result) if r.success and r.result else 0,
                "time": r.execution_time
            }
            for r in results
        ]
    
    @staticmethod
    def _execute_filter(filter_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a single filtered query"""
        try:
            import chromadb
            
            filter_dict = filter_data["filter"]
            limit = filter_data["limit"]
            db_path = filter_data["db_path"]
            
            # Create client and get collection
            client = chromadb.PersistentClient(path=db_path)
            collection = client.get_collection("vulnerabilities")
            
            # Execute filtered query
            results = collection.get(
                where=filter_dict,
                limit=limit
            )
            
            # Format results
            if results and results["documents"]:
                return [
                    {
                        "id": results["ids"][i],
                        "document": results["documents"][i],
                        "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                    }
                    for i in range(len(results["documents"]))
                ]
            return []
            
        except Exception as e:
            logger.error(f"Filter query failed: {e}")
            raise


class ParallelPoCDatabase:
    """Parallel operations on PoC database"""
    
    def __init__(self, poc_dir: str, max_workers: int = 8):
        self.poc_dir = poc_dir
        self.processor = ParallelProcessor(max_workers=max_workers)
    
    def batch_load_pocs(self, poc_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Load multiple PoCs in parallel
        
        Args:
            poc_ids: List of PoC identifiers
            
        Returns:
            List of PoC data
        """
        logger.info(f"Loading {len(poc_ids)} PoCs in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"load_poc_{poc_id}",
                input_data={"poc_id": poc_id, "poc_dir": self.poc_dir},
                metadata={"poc_id": poc_id}
            )
            for poc_id in poc_ids
        ]
        
        results = self.processor.execute(self._load_single_poc, tasks)
        
        return [r.result for r in results if r.success and r.result]
    
    @staticmethod
    def _load_single_poc(poc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load a single PoC from disk"""
        poc_id = poc_data["poc_id"]
        poc_dir = poc_data["poc_dir"]
        
        try:
            # Try to find PoC file
            poc_file = Path(poc_dir) / "pocs" / f"{poc_id}.sol"
            
            if poc_file.exists():
                with open(poc_file, "r") as f:
                    code = f.read()
                
                return {
                    "poc_id": poc_id,
                    "code": code,
                    "language": "solidity",
                    "file_path": str(poc_file)
                }
            else:
                return {
                    "poc_id": poc_id,
                    "error": "PoC file not found"
                }
                
        except Exception as e:
            return {
                "poc_id": poc_id,
                "error": str(e)
            }
    
    def batch_analyze_pocs(self, poc_codes: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple PoCs in parallel
        
        Args:
            poc_codes: List of PoC source codes
            
        Returns:
            List of analysis results
        """
        logger.info(f"Analyzing {len(poc_codes)} PoCs in parallel")
        
        tasks = [
            ParallelTask(
                task_id=f"analyze_poc_{i}",
                input_data=code
            )
            for i, code in enumerate(poc_codes)
        ]
        
        results = self.processor.execute(self._analyze_single_poc, tasks)
        
        return [r.result for r in results if r.success and r.result]
    
    @staticmethod
    def _analyze_single_poc(poc_code: str) -> Dict[str, Any]:
        """Analyze a single PoC"""
        # Extract metadata from PoC code
        lines = poc_code.split("\n")
        
        # Count lines and detect patterns
        total_lines = len(lines)
        has_test_function = any("function test" in line for line in lines)
        has_exploit = any("exploit" in line.lower() for line in lines)
        has_assertions = any("assert" in line for line in lines)
        
        return {
            "total_lines": total_lines,
            "has_test_function": has_test_function,
            "has_exploit": has_exploit,
            "has_assertions": has_assertions,
            "quality_score": sum([has_test_function, has_exploit, has_assertions]) / 3.0
        }


def demo_parallel_database():
    """Demonstrate parallel database operations"""
    print("=== Parallel Database Operations Demo ===\n")
    
    db_path = "database/vulnerability_db"
    
    if not os.path.exists(db_path):
        print("Database not found, skipping demo")
        return
    
    # Demo 1: Parallel searches
    print("1. Parallel Database Searches")
    vuln_db = ParallelVulnerabilityDB(db_path, max_workers=4)
    
    queries = [
        "reentrancy attack",
        "integer overflow",
        "access control",
        "oracle manipulation"
    ]
    
    search_results = vuln_db.batch_search(queries, n_results=3)
    print(f"   Executed {len(search_results)} searches")
    for r in search_results:
        print(f"   - '{r['query']}': {r['count']} results in {r['time']:.3f}s")
    
    print()
    
    # Demo 2: Parallel filters
    print("2. Parallel Filtered Queries")
    
    filters = [
        {"severity": "HIGH"},
        {"severity": "MEDIUM"},
        {"auditor": "Cyfrin"}
    ]
    
    filter_results = vuln_db.batch_filter(filters, limit=5)
    print(f"   Executed {len(filter_results)} filtered queries")
    for r in filter_results:
        print(f"   - Filter {r['filter']}: {r['count']} results in {r['time']:.3f}s")
    
    print()
    
    # Demo 3: PoC database operations
    print("3. Parallel PoC Operations")
    poc_dir = "data/extracted_pocs"
    
    if os.path.exists(poc_dir):
        poc_db = ParallelPoCDatabase(poc_dir, max_workers=4)
        
        # Load PoC metadata
        poc_json = Path(poc_dir) / "all_pocs.json"
        if poc_json.exists():
            with open(poc_json) as f:
                all_pocs = json.load(f)
            
            # Get first 5 PoC IDs
            poc_ids = [p["finding_id"] for p in all_pocs[:5]]
            
            loaded_pocs = poc_db.batch_load_pocs(poc_ids)
            print(f"   Loaded {len(loaded_pocs)} PoCs")
            
            # Analyze loaded PoCs
            if loaded_pocs:
                poc_codes = [p["code"] for p in loaded_pocs if "code" in p]
                analyzed = poc_db.batch_analyze_pocs(poc_codes)
                print(f"   Analyzed {len(analyzed)} PoCs")
                avg_quality = sum(p["quality_score"] for p in analyzed) / len(analyzed) if analyzed else 0
                print(f"   Average quality score: {avg_quality:.2f}")
        else:
            print("   PoC JSON not found")
    else:
        print("   PoC directory not found")
    
    print("\n=== Demo complete ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_parallel_database()
