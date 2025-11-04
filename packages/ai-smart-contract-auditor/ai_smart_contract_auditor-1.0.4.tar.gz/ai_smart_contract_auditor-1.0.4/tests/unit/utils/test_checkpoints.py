"""
Comprehensive unit tests for checkpoints.py
Tests all checkpoint validation logic with edge cases and error handling
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from src.utils.checkpoints import ValidationCheckpoints


class TestValidationCheckpointsInit:
    """Test ValidationCheckpoints initialization"""
    
    def test_init_without_config(self):
        """Test initialization without config file"""
        validator = ValidationCheckpoints()
        assert validator.checkpoints is not None
        assert len(validator.checkpoints) == 4
        assert 'GNG1' in validator.checkpoints
        assert validator.config == {}
        assert validator.checkpoint_results == {}
    
    def test_init_with_nonexistent_config(self):
        """Test initialization with nonexistent config file"""
        validator = ValidationCheckpoints(config_path='/nonexistent/config.json')
        assert validator.config == {}
    
    def test_init_with_valid_config(self, tmp_path):
        """Test initialization with valid config file"""
        config_file = tmp_path / "config.json"
        config_data = {"timeout": 120, "required_tools": ["slither"]}
        config_file.write_text(json.dumps(config_data))
        
        validator = ValidationCheckpoints(config_path=str(config_file))
        assert validator.config == config_data


class TestCheckpointEnvironment:
    """Test GNG1: Environment Setup Validation"""
    
    @patch('subprocess.run')
    def test_all_tools_present(self, mock_run):
        """Test when all required tools are installed"""
        mock_run.return_value = Mock(returncode=0)
        
        validator = ValidationCheckpoints()
        context = {'contract_path': __file__}  # Use this file as it exists
        
        passed, message = validator.checkpoint_environment(context)
        assert passed is True
        assert "successfully" in message.lower()
        assert validator.checkpoint_results['GNG1']['passed'] is True
    
    @patch('subprocess.run')
    def test_missing_tools(self, mock_run):
        """Test when required tools are missing"""
        mock_run.return_value = Mock(returncode=1)  # Tool not found
        
        validator = ValidationCheckpoints()
        context = {'contract_path': __file__}
        
        passed, message = validator.checkpoint_environment(context)
        assert passed is False
        assert "Missing required tools" in message
        assert validator.checkpoint_results['GNG1']['passed'] is False
    
    def test_nonexistent_contract_path(self):
        """Test when contract path doesn't exist"""
        validator = ValidationCheckpoints()
        context = {'contract_path': '/nonexistent/contract.sol'}
        
        with patch('subprocess.run', return_value=Mock(returncode=0)):
            passed, message = validator.checkpoint_environment(context)
            assert passed is False
            assert "does not exist" in message
    
    @patch('subprocess.run')
    def test_compilation_failure(self, mock_run):
        """Test when compilation fails"""
        def run_side_effect(cmd, **kwargs):
            if cmd[0] == 'which':
                return Mock(returncode=0)
            elif cmd[0] == 'forge' and cmd[1] == 'build':
                return Mock(returncode=1, stderr="Compilation error")
            return Mock(returncode=0)
        
        mock_run.side_effect = run_side_effect
        
        validator = ValidationCheckpoints()
        context = {
            'contract_path': __file__,
            'project_path': os.path.dirname(__file__)
        }
        
        passed, message = validator.checkpoint_environment(context)
        assert passed is False
        assert "Compilation failed" in message
    
    @patch('subprocess.run')
    def test_compilation_timeout(self, mock_run):
        """Test when compilation times out"""
        def run_side_effect(cmd, **kwargs):
            if cmd[0] == 'which':
                return Mock(returncode=0)
            elif cmd[0] == 'forge':
                raise subprocess.TimeoutExpired(cmd, 120)
            return Mock(returncode=0)
        
        mock_run.side_effect = run_side_effect
        
        validator = ValidationCheckpoints()
        context = {
            'contract_path': __file__,
            'project_path': os.path.dirname(__file__)
        }
        
        passed, message = validator.checkpoint_environment(context)
        assert passed is False
        assert "Compilation check failed" in message


