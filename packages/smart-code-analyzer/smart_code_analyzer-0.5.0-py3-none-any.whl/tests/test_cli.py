"""Tests for CLI interface."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from click.testing import CliRunner
from code_analyzer.cli import main, analyze


class TestCLI(unittest.TestCase):
    """Test command-line interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test main command help output."""
        result = self.runner.invoke(main, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Code Analyzer', result.output)
    
    def test_analyze_help(self):
        """Test analyze command help output."""
        result = self.runner.invoke(main, ['analyze', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('project_path', result.output.lower())
    
    @patch('code_analyzer.cli.CodeAnalyzer')
    def test_analyze_basic(self, mock_analyzer_class):
        """Test basic analyze command."""
        # Create mock analyzer
        mock_analyzer = Mock()
        mock_result = Mock()
        mock_result.modules = []
        mock_result.issues = []
        mock_result.metrics.total_files = 0
        mock_analyzer.analyze.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer
        
        # Run with temporary directory
        with self.runner.isolated_filesystem():
            Path('test_project').mkdir()
            Path('test_project/test.py').write_text('print("hello")')
            
            result = self.runner.invoke(main, [
                'analyze',
                'test_project',
                '--depth', 'shallow',
                '--output', '.code-analyzer'
            ])
            
            # Should complete without error
            self.assertEqual(result.exit_code, 0)
            # Analyzer should be created
            mock_analyzer_class.assert_called_once()
            # Analysis should run
            mock_analyzer.analyze.assert_called_once()
    
    @patch('code_analyzer.cli.CodeAnalyzer')
    def test_analyze_with_depth(self, mock_analyzer_class):
        """Test analyze with different depth levels."""
        mock_analyzer = Mock()
        mock_result = Mock()
        mock_result.modules = []
        mock_result.issues = []
        mock_result.metrics.total_files = 0
        mock_analyzer.analyze.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer
        
        with self.runner.isolated_filesystem():
            Path('test_project').mkdir()
            Path('test_project/test.py').write_text('def foo(): pass')
            
            for depth in ['shallow', 'medium', 'deep']:
                result = self.runner.invoke(main, [
                    'analyze',
                    'test_project',
                    '--depth', depth
                ])
                
                # Check depth was passed
                call_kwargs = mock_analyzer.analyze.call_args[1]
                self.assertEqual(call_kwargs['depth'], depth)
    
    def test_analyze_nonexistent_path(self):
        """Test analyze with non-existent path."""
        result = self.runner.invoke(main, [
            'analyze',
            '/nonexistent/path'
        ])
        
        # Should fail gracefully
        self.assertNotEqual(result.exit_code, 0)


class TestCLIConfiguration(unittest.TestCase):
    """Test CLI configuration loading."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('code_analyzer.cli.CodeAnalyzer')
    def test_config_file_loading(self, mock_analyzer_class):
        """Test loading configuration from YAML file."""
        mock_analyzer = Mock()
        mock_result = Mock()
        mock_result.modules = []
        mock_result.issues = []
        mock_result.metrics.total_files = 0
        mock_analyzer.analyze.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer
        
        with self.runner.isolated_filesystem():
            # Create test project
            Path('test_project').mkdir()
            Path('test_project/test.py').write_text('def test(): pass')
            
            # Create config file
            config_content = '''
analysis:
  depth: shallow
  ignore_patterns:
    - "*/test/*"
'''
            Path('test_project/.code-analyzer.yaml').write_text(config_content)
            
            result = self.runner.invoke(main, [
                'analyze',
                'test_project'
            ])
            
            self.assertEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
