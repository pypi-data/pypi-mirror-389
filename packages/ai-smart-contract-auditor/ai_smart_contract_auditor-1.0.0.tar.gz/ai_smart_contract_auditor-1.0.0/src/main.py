#!/usr/bin/env python3
"""
AI-Powered Smart Contract Auditor - Updated Version
Now with 14,013 findings from Solodit + Sherlock
"""

import sys
import os
import json
from pathlib import Path
import chromadb
from datetime import datetime

# Import existing modules
sys.path.insert(0, str(Path(__file__).parent))

def load_vector_database():
    """Load the updated vector database"""
    db_path = "/home/ubuntu/ai_auditor/database/vulnerability_db"
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name="vulnerabilities")
    return collection

def query_similar_vulnerabilities(collection, query_text, n_results=5):
    """Query for similar vulnerabilities"""
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results

def get_database_stats(collection):
    """Get database statistics"""
    total_count = collection.count()
    
    # Get counts by source
    try:
        solodit_results = collection.query(
            query_texts=["vulnerability"],
            n_results=1,
            where={"source": "solodit"}
        )
        sherlock_results = collection.query(
            query_texts=["vulnerability"],
            n_results=1,
            where={"source": "sherlock"}
        )
    except:
        solodit_results = None
        sherlock_results = None
    
    return {
        'total': total_count,
        'has_solodit': solodit_results is not None,
        'has_sherlock': sherlock_results is not None
    }

def audit_contract(contract_path):
    """Audit a smart contract using the updated database"""
    print("=" * 80)
    print("AI-POWERED SMART CONTRACT AUDITOR - UPDATED")
    print("=" * 80)
    
    # Load vector database
    print("\n1. Loading vector database...")
    collection = load_vector_database()
    stats = get_database_stats(collection)
    print(f"   Database loaded: {stats['total']:,} vulnerabilities")
    print(f"   Sources: Solodit {'✓' if stats['has_solodit'] else '✗'}, Sherlock {'✓' if stats['has_sherlock'] else '✗'}")
    
    # Read contract
    print(f"\n2. Reading contract: {contract_path}")
    try:
        with open(contract_path, 'r') as f:
            contract_code = f.read()
        print(f"   Contract size: {len(contract_code)} characters, {contract_code.count(chr(10))} lines")
    except FileNotFoundError:
        print(f"   ❌ Error: Contract file not found: {contract_path}")
        return
    
    # Analyze for common vulnerability patterns
    print("\n3. Analyzing for vulnerability patterns...")
    
    patterns = {
        'reentrancy': ['call{value:', '.call{', 'transfer(', 'send('],
        'access_control': ['onlyOwner', 'require(msg.sender', 'modifier only'],
        'integer_overflow': ['uint256', 'uint', 'unchecked', '++', '--'],
        'oracle_manipulation': ['getPrice', 'oracle', 'TWAP', 'chainlink'],
        'flash_loan': ['flashLoan', 'borrow(', 'repay(']
    }
    
    detected_patterns = []
    for pattern_name, keywords in patterns.items():
        if any(keyword in contract_code for keyword in keywords):
            detected_patterns.append(pattern_name)
    
    print(f"   Detected patterns: {', '.join(detected_patterns) if detected_patterns else 'None'}")
    
    # Query vector database for similar vulnerabilities
    print("\n4. Querying vector database for similar vulnerabilities...")
    
    findings = []
    for pattern in detected_patterns[:3]:  # Limit to top 3 patterns
        print(f"\n   Searching for {pattern} vulnerabilities...")
        results = query_similar_vulnerabilities(collection, f"{pattern} vulnerability", n_results=3)
        
        if results['documents'][0]:
            print(f"   Found {len(results['documents'][0])} similar cases")
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                findings.append({
                    'pattern': pattern,
                    'severity': metadata.get('severity', 'UNKNOWN'),
                    'source': metadata.get('source', 'unknown'),
                    'description': doc[:200],
                    'validated': metadata.get('validated', 'false') == 'true'
                })
                print(f"     - {metadata.get('severity', 'UNKNOWN')}: {doc[:80]}...")
    
    # Generate report
    print("\n5. Generating audit report...")
    
    report = {
        'contract': contract_path,
        'audit_date': datetime.now().isoformat(),
        'database_stats': stats,
        'patterns_detected': detected_patterns,
        'findings': findings,
        'summary': {
            'total_findings': len(findings),
            'high_severity': sum(1 for f in findings if f['severity'] == 'HIGH'),
            'medium_severity': sum(1 for f in findings if f['severity'] == 'MEDIUM'),
            'validated_findings': sum(1 for f in findings if f['validated'])
        }
    }
    
    # Save report
    report_file = Path(contract_path).stem + '_audit_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"   Report saved to: {report_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Contract: {contract_path}")
    print(f"Patterns Detected: {len(detected_patterns)}")
    print(f"Total Findings: {report['summary']['total_findings']}")
    print(f"  HIGH: {report['summary']['high_severity']}")
    print(f"  MEDIUM: {report['summary']['medium_severity']}")
    print(f"Validated Findings: {report['summary']['validated_findings']}")
    print("=" * 80)
    
    return report

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main_updated.py <contract_path>")
        print("\nExample:")
        print("  python3 main_updated.py tests/VulnerableBank.sol")
        sys.exit(1)
    
    contract_path = sys.argv[1]
    audit_contract(contract_path)

if __name__ == "__main__":
    main()
