"""
Test Data Generation Automation.

Automatically generates realistic test data for contracts, vulnerabilities,
findings, and reports using Faker and custom generators.
"""

from faker import Faker
import random
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta


class TestDataGenerator:
    """Generate realistic test data for auditing."""
    
    def __init__(self, seed=None):
        """Initialize generator with optional seed for reproducibility."""
        self.fake = Faker()
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
    
    # Contract Generation
    
    def generate_contract_code(self, vulnerability_type=None) -> str:
        """Generate a Solidity contract with optional vulnerability."""
        contract_name = self.fake.word().capitalize() + "Contract"
        
        if vulnerability_type == "reentrancy":
            return f"""
pragma solidity ^0.8.0;

contract {contract_name} {{
    mapping(address => uint256) public balances;
    
    function withdraw() public {{
        uint256 amount = balances[msg.sender];
        (bool success, ) = msg.sender.call{{value: amount}}("");
        require(success);
        balances[msg.sender] = 0;  // Reentrancy vulnerability
    }}
    
    function deposit() public payable {{
        balances[msg.sender] += msg.value;
    }}
}}
"""
        elif vulnerability_type == "overflow":
            return f"""
pragma solidity ^0.7.0;  // No SafeMath

contract {contract_name} {{
    uint256 public total;
    
    function add(uint256 value) public {{
        total += value;  // Potential overflow
    }}
}}
"""
        elif vulnerability_type == "access-control":
            return f"""
pragma solidity ^0.8.0;

contract {contract_name} {{
    address public owner;
    
    function setOwner(address newOwner) public {{
        owner = newOwner;  // Missing access control
    }}
}}
"""
        else:
            return f"""
pragma solidity ^0.8.0;

contract {contract_name} {{
    uint256 public value;
    
    function setValue(uint256 _value) public {{
        value = _value;
    }}
}}
"""
    
    def generate_contract_metadata(self) -> Dict[str, Any]:
        """Generate contract metadata."""
        return {
            "name": self.fake.word().capitalize() + "Contract",
            "version": f"{random.randint(0, 1)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
            "compiler": f"0.8.{random.randint(0, 20)}",
            "license": random.choice(["MIT", "Apache-2.0", "GPL-3.0", "UNLICENSED"]),
            "author": self.fake.name(),
            "created_at": self.fake.date_time_this_year().isoformat(),
        }
    
    # Vulnerability Generation
    
    def generate_vulnerability(self, severity=None) -> Dict[str, Any]:
        """Generate a vulnerability finding."""
        vuln_types = [
            "reentrancy", "overflow", "underflow", "access-control",
            "unchecked-call", "delegatecall", "tx-origin", "timestamp-dependence",
            "front-running", "denial-of-service", "logic-error"
        ]
        
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        severity = severity or random.choice(severities)
        
        return {
            "id": self.fake.uuid4(),
            "type": random.choice(vuln_types),
            "severity": severity,
            "confidence": round(random.uniform(0.5, 1.0), 2),
            "title": self.fake.sentence(nb_words=6),
            "description": self.fake.paragraph(nb_sentences=3),
            "line": random.randint(1, 100),
            "column": random.randint(1, 80),
            "file": f"{self.fake.word()}.sol",
            "detected_at": datetime.now().isoformat(),
        }
    
    def generate_vulnerabilities(self, count=5, severity_distribution=None) -> List[Dict[str, Any]]:
        """Generate multiple vulnerabilities with optional severity distribution."""
        if severity_distribution is None:
            severity_distribution = {
                "CRITICAL": 0.1,
                "HIGH": 0.3,
                "MEDIUM": 0.4,
                "LOW": 0.2,
            }
        
        vulnerabilities = []
        for _ in range(count):
            severity = random.choices(
                list(severity_distribution.keys()),
                weights=list(severity_distribution.values())
            )[0]
            vulnerabilities.append(self.generate_vulnerability(severity))
        
        return vulnerabilities
    
    # PoC Generation
    
    def generate_poc(self, vulnerability_type: str) -> Dict[str, Any]:
        """Generate a Proof of Concept exploit."""
        return {
            "id": self.fake.uuid4(),
            "vulnerability_type": vulnerability_type,
            "title": f"PoC for {vulnerability_type}",
            "description": self.fake.paragraph(),
            "code": self.generate_poc_code(vulnerability_type),
            "steps": [
                self.fake.sentence() for _ in range(random.randint(3, 7))
            ],
            "impact": self.fake.paragraph(nb_sentences=2),
            "created_at": datetime.now().isoformat(),
        }
    
    def generate_poc_code(self, vulnerability_type: str) -> str:
        """Generate PoC exploit code."""
        if vulnerability_type == "reentrancy":
            return """
contract Exploit {
    Vulnerable target;
    
    constructor(address _target) {
        target = Vulnerable(_target);
    }
    
    function attack() public payable {
        target.deposit{value: msg.value}();
        target.withdraw();
    }
    
    receive() external payable {
        if (address(target).balance > 0) {
            target.withdraw();
        }
    }
}
"""
        else:
            return f"// PoC for {vulnerability_type}\ncontract Exploit {{}}"
    
    # Fix Suggestion Generation
    
    def generate_fix_suggestion(self, vulnerability_type: str) -> Dict[str, Any]:
        """Generate a fix suggestion."""
        return {
            "id": self.fake.uuid4(),
            "vulnerability_type": vulnerability_type,
            "original_code": self.fake.text(max_nb_chars=100),
            "fixed_code": self.fake.text(max_nb_chars=100),
            "explanation": self.fake.paragraph(nb_sentences=3),
            "references": [
                self.fake.url() for _ in range(random.randint(1, 3))
            ],
            "confidence": round(random.uniform(0.7, 1.0), 2),
        }
    
    # Report Generation
    
    def generate_audit_report(self, num_findings=10) -> Dict[str, Any]:
        """Generate a complete audit report."""
        contract_meta = self.generate_contract_metadata()
        vulnerabilities = self.generate_vulnerabilities(num_findings)
        
        return {
            "id": self.fake.uuid4(),
            "title": f"Security Audit Report: {contract_meta['name']}",
            "contract": contract_meta,
            "auditor": self.fake.name(),
            "audit_date": self.fake.date_this_month().isoformat(),
            "summary": {
                "total_findings": num_findings,
                "critical": sum(1 for v in vulnerabilities if v["severity"] == "CRITICAL"),
                "high": sum(1 for v in vulnerabilities if v["severity"] == "HIGH"),
                "medium": sum(1 for v in vulnerabilities if v["severity"] == "MEDIUM"),
                "low": sum(1 for v in vulnerabilities if v["severity"] == "LOW"),
            },
            "findings": vulnerabilities,
            "recommendations": [
                self.fake.sentence() for _ in range(random.randint(3, 7))
            ],
            "conclusion": self.fake.paragraph(nb_sentences=4),
        }
    
    # Batch Generation
    
    def generate_batch_contracts(self, count=10) -> List[Dict[str, Any]]:
        """Generate multiple contracts."""
        return [
            {
                "code": self.generate_contract_code(),
                "metadata": self.generate_contract_metadata(),
            }
            for _ in range(count)
        ]
    
    def generate_batch_vulnerabilities(self, count=50) -> List[Dict[str, Any]]:
        """Generate a large batch of vulnerabilities."""
        return self.generate_vulnerabilities(count)
    
    # Specialized Generators
    
    def generate_test_suite_data(self) -> Dict[str, Any]:
        """Generate a complete test suite dataset."""
        return {
            "contracts": self.generate_batch_contracts(5),
            "vulnerabilities": self.generate_batch_vulnerabilities(20),
            "pocs": [self.generate_poc("reentrancy") for _ in range(3)],
            "fixes": [self.generate_fix_suggestion("reentrancy") for _ in range(5)],
            "reports": [self.generate_audit_report(10) for _ in range(2)],
        }
    
    def generate_edge_case_data(self) -> Dict[str, Any]:
        """Generate edge case test data."""
        return {
            "empty_contract": "",
            "minimal_contract": "contract A {}",
            "large_contract": self.generate_contract_code() * 10,
            "unicode_contract": "contract 测试 { uint 值; }",
            "special_chars": "contract Test { /* <>&\"' */ }",
            "no_vulnerabilities": [],
            "single_vulnerability": self.generate_vulnerabilities(1),
            "many_vulnerabilities": self.generate_vulnerabilities(100),
        }
    
    # Persistence
    
    def save_to_file(self, data: Any, filepath: str):
        """Save generated data to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str) -> Any:
        """Load generated data from JSON file."""
        with open(filepath, 'r') as f:
            return json.load(f)


# Convenience functions for pytest fixtures

def generate_test_contract(vulnerability_type=None, seed=None):
    """Generate a test contract."""
    gen = TestDataGenerator(seed=seed)
    return gen.generate_contract_code(vulnerability_type)


def generate_test_vulnerabilities(count=5, seed=None):
    """Generate test vulnerabilities."""
    gen = TestDataGenerator(seed=seed)
    return gen.generate_vulnerabilities(count)


def generate_test_report(num_findings=10, seed=None):
    """Generate a test audit report."""
    gen = TestDataGenerator(seed=seed)
    return gen.generate_audit_report(num_findings)


# Example usage
if __name__ == "__main__":
    generator = TestDataGenerator(seed=42)
    
    # Generate and save test data
    test_suite = generator.generate_test_suite_data()
    generator.save_to_file(test_suite, "test_data.json")
    
    print("✓ Test data generated and saved to test_data.json")
    print(f"  - {len(test_suite['contracts'])} contracts")
    print(f"  - {len(test_suite['vulnerabilities'])} vulnerabilities")
    print(f"  - {len(test_suite['pocs'])} PoCs")
    print(f"  - {len(test_suite['fixes'])} fixes")
    print(f"  - {len(test_suite['reports'])} reports")
