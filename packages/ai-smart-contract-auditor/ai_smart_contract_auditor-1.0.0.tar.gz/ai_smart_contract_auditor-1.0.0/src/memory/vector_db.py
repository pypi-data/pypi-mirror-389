"""
Vector Database Module for AI Auditor
Manages ChromaDB for storing and retrieving vulnerability patterns,
tool outputs, PoC templates, and audit history.
"""

import chromadb
from chromadb.config import Settings
import os
import json
from typing import List, Dict, Any


class VectorDatabase:
    """Manages the vector database for the AI auditor system"""
    
    def __init__(self, persist_directory: str = "./data/ai_auditor_memory"):
        """
        Initialize the vector database
        
        Args:
            persist_directory: Directory to persist the database
        """
        self.persist_directory = os.path.abspath(persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Create or get collections
        self.vulnerability_collection = self._get_or_create_collection("vulnerability_patterns")
        self.tool_output_collection = self._get_or_create_collection("tool_analysis")
        self.poc_templates_collection = self._get_or_create_collection("poc_templates")
        self.audit_history_collection = self._get_or_create_collection("audit_history")
        
    def _get_or_create_collection(self, name: str):
        """Get or create a collection"""
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(name=name)
    
    def add_vulnerability_pattern(self, 
                                  vuln_id: str,
                                  description: str,
                                  severity: str,
                                  category: str,
                                  swc_id: str = None):
        """
        Add a vulnerability pattern to the database
        
        Args:
            vuln_id: Unique identifier for the vulnerability
            description: Description of the vulnerability
            severity: Severity level (HIGH, MEDIUM, LOW)
            category: Category of vulnerability
            swc_id: Smart Contract Weakness Classification ID
        """
        metadata = {
            "severity": severity,
            "category": category
        }
        if swc_id:
            metadata["swc_id"] = swc_id
            
        self.vulnerability_collection.add(
            ids=[vuln_id],
            documents=[description],
            metadatas=[metadata]
        )
    
    def search_vulnerabilities(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for similar vulnerabilities
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of matching vulnerabilities with metadata
        """
        results = self.vulnerability_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return self._format_results(results)
    
    def add_tool_output(self, 
                       tool_name: str,
                       contract_path: str,
                       output: str,
                       findings: List[Dict]):
        """
        Store tool analysis output
        
        Args:
            tool_name: Name of the tool
            contract_path: Path to analyzed contract
            output: Raw tool output
            findings: List of findings from the tool
        """
        doc_id = f"{tool_name}_{os.path.basename(contract_path)}"
        
        self.tool_output_collection.add(
            ids=[doc_id],
            documents=[output],
            metadatas=[{
                "tool": tool_name,
                "contract": contract_path,
                "findings_count": len(findings)
            }]
        )
    
    def add_poc_template(self,
                        vulnerability_type: str,
                        template_code: str,
                        description: str):
        """
        Add a PoC template to the database
        
        Args:
            vulnerability_type: Type of vulnerability
            template_code: Solidity PoC template code
            description: Description of the template
        """
        self.poc_templates_collection.add(
            ids=[vulnerability_type],
            documents=[template_code],
            metadatas=[{"description": description}]
        )
    
    def get_poc_template(self, vulnerability_type: str) -> str:
        """
        Retrieve a PoC template
        
        Args:
            vulnerability_type: Type of vulnerability
            
        Returns:
            PoC template code
        """
        results = self.poc_templates_collection.get(ids=[vulnerability_type])
        if results and results['documents']:
            return results['documents'][0]
        return None
    
    def add_audit_record(self,
                        audit_id: str,
                        contract_name: str,
                        findings: List[Dict],
                        summary: str):
        """
        Store audit history
        
        Args:
            audit_id: Unique audit identifier
            contract_name: Name of audited contract
            findings: List of findings
            summary: Audit summary
        """
        self.audit_history_collection.add(
            ids=[audit_id],
            documents=[summary],
            metadatas=[{
                "contract": contract_name,
                "findings_count": len(findings),
                "high_severity": sum(1 for f in findings if f.get('severity') == 'HIGH'),
                "medium_severity": sum(1 for f in findings if f.get('severity') == 'MEDIUM'),
                "low_severity": sum(1 for f in findings if f.get('severity') == 'LOW')
            }]
        )
    
    def _format_results(self, results: Dict) -> List[Dict]:
        """Format query results into a list of dictionaries"""
        formatted = []
        if not results or not results.get('ids'):
            return formatted
            
        for i, doc_id in enumerate(results['ids'][0]):
            formatted.append({
                'id': doc_id,
                'document': results['documents'][0][i] if results.get('documents') else None,
                'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                'distance': results['distances'][0][i] if results.get('distances') else None
            })
        
        return formatted
    
    def populate_initial_data(self):
        """Populate database with initial vulnerability patterns"""
        
        # Common vulnerability patterns
        vulnerabilities = [
            {
                "vuln_id": "reentrancy_guard_missing",
                "description": "Missing reentrancy guard on external calls allows recursive execution and potential fund theft",
                "severity": "HIGH",
                "category": "reentrancy",
                "swc_id": "SWC-107"
            },
            {
                "vuln_id": "unchecked_external_call",
                "description": "Unchecked return value from external call can lead to silent failures",
                "severity": "MEDIUM",
                "category": "unchecked_calls",
                "swc_id": "SWC-104"
            },
            {
                "vuln_id": "integer_overflow",
                "description": "Integer overflow in arithmetic operations can lead to unexpected behavior",
                "severity": "HIGH",
                "category": "arithmetic",
                "swc_id": "SWC-101"
            },
            {
                "vuln_id": "access_control_missing",
                "description": "Missing access control on critical functions allows unauthorized access",
                "severity": "HIGH",
                "category": "access_control",
                "swc_id": "SWC-105"
            },
            {
                "vuln_id": "front_running_predictable",
                "description": "Predictable transaction ordering enables front-running attacks",
                "severity": "MEDIUM",
                "category": "front_running",
                "swc_id": "SWC-114"
            },
            {
                "vuln_id": "oracle_manipulation",
                "description": "Price oracle can be manipulated through flash loans or market manipulation",
                "severity": "HIGH",
                "category": "oracle",
                "swc_id": "SWC-136"
            }
        ]
        
        for vuln in vulnerabilities:
            try:
                self.add_vulnerability_pattern(**vuln)
            except Exception as e:
                print(f"Warning: Could not add vulnerability {vuln['vuln_id']}: {e}")


if __name__ == "__main__":
    # Initialize and populate database
    db = VectorDatabase()
    db.populate_initial_data()
    print("Vector database initialized and populated with vulnerability patterns")
    
    # Test search
    results = db.search_vulnerabilities("reentrancy attack", n_results=3)
    print(f"\nTest search for 'reentrancy attack': Found {len(results)} results")
    for result in results:
        print(f"  - {result['id']}: {result['metadata'].get('severity', 'N/A')}")