class TestCheckpointToolExecution:
    """Test GNG2: Automated Tool Execution Checkpoint"""
    
    def test_all_tools_successful(self):
        """Test when all tools executed successfully"""
        validator = ValidationCheckpoints()
        context = {
            'tool_results': {
                'slither': {
                    'success': True,
                    'findings': [{'type': 'reentrancy', 'severity': 'HIGH'}]
                }
            }
        }
        
        passed, message = validator.checkpoint_tool_execution(context)
        assert passed is True
        assert "1 tools run" in message
        assert "1 findings" in message
    
    def test_missing_tool_results(self):
        """Test when required tool results are missing"""
        validator = ValidationCheckpoints()
        context = {'tool_results': {}}
        
        passed, message = validator.checkpoint_tool_execution(context)
        assert passed is False
        assert "Missing or failed tool results" in message
    
    def test_tool_execution_failed(self):
        """Test when tool execution failed"""
        validator = ValidationCheckpoints()
        context = {
            'tool_results': {
                'slither': {'success': False, 'error': 'Tool crashed'}
            }
        }
        
        passed, message = validator.checkpoint_tool_execution(context)
        assert passed is False
        assert "failed" in message.lower()
    
    def test_multiple_tools_with_findings(self):
        """Test with multiple tools and findings"""
        validator = ValidationCheckpoints()
        context = {
            'tool_results': {
                'slither': {
                    'success': True,
                    'findings': [
                        {'type': 'reentrancy', 'severity': 'HIGH'},
                        {'type': 'overflow', 'severity': 'MEDIUM'}
                    ]
                },
                'mythril': {
                    'success': True,
                    'findings': [{'type': 'unchecked-call', 'severity': 'LOW'}]
                }
            }
        }
        
        passed, message = validator.checkpoint_tool_execution(context)
        assert passed is True
        assert "2 tools run" in message
        assert "3 findings" in message


class TestCheckpointPocWorking:
    """Test GNG3: PoC Validation Checkpoint"""
    
    def test_no_vulnerabilities_requiring_poc(self):
        """Test when no vulnerabilities require PoC"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'LOW'}
            ],
            'poc_results': {}
        }
        
        passed, message = validator.checkpoint_poc_working(context)
        assert passed is True
        assert "No vulnerabilities requiring PoC" in message
    
    def test_all_pocs_successful(self):
        """Test when all PoCs are successful"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'HIGH'},
                {'id': 'V2', 'severity': 'MEDIUM'}
            ],
            'poc_results': {
                'V1': {
                    'exploitation_successful': True,
                    'funds_stolen': True
                },
                'V2': {
                    'exploitation_successful': True,
                    'state_corrupted': True
                }
            }
        }
        
        passed, message = validator.checkpoint_poc_working(context)
        assert passed is True
        assert "2 PoCs validated" in message
    
    def test_missing_poc(self):
        """Test when PoC is missing for vulnerability"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'HIGH'}
            ],
            'poc_results': {}
        }
        
        passed, message = validator.checkpoint_poc_working(context)
        assert passed is False
        assert "Missing PoCs" in message
        assert "V1" in message
    
    def test_failed_poc_exploitation(self):
        """Test when PoC exploitation fails"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'HIGH'}
            ],
            'poc_results': {
                'V1': {'exploitation_successful': False}
            }
        }
        
        passed, message = validator.checkpoint_poc_working(context)
        assert passed is False
        assert "Failed PoCs" in message
    
    def test_poc_without_impact_demonstration(self):
        """Test when PoC doesn't demonstrate actual impact"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'HIGH'}
            ],
            'poc_results': {
                'V1': {
                    'exploitation_successful': True,
                    'funds_stolen': False,
                    'state_corrupted': False
                }
            }
        }
        
        passed, message = validator.checkpoint_poc_working(context)
        assert passed is False
        assert "does not demonstrate actual exploitation" in message


class TestCheckpointFixVerification:
    """Test GNG4: Fix Verification Checkpoint"""
    
    def test_no_fixes_to_verify(self):
        """Test when no fixes need verification"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'HIGH', 'fix_proposed': False}
            ],
            'fix_results': {}
        }
        
        passed, message = validator.checkpoint_fix_verification(context)
        assert passed is True
        assert "No fixes to verify" in message
    
    def test_all_fixes_verified(self):
        """Test when all fixes are verified successfully"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'HIGH', 'fix_proposed': True},
                {'id': 'V2', 'severity': 'MEDIUM', 'fix_proposed': True}
            ],
            'fix_results': {
                'V1': {'poc_still_succeeds': False},
                'V2': {'poc_still_succeeds': False}
            }
        }
        
        passed, message = validator.checkpoint_fix_verification(context)
        assert passed is True
        assert "2 fixes verified" in message
    
    def test_unverified_fix(self):
        """Test when fix is not verified"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'HIGH', 'fix_proposed': True}
            ],
            'fix_results': {}
        }
        
        passed, message = validator.checkpoint_fix_verification(context)
        assert passed is False
        assert "Unverified fixes" in message
        assert "V1" in message
    
    def test_fix_doesnt_prevent_exploitation(self):
        """Test when fix doesn't prevent exploitation"""
        validator = ValidationCheckpoints()
        context = {
            'vulnerabilities': [
                {'id': 'V1', 'severity': 'HIGH', 'fix_proposed': True}
            ],
            'fix_results': {
                'V1': {'poc_still_succeeds': True}
            }
        }
        
        passed, message = validator.checkpoint_fix_verification(context)
        assert passed is False
        assert "don't prevent exploitation" in message


