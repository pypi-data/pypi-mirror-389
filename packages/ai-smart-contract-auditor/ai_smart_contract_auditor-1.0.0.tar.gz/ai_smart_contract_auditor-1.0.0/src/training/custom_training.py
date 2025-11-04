#!/usr/bin/env python3
"""
Custom Training Framework
Protocol-specific fine-tuning for vulnerability detection
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class CustomTrainingFramework:
    """
    Framework for protocol-specific vulnerability detection training
    """
    
    def __init__(self, protocol_name: str, output_dir: str = "training/models"):
        """
        Initialize custom training framework
        
        Args:
            protocol_name: Name of the protocol
            output_dir: Directory to save trained models
        """
        self.protocol_name = protocol_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.training_data = []
        self.validation_data = []
        self.vulnerability_patterns = []
        
    def add_training_example(self, code: str, vulnerability: str, severity: str, 
                            description: str, fix: str = None):
        """
        Add training example
        
        Args:
            code: Vulnerable code snippet
            vulnerability: Vulnerability type
            severity: Severity level
            description: Vulnerability description
            fix: Optional fix code
        """
        example = {
            'code': code,
            'vulnerability': vulnerability,
            'severity': severity,
            'description': description,
            'fix': fix,
            'protocol': self.protocol_name,
            'timestamp': datetime.now().isoformat()
        }
        
        self.training_data.append(example)
    
    def add_vulnerability_pattern(self, pattern_name: str, indicators: List[str],
                                 severity: str, description: str):
        """
        Add protocol-specific vulnerability pattern
        
        Args:
            pattern_name: Name of the pattern
            indicators: Code indicators (function names, patterns, etc.)
            severity: Severity level
            description: Pattern description
        """
        pattern = {
            'name': pattern_name,
            'indicators': indicators,
            'severity': severity,
            'description': description,
            'protocol': self.protocol_name
        }
        
        self.vulnerability_patterns.append(pattern)
    
    def load_from_audit_reports(self, reports_dir: str):
        """
        Load training data from audit reports
        
        Args:
            reports_dir: Directory containing audit reports
        """
        reports_path = Path(reports_dir)
        
        if not reports_path.exists():
            print(f"⚠️ Reports directory not found: {reports_dir}")
            return
        
        count = 0
        for report_file in reports_path.glob("**/*.json"):
            try:
                with open(report_file) as f:
                    report = json.load(f)
                
                for finding in report.get('findings', []):
                    self.add_training_example(
                        code=finding.get('code', ''),
                        vulnerability=finding.get('title', ''),
                        severity=finding.get('severity', 'UNKNOWN'),
                        description=finding.get('description', ''),
                        fix=finding.get('fix', None)
                    )
                    count += 1
            except Exception as e:
                print(f"⚠️ Error loading {report_file}: {e}")
        
        print(f"✅ Loaded {count} training examples from audit reports")
    
    def generate_training_dataset(self) -> str:
        """
        Generate training dataset in JSONL format
        
        Returns:
            Path to generated dataset
        """
        dataset_path = self.output_dir / f"{self.protocol_name}_training_dataset.jsonl"
        
        with open(dataset_path, 'w') as f:
            for example in self.training_data:
                # Format for GPT fine-tuning
                training_item = {
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a security auditor specialized in {self.protocol_name} smart contracts."
                        },
                        {
                            "role": "user",
                            "content": f"Analyze this code for vulnerabilities:\\n\\n{example['code']}"
                        },
                        {
                            "role": "assistant",
                            "content": f"Vulnerability: {example['vulnerability']}\\nSeverity: {example['severity']}\\nDescription: {example['description']}"
                        }
                    ]
                }
                
                f.write(json.dumps(training_item) + '\\n')
        
        print(f"✅ Generated training dataset: {dataset_path}")
        print(f"   Total examples: {len(self.training_data)}")
        
        return str(dataset_path)
    
    def save_vulnerability_patterns(self) -> str:
        """
        Save vulnerability patterns to JSON
        
        Returns:
            Path to saved patterns
        """
        patterns_path = self.output_dir / f"{self.protocol_name}_patterns.json"
        
        with open(patterns_path, 'w') as f:
            json.dump({
                'protocol': self.protocol_name,
                'patterns': self.vulnerability_patterns,
                'created': datetime.now().isoformat(),
                'count': len(self.vulnerability_patterns)
            }, f, indent=2)
        
        print(f"✅ Saved vulnerability patterns: {patterns_path}")
        print(f"   Total patterns: {len(self.vulnerability_patterns)}")
        
        return str(patterns_path)
    
    def generate_evaluation_metrics(self):
        """
        Generate evaluation metrics configuration
        """
        metrics = {
            'protocol': self.protocol_name,
            'metrics': {
                'precision': 'Percentage of identified vulnerabilities that are true positives',
                'recall': 'Percentage of actual vulnerabilities that are identified',
                'f1_score': 'Harmonic mean of precision and recall',
                'false_positive_rate': 'Percentage of false alarms',
                'severity_accuracy': 'Accuracy of severity classification'
            },
            'thresholds': {
                'min_precision': 0.85,
                'min_recall': 0.90,
                'max_false_positive_rate': 0.10
            }
        }
        
        metrics_path = self.output_dir / f"{self.protocol_name}_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"✅ Generated evaluation metrics: {metrics_path}")
        
        return str(metrics_path)
    
    def create_fine_tuning_guide(self):
        """
        Create fine-tuning guide
        """
        guide = f"""# Custom Training Guide: {self.protocol_name}

