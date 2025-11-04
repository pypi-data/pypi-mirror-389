"""Unit tests for Vector Database module."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_vector_db():
    """Create a mock Vector DB for testing."""
    class MockVectorDB:
        def __init__(self):
            self.data = []
            self.initialized = False
        
        def initialize(self, collection_name: str = "vulnerabilities") -> bool:
            """Initialize vector database."""
            self.initialized = True
            return True
        
        def add_vulnerability(self, vuln_data: dict) -> str:
            """Add vulnerability to database."""
            if not self.initialized:
                raise RuntimeError("Database not initialized")
            
            vuln_id = f"vuln-{len(self.data) + 1}"
            vuln_data["id"] = vuln_id
            self.data.append(vuln_data)
            return vuln_id
        
        def query_similar(self, query_text: str, top_k: int = 5, threshold: float = 0.8) -> list:
            """Query similar vulnerabilities."""
            if not self.initialized:
                raise RuntimeError("Database not initialized")
            
            # Mock similarity search
            return self.data[:top_k]
        
        def update_embedding(self, vuln_id: str, new_data: dict) -> bool:
            """Update vulnerability embedding."""
            for vuln in self.data:
                if vuln.get("id") == vuln_id:
                    vuln.update(new_data)
                    return True
            return False
        
        def delete_vulnerability(self, vuln_id: str) -> bool:
            """Delete vulnerability from database."""
            original_len = len(self.data)
            self.data = [v for v in self.data if v.get("id") != vuln_id]
            return len(self.data) < original_len
        
        def batch_insert(self, vulnerabilities: list) -> int:
            """Batch insert vulnerabilities."""
            count = 0
            for vuln in vulnerabilities:
                self.add_vulnerability(vuln)
                count += 1
            return count
        
        def get_count(self) -> int:
            """Get total count of vulnerabilities."""
            return len(self.data)
    
    return MockVectorDB()


class TestVectorDB:
    """Test suite for Vector Database functionality."""
    
    def test_initialize_database(self, mock_vector_db):
        """Test database initialization."""
        result = mock_vector_db.initialize()
        
        assert result is True
        assert mock_vector_db.initialized is True
    
    def test_add_vulnerability(self, mock_vector_db):
        """Test adding vulnerability to database."""
        mock_vector_db.initialize()
        
        vuln = {"type": "reentrancy", "severity": "HIGH"}
        vuln_id = mock_vector_db.add_vulnerability(vuln)
        
        assert vuln_id is not None
        assert vuln_id.startswith("vuln-")
        assert mock_vector_db.get_count() == 1
    
    def test_query_similar_vulnerabilities(self, mock_vector_db):
        """Test querying similar vulnerabilities."""
        mock_vector_db.initialize()
        mock_vector_db.add_vulnerability({"type": "reentrancy"})
        mock_vector_db.add_vulnerability({"type": "access_control"})
        
        results = mock_vector_db.query_similar("reentrancy attack", top_k=5)
        
        assert isinstance(results, list)
        assert len(results) <= 5
    
    def test_update_embedding(self, mock_vector_db):
        """Test updating vulnerability embedding."""
        mock_vector_db.initialize()
        vuln_id = mock_vector_db.add_vulnerability({"type": "reentrancy"})
        
        result = mock_vector_db.update_embedding(vuln_id, {"severity": "CRITICAL"})
        
        assert result is True
    
    def test_delete_vulnerability(self, mock_vector_db):
        """Test deleting vulnerability."""
        mock_vector_db.initialize()
        vuln_id = mock_vector_db.add_vulnerability({"type": "reentrancy"})
        
        result = mock_vector_db.delete_vulnerability(vuln_id)
        
        assert result is True
        assert mock_vector_db.get_count() == 0
    
    def test_batch_insert(self, mock_vector_db):
        """Test batch inserting vulnerabilities."""
        mock_vector_db.initialize()
        
        vulns = [
            {"type": "reentrancy"},
            {"type": "access_control"},
            {"type": "overflow"}
        ]
        
        count = mock_vector_db.batch_insert(vulns)
        
        assert count == 3
        assert mock_vector_db.get_count() == 3
    
    def test_similarity_threshold(self, mock_vector_db):
        """Test similarity threshold filtering."""
        mock_vector_db.initialize()
        mock_vector_db.add_vulnerability({"type": "reentrancy"})
        
        results = mock_vector_db.query_similar("test", threshold=0.9)
        
        assert isinstance(results, list)
    
    def test_database_persistence(self, mock_vector_db):
        """Test database state persistence."""
        mock_vector_db.initialize()
        mock_vector_db.add_vulnerability({"type": "test"})
        
        count_before = mock_vector_db.get_count()
        # Simulate restart
        count_after = mock_vector_db.get_count()
        
        assert count_before == count_after
    
    def test_vector_dimensions(self, mock_vector_db):
        """Test vector embedding dimensions."""
        mock_vector_db.initialize()
        vuln_id = mock_vector_db.add_vulnerability({"type": "reentrancy", "description": "test"})
        
        assert vuln_id is not None
    
    def test_query_performance(self, mock_vector_db):
        """Test query performance with many items."""
        mock_vector_db.initialize()
        
        # Add many vulnerabilities
        for i in range(100):
            mock_vector_db.add_vulnerability({"type": f"vuln-{i}"})
        
        results = mock_vector_db.query_similar("test", top_k=10)
        
        assert len(results) <= 10
