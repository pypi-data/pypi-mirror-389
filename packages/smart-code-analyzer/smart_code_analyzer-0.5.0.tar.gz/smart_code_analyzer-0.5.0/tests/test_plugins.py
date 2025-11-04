"""Tests for plugin system."""

import pytest
from pathlib import Path
from code_analyzer.plugins import (
    AnalyzerPlugin, CustomRulePlugin, PluginManager,
    NamingConventionPlugin, LoggingBestPracticesPlugin
)
from code_analyzer.models import (
    ModuleInfo, FunctionInfo, ClassInfo, Issue, 
    IssueType, IssueSeverity, CodeLocation
)


class TestAnalyzerPlugin:
    """Tests for AnalyzerPlugin base class."""
    
    def test_plugin_interface(self):
        """Test that plugin interface is properly defined."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            AnalyzerPlugin()
    
    def test_custom_plugin_implementation(self):
        """Test creating a custom plugin."""
        
        class TestPlugin(AnalyzerPlugin):
            @property
            def name(self):
                return "test-plugin"
            
            @property
            def version(self):
                return "1.0.0"
            
            def analyze_module(self, module):
                return []
        
        plugin = TestPlugin()
        assert plugin.name == "test-plugin"
        assert plugin.version == "1.0.0"
        
        # Test hooks have default implementations
        plugin.pre_analysis_hook([])
        plugin.post_analysis_hook([], [])
        findings = plugin.generate_custom_findings([])
        assert findings == {}


class TestCustomRulePlugin:
    """Tests for CustomRulePlugin."""
    
    def test_create_rule_plugin(self):
        """Test creating a rule-based plugin."""
        
        class TestRulePlugin(CustomRulePlugin):
            @property
            def name(self):
                return "test-rules"
            
            @property
            def version(self):
                return "1.0.0"
            
            def __init__(self):
                super().__init__()
                self.add_rule(
                    name="test-rule",
                    check=lambda obj: hasattr(obj, 'name') and obj.name == "bad_name",
                    severity=IssueSeverity.LOW,
                    message="Bad naming",
                    recommendation="Use better name"
                )
        
        plugin = TestRulePlugin()
        assert len(plugin.rules) == 1
        assert plugin.rules[0]['name'] == "test-rule"
    
    def test_rule_matches_function(self):
        """Test that rules can match functions."""
        
        class TestPlugin(CustomRulePlugin):
            @property
            def name(self):
                return "test"
            
            @property
            def version(self):
                return "1.0.0"
            
            def __init__(self):
                super().__init__()
                self.add_rule(
                    name="short-name",
                    check=lambda obj: hasattr(obj, 'name') and len(obj.name) < 3,
                    severity=IssueSeverity.LOW,
                    message="Name too short"
                )
        
        plugin = TestPlugin()
        
        # Create test module with short function name
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=5)
        func = FunctionInfo(
            name="ab",  # Too short
            location=loc,
            parameters=[],
            return_type=None,
            docstring=None,
            complexity=1
        )
        module = ModuleInfo(
            name="test_module",
            file_path="test.py",
            docstring=None,
            functions=[func]
        )
        
        issues = plugin.analyze_module(module)
        assert len(issues) == 1
        assert "short-name" in issues[0].title
    
    def test_rule_matches_class(self):
        """Test that rules can match classes."""
        
        class TestPlugin(CustomRulePlugin):
            @property
            def name(self):
                return "test"
            
            @property
            def version(self):
                return "1.0.0"
            
            def __init__(self):
                super().__init__()
                self.add_rule(
                    name="lowercase-class",
                    check=lambda obj: hasattr(obj, 'name') and obj.name[0].islower(),
                    severity=IssueSeverity.MEDIUM,
                    message="Class should start with uppercase"
                )
        
        plugin = TestPlugin()
        
        # Create test module with lowercase class
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=10)
        cls = ClassInfo(
            name="badClass",  # Should be BadClass
            location=loc,
            bases=[],
            docstring=None
        )
        module = ModuleInfo(
            name="test_module",
            file_path="test.py",
            docstring=None,
            classes=[cls]
        )
        
        issues = plugin.analyze_module(module)
        # May match both module and class, filter for class issues
        class_issues = [i for i in issues if 'badClass' in str(i.location) or i.location.line_start != 1 or i.location.line_end != 1]
        assert len(class_issues) >= 1
        assert class_issues[0].severity == IssueSeverity.MEDIUM


class TestPluginManager:
    """Tests for PluginManager."""
    
    def test_register_plugin(self):
        """Test registering a plugin."""
        
        class TestPlugin(AnalyzerPlugin):
            @property
            def name(self):
                return "test"
            
            @property
            def version(self):
                return "1.0.0"
            
            def analyze_module(self, module):
                return []
        
        manager = PluginManager()
        plugin = TestPlugin()
        
        assert len(manager.plugins) == 0
        manager.register_plugin(plugin)
        assert len(manager.plugins) == 1
        assert manager.plugins[0].name == "test"
    
    def test_run_analysis(self):
        """Test running analysis with plugins."""
        
        class IssuePlugin(CustomRulePlugin):
            @property
            def name(self):
                return "issue-generator"
            
            @property
            def version(self):
                return "1.0.0"
            
            def __init__(self):
                super().__init__()
                self.add_rule(
                    name="always-trigger",
                    check=lambda obj: True,
                    severity=IssueSeverity.INFO,
                    message="Test issue"
                )
        
        manager = PluginManager()
        manager.register_plugin(IssuePlugin())
        
        # Create test module
        module = ModuleInfo(
            name="test",
            file_path="test.py",
            docstring=None
        )
        
        issues = manager.run_analysis([module])
        assert len(issues) >= 1  # At least one issue from the rule
    
    def test_pre_analysis_hooks(self):
        """Test pre-analysis hooks are called."""
        
        class HookPlugin(AnalyzerPlugin):
            def __init__(self):
                self.pre_called = False
            
            @property
            def name(self):
                return "hook-test"
            
            @property
            def version(self):
                return "1.0.0"
            
            def analyze_module(self, module):
                return []
            
            def pre_analysis_hook(self, modules):
                self.pre_called = True
        
        manager = PluginManager()
        plugin = HookPlugin()
        manager.register_plugin(plugin)
        
        assert not plugin.pre_called
        manager.run_pre_analysis_hooks([])
        assert plugin.pre_called
    
    def test_post_analysis_hooks(self):
        """Test post-analysis hooks are called."""
        
        class HookPlugin(AnalyzerPlugin):
            def __init__(self):
                self.post_called = False
            
            @property
            def name(self):
                return "hook-test"
            
            @property
            def version(self):
                return "1.0.0"
            
            def analyze_module(self, module):
                return []
            
            def post_analysis_hook(self, modules, issues):
                self.post_called = True
        
        manager = PluginManager()
        plugin = HookPlugin()
        manager.register_plugin(plugin)
        
        assert not plugin.post_called
        manager.run_post_analysis_hooks([], [])
        assert plugin.post_called
    
    def test_custom_findings(self):
        """Test custom findings generation."""
        
        class FindingsPlugin(AnalyzerPlugin):
            @property
            def name(self):
                return "findings-test"
            
            @property
            def version(self):
                return "1.0.0"
            
            def analyze_module(self, module):
                return []
            
            def generate_custom_findings(self, modules):
                return {"test_metric": 42}
        
        manager = PluginManager()
        manager.register_plugin(FindingsPlugin())
        
        findings = manager.generate_custom_findings([])
        assert "findings-test" in findings
        assert findings["findings-test"]["test_metric"] == 42


class TestBuiltInPlugins:
    """Tests for built-in plugins."""
    
    def test_naming_convention_plugin(self):
        """Test naming convention plugin."""
        plugin = NamingConventionPlugin()
        
        assert plugin.name == "naming-conventions"
        assert len(plugin.rules) >= 1
        
        # Test it detects lowercase class names
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=5)
        cls = ClassInfo(
            name="myclass",  # Should be MyClass
            location=loc,
            bases=[],
            docstring=None
        )
        module = ModuleInfo(
            name="test",
            file_path="test.py",
            docstring=None,
            classes=[cls]
        )
        
        issues = plugin.analyze_module(module)
        # Should find at least the class naming issue
        assert len(issues) >= 1
    
    def test_logging_best_practices_plugin(self):
        """Test logging best practices plugin."""
        plugin = LoggingBestPracticesPlugin()
        
        assert plugin.name == "logging-practices"
        assert len(plugin.rules) >= 1


class TestPluginErrorHandling:
    """Tests for plugin error handling."""
    
    def test_plugin_exception_handling(self):
        """Test that plugin exceptions don't crash the manager."""
        
        class BrokenPlugin(AnalyzerPlugin):
            @property
            def name(self):
                return "broken"
            
            @property
            def version(self):
                return "1.0.0"
            
            def analyze_module(self, module):
                raise Exception("Plugin is broken!")
        
        manager = PluginManager()
        manager.register_plugin(BrokenPlugin())
        
        module = ModuleInfo(
            name="test",
            file_path="test.py",
            docstring=None
        )
        
        # Should not raise exception, just return empty list
        issues = manager.run_analysis([module])
        assert isinstance(issues, list)
