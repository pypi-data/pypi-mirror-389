#!/usr/bin/env python3
"""
Automated PoC Generation Module
Generates proof-of-concept exploits based on vulnerability findings
"""

import os
import json
from typing import Dict, List, Optional
import chromadb
from openai import OpenAI

class PoCGenerator:
    """
    Automated PoC generator using AI and template matching
    """
    
    def __init__(self, db_path: str = "/home/ubuntu/ai_auditor/database/vulnerability_db"):
        """Initialize PoC generator with vector database"""
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection("vulnerabilities")
        self.openai_client = OpenAI()  # Uses OPENAI_API_KEY from environment
        
    def find_similar_pocs(self, vulnerability_description: str, n_results: int = 5) -> List[Dict]:
        """
        Find similar PoCs from the database using semantic search
        """
        results = self.collection.query(
            query_texts=[vulnerability_description],
            n_results=n_results,
            where={"source": {"$in": ["Sherlock", "DeFiHackLabs"]}}  # Only sources with PoCs
        )
        
        similar_pocs = []
        for i, (doc_id, metadata) in enumerate(zip(results['ids'][0], results['metadatas'][0])):
            similar_pocs.append({
                'id': doc_id,
                'title': metadata.get('title', ''),
                'severity': metadata.get('severity', ''),
                'source': metadata.get('source', ''),
                'relevance_score': 1.0 - (i / n_results)  # Simple relevance scoring
            })
        
        return similar_pocs
    
    def generate_poc_from_template(self, vulnerability: Dict, similar_pocs: List[Dict]) -> str:
        """
        Generate PoC using AI with similar PoCs as context
        """
        # Build context from similar PoCs
        context = "Similar vulnerability PoCs for reference:\n\n"
        for poc in similar_pocs[:3]:  # Use top 3 similar PoCs
            context += f"- {poc['title']} (Severity: {poc['severity']}, Source: {poc['source']})\n"
        
        # Create prompt for AI
        prompt = f"""You are a smart contract security expert. Generate a Foundry test PoC (Proof of Concept) for the following vulnerability:

**Vulnerability Details:**
Title: {vulnerability.get('title', 'Unknown')}
Description: {vulnerability.get('description', 'No description')}
Severity: {vulnerability.get('severity', 'UNKNOWN')}
Contract: {vulnerability.get('contract', 'Unknown')}

{context}

**Requirements:**
1. Use Foundry test framework (forge-std/Test.sol)
2. Create a complete, working exploit demonstration
3. Include setup, attack execution, and verification
4. Add comments explaining each step
5. Use realistic attack scenarios (no artificial vulnerabilities)
6. Demonstrate actual fund theft or impact
7. Include assertions to prove the exploit works

**Generate the complete Solidity PoC:**
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",  # Using available model
                messages=[
                    {"role": "system", "content": "You are an expert smart contract security auditor specializing in creating proof-of-concept exploits."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            poc_code = response.choices[0].message.content
            return poc_code
            
        except Exception as e:
            return f"// Error generating PoC: {str(e)}\n// Please create PoC manually based on similar examples"
    
    def generate_poc(self, vulnerability: Dict) -> Dict:
        """
        Main method to generate PoC for a vulnerability
        
        Args:
            vulnerability: Dict with keys: title, description, severity, contract
            
        Returns:
            Dict with generated PoC code and metadata
        """
        print(f"Generating PoC for: {vulnerability.get('title', 'Unknown')}")
        
        # Step 1: Find similar PoCs
        similar_pocs = self.find_similar_pocs(
            vulnerability.get('description', ''),
            n_results=5
        )
        
        print(f"Found {len(similar_pocs)} similar PoCs")
        
        # Step 2: Generate PoC using AI
        poc_code = self.generate_poc_from_template(vulnerability, similar_pocs)
        
        # Step 3: Return result
        result = {
            'vulnerability': vulnerability,
            'poc_code': poc_code,
            'similar_pocs': similar_pocs,
            'generation_method': 'AI-powered with template matching',
            'confidence': 'medium' if similar_pocs else 'low'
        }
        
        return result
    
    def save_poc(self, poc_result: Dict, output_dir: str = "/home/ubuntu/ai_auditor/generated_pocs") -> str:
        """
        Save generated PoC to file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename from vulnerability title
        title = poc_result['vulnerability'].get('title', 'unknown')
        filename = title.lower().replace(' ', '_').replace('/', '_')[:50] + '.sol'
        filepath = os.path.join(output_dir, filename)
        
        # Write PoC code
        with open(filepath, 'w') as f:
            f.write(f"// SPDX-License-Identifier: MIT\n")
            f.write(f"pragma solidity ^0.8.0;\n\n")
            f.write(f"// Vulnerability: {poc_result['vulnerability'].get('title', 'Unknown')}\n")
            f.write(f"// Severity: {poc_result['vulnerability'].get('severity', 'UNKNOWN')}\n")
            f.write(f"// Generated by: AI-Powered PoC Generator\n")
            f.write(f"// Confidence: {poc_result['confidence']}\n\n")
            f.write(poc_result['poc_code'])
        
        print(f"PoC saved to: {filepath}")
        return filepath


def main():
    """
    Example usage of PoC generator
    """
    print("=== AI-Powered PoC Generator ===\n")
    
    # Initialize generator
    generator = PoCGenerator()
    
    # Example vulnerability
    vulnerability = {
        'title': 'Reentrancy in withdraw function',
        'description': 'The withdraw function calls external contract before updating balance, allowing reentrancy attack to drain funds',
        'severity': 'HIGH',
        'contract': 'VulnerableBank.sol'
    }
    
    # Generate PoC
    result = generator.generate_poc(vulnerability)
    
    # Save PoC
    filepath = generator.save_poc(result)
    
    print(f"\n=== Generation Complete ===")
    print(f"Similar PoCs found: {len(result['similar_pocs'])}")
    print(f"Confidence: {result['confidence']}")
    print(f"Output file: {filepath}")


if __name__ == "__main__":
    main()