## Overview

This guide explains how to fine-tune the AI auditor for {self.protocol_name}-specific vulnerabilities.

## Prerequisites

1. OpenAI API key with fine-tuning access
2. Training dataset (generated)
3. Validation dataset (recommended: 20% of training data)

## Training Dataset

- **Location**: `{self.protocol_name}_training_dataset.jsonl`
- **Examples**: {len(self.training_data)}
- **Format**: JSONL (OpenAI fine-tuning format)

## Vulnerability Patterns

- **Location**: `{self.protocol_name}_patterns.json`
- **Patterns**: {len(self.vulnerability_patterns)}
- **Usage**: Static analysis rules

## Fine-Tuning Steps

### 1. Prepare Data

```bash
# Split into training and validation
python3 training/split_dataset.py {self.protocol_name}_training_dataset.jsonl --split 0.8
```

### 2. Upload to OpenAI

```bash
# Upload training file
openai api files.create \\
  -f {self.protocol_name}_training_dataset.jsonl \\
  -p fine-tune

# Note the file ID
export TRAINING_FILE_ID="file-xxx"
```

### 3. Create Fine-Tuning Job

```bash
openai api fine_tunes.create \\
  -t $TRAINING_FILE_ID \\
  -m gpt-4.1-mini \\
  --suffix "{self.protocol_name}-auditor"
```

### 4. Monitor Training

```bash
# Check status
openai api fine_tunes.get -i <fine-tune-id>

# Stream logs
openai api fine_tunes.follow -i <fine-tune-id>
```

### 5. Use Fine-Tuned Model

```python
from ..features.poc_generator import PoCGenerator

generator = PoCGenerator(
    model="ft:gpt-4.1-mini:{self.protocol_name}-auditor"
)

poc = generator.generate_poc(
    vulnerability="Reentrancy in withdraw",
    contract_code=contract_code
)
```

## Evaluation

### Metrics

- **Precision**: {'>85%'}
- **Recall**: {'>90%'}
- **F1 Score**: {'>87%'}
- **False Positive Rate**: {'<10%'}

### Testing

```bash
python3 training/evaluate_model.py \\
  --model ft:gpt-4.1-mini:{self.protocol_name}-auditor \\
  --test-data validation_dataset.jsonl
```

## Continuous Improvement

1. **Collect New Examples**: Add findings from new audits
2. **Retrain Periodically**: Update model every 3-6 months
3. **Monitor Performance**: Track precision/recall metrics
4. **Update Patterns**: Add new vulnerability patterns

## Cost Estimation

- **Training**: ~$0.008 per 1K tokens
- **Inference**: ~$0.03 per 1K tokens (fine-tuned model)
- **Estimated Cost**: ${len(self.training_data) * 0.5:.2f} for {len(self.training_data)} examples

## Support

For issues or questions:
- GitHub: https://github.com/jw3b-dev/AI-Smart-Contract-Auditor
- Documentation: See TRAINING.md
"""
        
        guide_path = self.output_dir / f"{self.protocol_name}_TRAINING_GUIDE.md"
        with open(guide_path, 'w') as f:
            f.write(guide)
        
        print(f"✅ Created training guide: {guide_path}")
        
        return str(guide_path)


def example_usage():
    """
    Example usage of custom training framework
    """
    print("=== Custom Training Framework ===\\n")
    
    # Initialize framework for Uniswap V3
    framework = CustomTrainingFramework("UniswapV3")
    
    # Add training examples
    framework.add_training_example(
        code="""
function swap(uint256 amount) external {
    // Missing slippage protection
    pool.swap(amount, 0, address(this));
}
""",
        vulnerability="Missing Slippage Protection",
        severity="HIGH",
        description="Swap function does not implement slippage protection, allowing MEV attacks",
        fix="Add minAmountOut parameter and validate output amount"
    )
    
    framework.add_training_example(
        code="""
function collect(uint128 amount0, uint128 amount1) external {
    // Missing access control
    position.collect(amount0, amount1);
}
""",
        vulnerability="Missing Access Control",
        severity="CRITICAL",
        description="Collect function lacks access control, allowing anyone to collect fees",
        fix="Add onlyOwner modifier or position ownership check"
    )
    
    # Add vulnerability patterns
    framework.add_vulnerability_pattern(
        pattern_name="Unprotected Swap",
        indicators=["swap(", "minAmountOut == 0", "deadline == 0"],
        severity="HIGH",
        description="Swap operations without slippage or deadline protection"
    )
    
    framework.add_vulnerability_pattern(
        pattern_name="Fee Collection Vulnerability",
        indicators=["collect(", "!= msg.sender", "public"],
        severity="CRITICAL",
        description="Fee collection functions without proper access control"
    )
    
    # Generate outputs
    dataset_path = framework.generate_training_dataset()
    patterns_path = framework.save_vulnerability_patterns()
    metrics_path = framework.generate_evaluation_metrics()
    guide_path = framework.create_fine_tuning_guide()
    
    print("\\n✅ Custom training framework setup complete!")
    print(f"\\nGenerated files:")
    print(f"  - Training dataset: {dataset_path}")
    print(f"  - Vulnerability patterns: {patterns_path}")
    print(f"  - Evaluation metrics: {metrics_path}")
    print(f"  - Training guide: {guide_path}")


if __name__ == "__main__":
    example_usage()
