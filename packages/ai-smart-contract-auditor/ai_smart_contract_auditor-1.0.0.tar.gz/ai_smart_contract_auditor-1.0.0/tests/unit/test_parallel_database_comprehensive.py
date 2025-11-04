"""
Comprehensive tests for src/parallel/parallel_database.py
Target: Increase coverage from 17.33% to 75%+
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
import json

from src.parallel.parallel_database import (
    ParallelVulnerabilityDB,
    ParallelPoCDatabase
)
from src.parallel.parallel_processor import ParallelTask, ParallelResult


class TestParallelVulnerabilityDB:
    """Tests for ParallelVulnerabilityDB class"""
    
    @pytest.fixture
    def mock_db_path(self, tmp_path):
        """Create temporary database path"""
        db_path = tmp_path / "test_db"
        db_path.mkdir()
        return str(db_path)
    
    @pytest.fixture
    def vuln_db(self, mock_db_path):
        """Create ParallelVulnerabilityDB instance"""
        return ParallelVulnerabilityDB(db_path=mock_db_path, max_workers=4)
    
    def test_init(self, mock_db_path):
        """Test database initialization"""
        db = ParallelVulnerabilityDB(db_path=mock_db_path, max_workers=4)
        assert db.db_path == mock_db_path
        assert db.processor is not None
        assert db._db_client is None
    
    @patch('src.parallel.parallel_database.ParallelProcessor.execute')
    def test_batch_search_success(self, mock_execute, vuln_db):
        """Test successful batch search"""
        # Mock successful results
        mock_execute.return_value = [
            ParallelResult(
                task_id="search_0",
                success=True,
                result=[{"id": "1", "document": "test"}],
                execution_time=0.5,
                metadata={"query_text": "reentrancy"}
            ),
            ParallelResult(
                task_id="search_1",
                success=True,
                result=[{"id": "2", "document": "test2"}],
                execution_time=0.6,
                metadata={"query_text": "overflow"}
            )
        ]
        
        queries = ["reentrancy", "overflow"]
        results = vuln_db.batch_search(queries, n_results=5)
        
        assert len(results) == 2
        assert results[0]["query"] == "reentrancy"
        assert results[0]["success"] is True
        assert results[0]["count"] == 1
        assert results[1]["query"] == "overflow"
        assert results[1]["success"] is True
        assert results[1]["count"] == 1
    
    @patch('src.parallel.parallel_database.ParallelProcessor.execute')
    def test_batch_search_failure(self, mock_execute, vuln_db):
        """Test batch search with failures"""
        mock_execute.return_value = [
            ParallelResult(
                task_id="search_0",
                success=False,
                result=None,
                execution_time=0.5,
                error="Database error",
                metadata={"query_text": "reentrancy"}
            )
        ]
        
        results = vuln_db.batch_search(["reentrancy"], n_results=5)
        
        assert len(results) == 1
        assert results[0]["success"] is False
        assert results[0]["results"] == []
        assert results[0]["count"] == 0
    
    @patch('chromadb.PersistentClient')
    def test_execute_search_success(self, mock_client_class, mock_db_path):
        """Test single search execution"""
        # Mock ChromaDB client
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"type": "reentrancy"}, {"type": "overflow"}]],
            "distances": [[0.1, 0.2]]
        }
        
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        search_data = {
            "query": "reentrancy vulnerability",
            "n_results": 5,
            "db_path": mock_db_path
        }
        
        results = ParallelVulnerabilityDB._execute_search(search_data)
        
        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["document"] == "doc1"
        assert results[0]["metadata"]["type"] == "reentrancy"
        assert results[0]["distance"] == 0.1
    
    @patch('chromadb.PersistentClient')
    def test_execute_search_empty_results(self, mock_client_class, mock_db_path):
        """Test search with no results"""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]]
        }
        
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        search_data = {
            "query": "nonexistent",
            "n_results": 5,
            "db_path": mock_db_path
        }
        
        results = ParallelVulnerabilityDB._execute_search(search_data)
        assert results == []
    
    @patch('chromadb.PersistentClient')
    def test_execute_search_error(self, mock_client_class, mock_db_path):
        """Test search error handling"""
        mock_client_class.side_effect = Exception("Database connection failed")
        
        search_data = {
            "query": "test",
            "n_results": 5,
            "db_path": mock_db_path
        }
        
        with pytest.raises(Exception, match="Database connection failed"):
            ParallelVulnerabilityDB._execute_search(search_data)
    
    @patch('src.parallel.parallel_database.ParallelProcessor.execute')
    def test_batch_filter_success(self, mock_execute, vuln_db):
        """Test successful batch filter"""
        mock_execute.return_value = [
            ParallelResult(
                task_id="filter_0",
                success=True,
                result=[{"id": "1", "type": "reentrancy"}],
                execution_time=0.3,
                metadata={"filter_desc": "{'severity': 'high'}"}
            )
        ]
        
        filters = [{"severity": "high"}]
        results = vuln_db.batch_filter(filters, limit=10)
        
        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["count"] == 1
    
    @patch('chromadb.PersistentClient')
    def test_execute_filter_success(self, mock_client_class, mock_db_path):
        """Test single filter execution"""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "documents": ["doc1", "doc2"],
            "metadatas": [{"severity": "high"}, {"severity": "high"}]
        }
        
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        filter_data = {
            "filter": {"severity": "high"},
            "limit": 10,
            "db_path": mock_db_path
        }
        
        results = ParallelVulnerabilityDB._execute_filter(filter_data)
        
        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["metadata"]["severity"] == "high"
    
    @patch('chromadb.PersistentClient')
    def test_execute_filter_empty(self, mock_client_class, mock_db_path):
        """Test filter with no results"""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": [],
            "documents": []
        }
        
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        filter_data = {
            "filter": {"severity": "critical"},
            "limit": 10,
            "db_path": mock_db_path
        }
        
        results = ParallelVulnerabilityDB._execute_filter(filter_data)
        assert results == []
    
    @patch('chromadb.PersistentClient')
    def test_execute_filter_error(self, mock_client_class, mock_db_path):
        """Test filter error handling"""
        mock_client_class.side_effect = Exception("Filter failed")
        
        filter_data = {
            "filter": {"severity": "high"},
            "limit": 10,
            "db_path": mock_db_path
        }
        
        with pytest.raises(Exception, match="Filter failed"):
            ParallelVulnerabilityDB._execute_filter(filter_data)


class TestParallelPoCDatabase:
    """Tests for ParallelPoCDatabase class"""
    
    @pytest.fixture
    def mock_poc_dir(self, tmp_path):
        """Create temporary PoC directory"""
        poc_dir = tmp_path / "pocs"
        poc_dir.mkdir()
        return str(tmp_path)
    
    @pytest.fixture
    def poc_db(self, mock_poc_dir):
        """Create ParallelPoCDatabase instance"""
        return ParallelPoCDatabase(poc_dir=mock_poc_dir, max_workers=4)
    
    def test_init(self, mock_poc_dir):
        """Test PoC database initialization"""
        db = ParallelPoCDatabase(poc_dir=mock_poc_dir, max_workers=4)
        assert db.poc_dir == mock_poc_dir
        assert db.processor is not None
    
    @patch('src.parallel.parallel_database.ParallelProcessor.execute')
    def test_batch_load_pocs_success(self, mock_execute, poc_db):
        """Test successful batch PoC loading"""
        mock_execute.return_value = [
            ParallelResult(
                task_id="load_poc_1",
                success=True,
                result={"poc_id": "1", "code": "contract Test {}"},
                execution_time=0.1
            ),
            ParallelResult(
                task_id="load_poc_2",
                success=True,
                result={"poc_id": "2", "code": "contract Test2 {}"},
                execution_time=0.1
            )
        ]
        
        poc_ids = ["1", "2"]
        results = poc_db.batch_load_pocs(poc_ids)
        
        assert len(results) == 2
        assert results[0]["poc_id"] == "1"
        assert results[1]["poc_id"] == "2"
    
    @patch('src.parallel.parallel_database.ParallelProcessor.execute')
    def test_batch_load_pocs_with_failures(self, mock_execute, poc_db):
        """Test batch loading with some failures"""
        mock_execute.return_value = [
            ParallelResult(
                task_id="load_poc_1",
                success=True,
                result={"poc_id": "1", "code": "contract Test {}"},
                execution_time=0.1
            ),
            ParallelResult(
                task_id="load_poc_2",
                success=False,
                result=None,
                execution_time=0.1,
                error="File not found"
            )
        ]
        
        results = poc_db.batch_load_pocs(["1", "2"])
        assert len(results) == 1  # Only successful ones
        assert results[0]["poc_id"] == "1"
    
    def test_load_single_poc_success(self, tmp_path):
        """Test loading a single PoC file"""
        # Create PoC file
        poc_dir = tmp_path
        pocs_dir = poc_dir / "pocs"
        pocs_dir.mkdir()
        poc_file = pocs_dir / "test_poc.sol"
        poc_file.write_text("contract TestPoC { function exploit() public {} }")
        
        poc_data = {
            "poc_id": "test_poc",
            "poc_dir": str(poc_dir)
        }
        
        result = ParallelPoCDatabase._load_single_poc(poc_data)
        
        assert result["poc_id"] == "test_poc"
        assert "contract TestPoC" in result["code"]
        assert result["language"] == "solidity"
        assert "test_poc.sol" in result["file_path"]
    
    def test_load_single_poc_not_found(self, tmp_path):
        """Test loading non-existent PoC"""
        poc_data = {
            "poc_id": "nonexistent",
            "poc_dir": str(tmp_path)
        }
        
        result = ParallelPoCDatabase._load_single_poc(poc_data)
        
        assert result["poc_id"] == "nonexistent"
        assert "error" in result
        assert "not found" in result["error"]
    
    def test_load_single_poc_read_error(self, tmp_path):
        """Test PoC loading with read error"""
        # Create directory but not file
        pocs_dir = tmp_path / "pocs"
        pocs_dir.mkdir()
        
        poc_data = {
            "poc_id": "error_poc",
            "poc_dir": str(tmp_path)
        }
        
        result = ParallelPoCDatabase._load_single_poc(poc_data)
        assert "error" in result
    
    @patch('src.parallel.parallel_database.ParallelProcessor.execute')
    def test_batch_analyze_pocs(self, mock_execute, poc_db):
        """Test batch PoC analysis"""
        mock_execute.return_value = [
            ParallelResult(
                task_id="analyze_poc_0",
                success=True,
                result={
                    "total_lines": 10,
                    "has_test_function": True,
                    "has_exploit": True
                },
                execution_time=0.2
            )
        ]
        
        poc_codes = ["contract Test { function testExploit() {} }"]
        results = poc_db.batch_analyze_pocs(poc_codes)
        
        assert len(results) == 1
        assert results[0]["total_lines"] == 10
        assert results[0]["has_test_function"] is True
    
    def test_analyze_single_poc(self):
        """Test single PoC analysis"""
        poc_code = """
        contract TestPoC {
            function testExploit() public {
                // exploit code
                assert(balance > 0);
            }
        }
        """
        
        result = ParallelPoCDatabase._analyze_single_poc(poc_code)
        
        assert result["total_lines"] > 0
        assert result["has_test_function"] is True
        assert result["has_exploit"] is True
        assert result["has_assertions"] is True
    
    def test_analyze_single_poc_minimal(self):
        """Test analysis of minimal PoC"""
        poc_code = "contract Empty {}"
        
        result = ParallelPoCDatabase._analyze_single_poc(poc_code)
        
        assert result["total_lines"] == 1
        assert result["has_test_function"] is False
        assert result["has_exploit"] is False
        assert result["has_assertions"] is False


class TestIntegration:
    """Integration tests for parallel database operations"""
    
    @pytest.mark.integration
    def test_vulnerability_db_end_to_end(self, tmp_path):
        """Test complete vulnerability DB workflow"""
        db_path = tmp_path / "vuln_db"
        db_path.mkdir()
        
        db = ParallelVulnerabilityDB(db_path=str(db_path), max_workers=2)
        
        # Test that database is initialized
        assert db.db_path == str(db_path)
        assert db.processor.max_workers == 2
    
    @pytest.mark.integration
    def test_poc_db_end_to_end(self, tmp_path):
        """Test complete PoC DB workflow"""
        # Create PoC files
        pocs_dir = tmp_path / "pocs"
        pocs_dir.mkdir()
        
        for i in range(3):
            poc_file = pocs_dir / f"poc_{i}.sol"
            poc_file.write_text(f"contract PoC{i} {{ function testExploit() public {{}} }}")
        
        db = ParallelPoCDatabase(poc_dir=str(tmp_path), max_workers=2)
        
        # Load PoCs
        poc_ids = ["poc_0", "poc_1", "poc_2"]
        results = db.batch_load_pocs(poc_ids)
        
        # Should load all successfully
        assert len(results) == 3
        for result in results:
            assert "code" in result
            assert "contract PoC" in result["code"]
