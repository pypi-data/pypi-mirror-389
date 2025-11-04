"""Tests for data models."""

import pytest
from code_analyzer.models import (
    CodeLocation, Issue, IssueType, IssueSeverity,
    FunctionInfo, ClassInfo, ModuleInfo
)


class TestCodeLocation:
    """Tests for CodeLocation model."""
    
    def test_create_location(self):
        """Test creating a code location."""
        loc = CodeLocation(
            file_path="test.py",
            line_start=10,
            line_end=20
        )
        assert loc.file_path == "test.py"
        assert loc.line_start == 10
        assert loc.line_end == 20
    
    def test_location_str(self):
        """Test string representation of location."""
        loc = CodeLocation(
            file_path="test.py",
            line_start=10,
            line_end=10
        )
        assert str(loc) == "test.py:10"
        
        loc_range = CodeLocation(
            file_path="test.py",
            line_start=10,
            line_end=20
        )
        assert str(loc_range) == "test.py:10-20"
    
    def test_location_with_function(self):
        """Test location with function name."""
        loc = CodeLocation(
            file_path="test.py",
            line_start=10,
            line_end=10,
            function_name="test_func"
        )
        assert "test_func()" in str(loc)


class TestIssue:
    """Tests for Issue model."""
    
    def test_create_issue(self):
        """Test creating an issue."""
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=1)
        issue = Issue(
            issue_type=IssueType.BUG,
            severity=IssueSeverity.HIGH,
            title="Test Bug",
            description="This is a test bug",
            location=loc
        )
        assert issue.title == "Test Bug"
        assert issue.severity == IssueSeverity.HIGH
    
    def test_issue_to_dict(self):
        """Test converting issue to dictionary."""
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=1)
        issue = Issue(
            issue_type=IssueType.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="Security Issue",
            description="Test",
            location=loc,
            recommendation="Fix it"
        )
        issue_dict = issue.to_dict()
        assert issue_dict["type"] == "security"
        assert issue_dict["severity"] == "critical"
        assert issue_dict["recommendation"] == "Fix it"


class TestFunctionInfo:
    """Tests for FunctionInfo model."""
    
    def test_create_function(self):
        """Test creating function info."""
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=5)
        func = FunctionInfo(
            name="test_function",
            location=loc,
            parameters=["arg1", "arg2"],
            return_type="int",
            docstring="Test function",
            complexity=2
        )
        assert func.name == "test_function"
        assert len(func.parameters) == 2
        assert func.complexity == 2
    
    def test_function_with_source(self):
        """Test function with source code."""
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=5)
        func = FunctionInfo(
            name="test_function",
            location=loc,
            parameters=[],
            return_type=None,
            docstring=None,
            complexity=1,
            source_code="def test_function():\n    pass"
        )
        assert func.source_code is not None
        assert "def test_function" in func.source_code


class TestClassInfo:
    """Tests for ClassInfo model."""
    
    def test_create_class(self):
        """Test creating class info."""
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=10)
        cls = ClassInfo(
            name="TestClass",
            location=loc,
            bases=["object"],
            docstring="Test class"
        )
        assert cls.name == "TestClass"
        assert len(cls.bases) == 1
        assert cls.bases[0] == "object"
    
    def test_class_with_methods(self):
        """Test class with methods."""
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=10)
        method_loc = CodeLocation(file_path="test.py", line_start=5, line_end=7)
        method = FunctionInfo(
            name="test_method",
            location=method_loc,
            parameters=["self"],
            return_type=None,
            docstring=None,
            complexity=1
        )
        cls = ClassInfo(
            name="TestClass",
            location=loc,
            bases=[],
            docstring="Test class",
            methods=[method]
        )
        assert len(cls.methods) == 1
        assert cls.methods[0].name == "test_method"


class TestModuleInfo:
    """Tests for ModuleInfo model."""
    
    def test_create_module(self):
        """Test creating module info."""
        module = ModuleInfo(
            name="test_module",
            file_path="test.py",
            docstring="Test module"
        )
        assert module.name == "test_module"
        assert module.file_path == "test.py"
    
    def test_module_with_functions(self):
        """Test module with functions."""
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=5)
        func = FunctionInfo(
            name="test_function",
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
        assert len(module.functions) == 1
        assert module.functions[0].name == "test_function"
    
    def test_module_with_imports(self):
        """Test module with imports."""
        module = ModuleInfo(
            name="test_module",
            file_path="test.py",
            docstring=None,
            imports=["os", "sys", "pathlib"]
        )
        assert len(module.imports) == 3
        assert "os" in module.imports
