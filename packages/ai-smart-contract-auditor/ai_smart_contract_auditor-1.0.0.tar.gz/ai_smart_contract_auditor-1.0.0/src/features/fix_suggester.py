#!/usr/bin/env python3
"""
AI-Powered Fix Suggestion Module
Provides automated remediation suggestions for vulnerabilities
"""

import os
import json
from typing import Dict, List, Optional
import chromadb
from openai import OpenAI

class FixSuggester:
    """
    AI-powered fix suggester using vector database and LLM
    """
    
    def __init__(self, db_path: str = "/home/ubuntu/ai_auditor/database/vulnerability_db"):
        """Initialize fix suggester with vector database"""
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection("vulnerabilities")
        self.openai_client = OpenAI()
        
    def find_similar_fixes(self, vulnerability_description: str, n_results: int = 5) -> List[Dict]:
        """
        Find similar vulnerabilities with known fixes
        """
        results = self.collection.query(
            query_texts=[vulnerability_description],
            n_results=n_results
        )
        
        similar_fixes = []
        for i, (doc_id, metadata, document) in enumerate(zip(
            results['ids'][0], 
            results['metadatas'][0],
            results['documents'][0]
        )):
            similar_fixes.append({
                'id': doc_id,
                'title': metadata.get('title', ''),
                'severity': metadata.get('severity', ''),
                'source': metadata.get('source', ''),
                'description': document,
                'relevance_score': 1.0 - (i / n_results)
            })
        
        return similar_fixes
    
    def generate_fix_suggestion(self, vulnerability: Dict, similar_fixes: List[Dict]) -> Dict:
        """
        Generate fix suggestion using AI with similar fixes as context
        """
        # Build context from similar fixes
        context = "Similar vulnerabilities and their fixes:\n\n"
        for fix in similar_fixes[:3]:
            context += f"- {fix['title']} (Severity: {fix['severity']})\n"
            context += f"  Description: {fix['description'][:200]}...\n\n"
        
        # Create prompt for AI
        prompt = f"""You are a smart contract security expert. Provide a comprehensive fix for the following vulnerability:

**Vulnerability Details:**
Title: {vulnerability.get('title', 'Unknown')}
Description: {vulnerability.get('description', 'No description')}
Severity: {vulnerability.get('severity', 'UNKNOWN')}
Contract: {vulnerability.get('contract', 'Unknown')}
Vulnerable Code:
```solidity
{vulnerability.get('code', '// Code not provided')}
```

{context}

**Provide the following:**

1. **Root Cause Analysis**: Explain why this vulnerability exists

2. **Fix Recommendation**: Provide the corrected code with explanations

3. **Security Best Practices**: Additional recommendations to prevent similar issues

4. **Testing Recommendations**: How to test the fix

Format your response in markdown with clear sections.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert smart contract security auditor specializing in vulnerability remediation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            fix_suggestion = response.choices[0].message.content
            
            return {
                'vulnerability': vulnerability,
                'fix_suggestion': fix_suggestion,
                'similar_fixes': similar_fixes,
                'confidence': 'high' if len(similar_fixes) >= 3 else 'medium',
                'generation_method': 'AI-powered with pattern matching'
            }
            
        except Exception as e:
            return {
                'vulnerability': vulnerability,
                'fix_suggestion': f"Error generating fix: {str(e)}",
                'similar_fixes': similar_fixes,
                'confidence': 'low',
                'generation_method': 'error'
            }
    
    def suggest_fix(self, vulnerability: Dict) -> Dict:
        """
        Main method to generate fix suggestion for a vulnerability
        
        Args:
            vulnerability: Dict with keys: title, description, severity, contract, code
            
        Returns:
            Dict with fix suggestion and metadata
        """
        print(f"Generating fix for: {vulnerability.get('title', 'Unknown')}")
        
        # Step 1: Find similar fixes
        similar_fixes = self.find_similar_fixes(
            vulnerability.get('description', ''),
            n_results=5
        )
        
        print(f"Found {len(similar_fixes)} similar vulnerabilities")
        
        # Step 2: Generate fix using AI
        result = self.generate_fix_suggestion(vulnerability, similar_fixes)
        
        return result
    
    def save_fix_report(self, fix_result: Dict, output_dir: str = "/home/ubuntu/ai_auditor/fix_reports") -> str:
        """
        Save fix suggestion report to file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename
        title = fix_result['vulnerability'].get('title', 'unknown')
        filename = title.lower().replace(' ', '_').replace('/', '_')[:50] + '_fix.md'
        filepath = os.path.join(output_dir, filename)
        
        # Write report
        with open(filepath, 'w') as f:
            f.write(f"# Fix Report: {fix_result['vulnerability'].get('title', 'Unknown')}\n\n")
            f.write(f"**Severity**: {fix_result['vulnerability'].get('severity', 'UNKNOWN')}\n\n")
            f.write(f"**Contract**: {fix_result['vulnerability'].get('contract', 'Unknown')}\n\n")
            f.write(f"**Confidence**: {fix_result['confidence']}\n\n")
            f.write(f"---\n\n")
            f.write(fix_result['fix_suggestion'])
            f.write(f"\n\n---\n\n")
            f.write(f"## Similar Vulnerabilities Referenced\n\n")
            for fix in fix_result['similar_fixes']:
                f.write(f"- {fix['title']} ({fix['source']}, Severity: {fix['severity']})\n")
            f.write(f"\n\n*Generated by AI-Powered Fix Suggester*\n")
        
        print(f"Fix report saved to: {filepath}")
        return filepath


def main():
    """
    Example usage of fix suggester
    """
    print("=== AI-Powered Fix Suggester ===\n")
    
    # Initialize suggester
    suggester = FixSuggester()
    
    # Example vulnerability
    vulnerability = {
        'title': 'Reentrancy in withdraw function',
        'description': 'The withdraw function calls external contract before updating balance, allowing reentrancy attack',
        'severity': 'HIGH',
        'contract': 'VulnerableBank.sol',
        'code': '''function withdraw(uint256 amount) public {
    require(balances[msg.sender] >= amount, "Insufficient balance");
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
    balances[msg.sender] -= amount;
}'''
    }
    
    # Generate fix
    result = suggester.suggest_fix(vulnerability)
    
    # Save report
    filepath = suggester.save_fix_report(result)
    
    print(f"\n=== Fix Generation Complete ===")
    print(f"Similar fixes found: {len(result['similar_fixes'])}")
    print(f"Confidence: {result['confidence']}")
    print(f"Output file: {filepath}")


if __name__ == "__main__":
    main()
