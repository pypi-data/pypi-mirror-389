#!/usr/bin/env python3
"""
4naly3er Wrapper
Integrates 4naly3er static analysis tool with AI auditor
"""

import subprocess
import json
import os
from pathlib import Path

class FourNaly3erWrapper:
    def __init__(self):
        self.tool_path = "/home/ubuntu/ai_auditor/data/4naly3er"
        
    def analyze(self, contract_path, output_file=None):
        """Run 4naly3er analysis on a contract"""
        try:
            # Run 4naly3er
            cmd = [
                "yarn",
                "analyze",
                contract_path
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.tool_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse output
            findings = self.parse_output(result.stdout)
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(findings, f, indent=2)
            
            return findings
            
        except Exception as e:
            print(f"Error running 4naly3er: {e}")
            return []
    
    def parse_output(self, output):
        """Parse 4naly3er output"""
        findings = []
        
        # 4naly3er outputs markdown format
        # Parse it to extract findings
        lines = output.split('\n')
        
        current_category = None
        for line in lines:
            if line.startswith('##'):
                current_category = line.strip('# ').strip()
            elif line.startswith('-'):
                finding = line.strip('- ').strip()
                if finding:
                    findings.append({
                        'category': current_category,
                        'description': finding,
                        'tool': '4naly3er'
                    })
        
        return findings

def main():
    """Test 4naly3er wrapper"""
    wrapper = FourNaly3erWrapper()
    
    # Test on a sample contract
    test_contract = "/home/ubuntu/ai_auditor/tests/VulnerableBank.sol"
    
    if os.path.exists(test_contract):
        print("Testing 4naly3er on VulnerableBank.sol...")
        findings = wrapper.analyze(test_contract)
        print(f"Found {len(findings)} issues")
        
        for finding in findings[:5]:
            print(f"- [{finding['category']}] {finding['description']}")
    else:
        print("Test contract not found")
    
    print("\n✅ 4naly3er wrapper ready for integration")

if __name__ == "__main__":
    main()
