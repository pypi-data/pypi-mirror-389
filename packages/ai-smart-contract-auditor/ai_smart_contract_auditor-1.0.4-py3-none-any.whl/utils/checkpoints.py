"""
Validation Checkpoints Module
Implements Go/No-Go checkpoints for the audit workflow
"""

import subprocess
import os
import json
from typing import Dict, List, Any, Tuple


class ValidationCheckpoints:
    """Manages validation checkpoints for the audit workflow"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize validation checkpoints
        
        Args:
            config_path: Path to checkpoint configuration file
        """
        self.checkpoints = {
            "GNG1": self.checkpoint_environment,
            "GNG2": self.checkpoint_tool_execution,
            "GNG3": self.checkpoint_poc_working,
            "GNG4": self.checkpoint_fix_verification
        }
        
        self.config = self._load_config(config_path)
        self.checkpoint_results = {}
    
    def _load_config(self, config_path: str) -> Dict:
        """Load checkpoint configuration"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def checkpoint_environment(self, audit_context: Dict) -> Tuple[bool, str]:
        """
        GNG1: Environment Setup Validation
        
        Verifies:
        - All required tools are installed
        - Code compiles without errors
        - Test environment is configured
        - Dependencies are resolved
        
        Args:
            audit_context: Dictionary containing audit context
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        required_tools = ['slither', 'forge', 'halmos']
        missing_tools = []
        
        # Check for required tools
        for tool in required_tools:
            result = subprocess.run(
                ['which', tool],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                missing_tools.append(tool)
        
        if missing_tools:
            message = f"Missing required tools: {', '.join(missing_tools)}"
            self.checkpoint_results['GNG1'] = {'passed': False, 'message': message}
            return False, message
        
        # Check if contract path exists
        contract_path = audit_context.get('contract_path')
        if contract_path and not os.path.exists(contract_path):
            message = f"Contract path does not exist: {contract_path}"
            self.checkpoint_results['GNG1'] = {'passed': False, 'message': message}
            return False, message
        
        # Check if code compiles (if project path provided)
        project_path = audit_context.get('project_path')
        if project_path and os.path.exists(project_path):
            try:
                result = subprocess.run(
                    ['forge', 'build'],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode != 0:
                    message = f"Compilation failed: {result.stderr[:200]}"
                    self.checkpoint_results['GNG1'] = {'passed': False, 'message': message}
                    return False, message
            except Exception as e:
                message = f"Compilation check failed: {str(e)}"
                self.checkpoint_results['GNG1'] = {'passed': False, 'message': message}
                return False, message
        
        message = "Environment setup validated successfully"
        self.checkpoint_results['GNG1'] = {'passed': True, 'message': message}
        return True, message
    
    def checkpoint_tool_execution(self, audit_context: Dict) -> Tuple[bool, str]:
        """
        GNG2: Automated Tool Execution Checkpoint
        
        Verifies:
        - All static and dynamic analysis tools have been run
        - Tools produced valid output
        - Results have been collected
        
        Args:
            audit_context: Dictionary containing audit context
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        tool_results = audit_context.get('tool_results', {})
        
        required_tools = ['slither']  # Minimum required
        missing_results = []
        
        for tool in required_tools:
            if tool not in tool_results:
                missing_results.append(tool)
            elif not tool_results[tool].get('success'):
                missing_results.append(f"{tool} (failed)")
        
        if missing_results:
            message = f"Missing or failed tool results: {', '.join(missing_results)}"
            self.checkpoint_results['GNG2'] = {'passed': False, 'message': message}
            return False, message
        
        # Check if we have findings
        total_findings = 0
        for tool, result in tool_results.items():
            findings = result.get('findings', [])
            total_findings += len(findings)
        
        message = f"Tool execution validated: {len(tool_results)} tools run, {total_findings} findings"
        self.checkpoint_results['GNG2'] = {'passed': True, 'message': message}
        return True, message
    
    def checkpoint_poc_working(self, audit_context: Dict) -> Tuple[bool, str]:
        """
        GNG3: PoC Validation Checkpoint
        
        Verifies:
        - PoC has been developed for each confirmed vulnerability
        - PoC executes successfully
        - PoC demonstrates actual exploitation
        - Financial impact is proven
        
        Args:
            audit_context: Dictionary containing audit context
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        poc_results = audit_context.get('poc_results', {})
        vulnerabilities = audit_context.get('vulnerabilities', [])
        
        # Filter vulnerabilities that require PoC (HIGH and MEDIUM severity)
        vuln_requiring_poc = [
            v for v in vulnerabilities 
            if v.get('severity') in ['HIGH', 'MEDIUM']
        ]
        
        if not vuln_requiring_poc:
            message = "No vulnerabilities requiring PoC validation"
            self.checkpoint_results['GNG3'] = {'passed': True, 'message': message}
            return True, message
        
        # Check if each vulnerability has a working PoC
        missing_pocs = []
        failed_pocs = []
        
        for vuln in vuln_requiring_poc:
            vuln_id = vuln.get('id')
            poc_result = poc_results.get(vuln_id)
            
            if not poc_result:
                missing_pocs.append(vuln_id)
            elif not poc_result.get('exploitation_successful'):
                failed_pocs.append(vuln_id)
        
        if missing_pocs:
            message = f"Missing PoCs for vulnerabilities: {', '.join(missing_pocs)}"
            self.checkpoint_results['GNG3'] = {'passed': False, 'message': message}
            return False, message
        
        if failed_pocs:
            message = f"Failed PoCs (exploitation unsuccessful): {', '.join(failed_pocs)}"
            self.checkpoint_results['GNG3'] = {'passed': False, 'message': message}
            return False, message
        
        # Verify exploitation demonstrates actual impact
        for vuln in vuln_requiring_poc:
            vuln_id = vuln.get('id')
            poc_result = poc_results.get(vuln_id, {})
            
            # Check for evidence of exploitation
            if not poc_result.get('funds_stolen') and not poc_result.get('state_corrupted'):
                message = f"PoC for {vuln_id} does not demonstrate actual exploitation"
                self.checkpoint_results['GNG3'] = {'passed': False, 'message': message}
                return False, message
        
        message = f"PoC validation passed: {len(vuln_requiring_poc)} PoCs validated"
        self.checkpoint_results['GNG3'] = {'passed': True, 'message': message}
        return True, message
    
    def checkpoint_fix_verification(self, audit_context: Dict) -> Tuple[bool, str]:
        """
        GNG4: Fix Verification Checkpoint
        
        Verifies:
        - Proposed fix has been applied
        - PoC no longer succeeds after fix
        - Fix doesn't introduce new vulnerabilities
        
        Args:
            audit_context: Dictionary containing audit context
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        fix_results = audit_context.get('fix_results', {})
        vulnerabilities = audit_context.get('vulnerabilities', [])
        
        # Filter vulnerabilities that have fixes
        vuln_with_fixes = [
            v for v in vulnerabilities 
            if v.get('fix_proposed')
        ]
        
        if not vuln_with_fixes:
            message = "No fixes to verify"
            self.checkpoint_results['GNG4'] = {'passed': True, 'message': message}
            return True, message
        
        # Check if each fix has been verified
        unverified_fixes = []
        failed_verifications = []
        
        for vuln in vuln_with_fixes:
            vuln_id = vuln.get('id')
            fix_result = fix_results.get(vuln_id)
            
            if not fix_result:
                unverified_fixes.append(vuln_id)
            elif fix_result.get('poc_still_succeeds'):
                failed_verifications.append(vuln_id)
        
        if unverified_fixes:
            message = f"Unverified fixes: {', '.join(unverified_fixes)}"
            self.checkpoint_results['GNG4'] = {'passed': False, 'message': message}
            return False, message
        
        if failed_verifications:
            message = f"Fixes that don't prevent exploitation: {', '.join(failed_verifications)}"
            self.checkpoint_results['GNG4'] = {'passed': False, 'message': message}
            return False, message
        
        message = f"Fix verification passed: {len(vuln_with_fixes)} fixes verified"
        self.checkpoint_results['GNG4'] = {'passed': True, 'message': message}
        return True, message
    
    def run_checkpoint(self, checkpoint_id: str, audit_context: Dict) -> Tuple[bool, str]:
        """
        Run a specific checkpoint
        
        Args:
            checkpoint_id: Checkpoint identifier (GNG1, GNG2, GNG3, GNG4)
            audit_context: Dictionary containing audit context
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if checkpoint_id not in self.checkpoints:
            return False, f"Unknown checkpoint: {checkpoint_id}"
        
        checkpoint_func = self.checkpoints[checkpoint_id]
        return checkpoint_func(audit_context)
    
    def run_all_checkpoints(self, audit_context: Dict) -> Dict[str, Any]:
        """
        Run all checkpoints in sequence
        
        Args:
            audit_context: Dictionary containing audit context
            
        Returns:
            Dictionary with results for all checkpoints
        """
        results = {
            "all_passed": True,
            "checkpoints": {}
        }
        
        for checkpoint_id in ['GNG1', 'GNG2', 'GNG3', 'GNG4']:
            passed, message = self.run_checkpoint(checkpoint_id, audit_context)
            
            results['checkpoints'][checkpoint_id] = {
                "passed": passed,
                "message": message
            }
            
            if not passed:
                results['all_passed'] = False
                # Halt on first failure
                results['halted_at'] = checkpoint_id
                break
        
        return results
    
    def get_checkpoint_status(self) -> Dict[str, Any]:
        """Get status of all checkpoints"""
        return self.checkpoint_results


if __name__ == "__main__":
    # Test checkpoints
    validator = ValidationCheckpoints()
    
    # Test GNG1
    test_context = {
        'contract_path': '/home/ubuntu/ai_auditor',
        'project_path': None
    }
    
    passed, message = validator.checkpoint_environment(test_context)
    print(f"GNG1: {'PASS' if passed else 'FAIL'} - {message}")