class TestRunCheckpoint:
    """Test run_checkpoint method"""
    
    @patch('subprocess.run')
    def test_run_valid_checkpoint(self, mock_run):
        """Test running a valid checkpoint"""
        mock_run.return_value = Mock(returncode=0)
        
        validator = ValidationCheckpoints()
        context = {'contract_path': __file__}
        
        passed, message = validator.run_checkpoint('GNG1', context)
        assert isinstance(passed, bool)
        assert isinstance(message, str)
    
    def test_run_invalid_checkpoint(self):
        """Test running an invalid checkpoint"""
        validator = ValidationCheckpoints()
        context = {}
        
        passed, message = validator.run_checkpoint('INVALID', context)
        assert passed is False
        assert "Unknown checkpoint" in message


class TestRunAllCheckpoints:
    """Test run_all_checkpoints method"""
    
    @patch('subprocess.run')
    def test_all_checkpoints_pass(self, mock_run):
        """Test when all checkpoints pass"""
        mock_run.return_value = Mock(returncode=0)
        
        validator = ValidationCheckpoints()
        context = {
            'contract_path': __file__,
            'tool_results': {
                'slither': {'success': True, 'findings': []}
            },
            'vulnerabilities': [],
            'poc_results': {},
            'fix_results': {}
        }
        
        results = validator.run_all_checkpoints(context)
        assert results['all_passed'] is True
        assert len(results['checkpoints']) == 4
        assert 'halted_at' not in results
    
    @patch('subprocess.run')
    def test_halt_on_first_failure(self, mock_run):
        """Test that execution halts on first failure"""
        mock_run.return_value = Mock(returncode=1)  # Fail GNG1
        
        validator = ValidationCheckpoints()
        context = {'contract_path': __file__}
        
        results = validator.run_all_checkpoints(context)
        assert results['all_passed'] is False
        assert results['halted_at'] == 'GNG1'
        assert len(results['checkpoints']) == 1  # Only GNG1 ran


class TestGetCheckpointStatus:
    """Test get_checkpoint_status method"""
    
    @patch('subprocess.run')
    def test_get_status_after_checkpoints(self, mock_run):
        """Test getting checkpoint status after running checkpoints"""
        mock_run.return_value = Mock(returncode=0)
        
        validator = ValidationCheckpoints()
        context = {'contract_path': __file__}
        
        validator.checkpoint_environment(context)
        status = validator.get_checkpoint_status()
        
        assert 'GNG1' in status
        assert status['GNG1']['passed'] is True


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_context(self):
        """Test with empty audit context"""
        validator = ValidationCheckpoints()
        context = {}
        
        # Should handle gracefully
        passed, message = validator.checkpoint_tool_execution(context)
        assert passed is False
    
    def test_none_values_in_context(self):
        """Test with None values in context"""
        validator = ValidationCheckpoints()
        context = {
            'contract_path': None,
            'tool_results': None,
            'vulnerabilities': None
        }
        
        # Should handle None gracefully
        with patch('subprocess.run', return_value=Mock(returncode=0)):
            passed, message = validator.checkpoint_environment(context)
            # Should pass since contract_path is None (not checked)
            assert isinstance(passed, bool)
    
    def test_malformed_tool_results(self):
        """Test with malformed tool results"""
        validator = ValidationCheckpoints()
        context = {
            'tool_results': {
                'slither': "invalid_format"  # Should be dict
            }
        }
        
        # Should raise AttributeError for malformed data
        with pytest.raises(AttributeError):
            validator.checkpoint_tool_execution(context)
