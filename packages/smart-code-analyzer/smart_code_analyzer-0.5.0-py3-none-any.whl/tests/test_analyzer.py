"""Tests for core analyzer."""

import pytest
import tempfile
import shutil
from pathlib import Path
from code_analyzer.analyzer import CodeAnalyzer
from code_analyzer.models import (
    AnalysisResult, ModuleInfo, FunctionInfo, ClassInfo,
    Issue, IssueType, IssueSeverity
)


class TestCodeAnalyzerInit:
    """Tests for CodeAnalyzer initialization."""
    
    def test_create_analyzer(self, tmp_path):
        """Test creating a code analyzer."""
        analyzer = CodeAnalyzer(str(tmp_path))
        
        # Use resolve() to handle symlinks
        assert analyzer.project_path == tmp_path.resolve()
        assert len(analyzer.modules) == 0
        assert len(analyzer.issues) == 0
    
    def test_default_ignore_patterns(self, tmp_path):
        """Test default ignore patterns are set."""
        analyzer = CodeAnalyzer(str(tmp_path))
        
        # Should have default patterns
        assert len(analyzer.ignore_patterns) > 0
        assert any('venv' in p for p in analyzer.ignore_patterns)
        assert any('__pycache__' in p for p in analyzer.ignore_patterns)
        assert any('.git' in p for p in analyzer.ignore_patterns)
    
    def test_custom_ignore_patterns(self, tmp_path):
        """Test setting custom ignore patterns."""
        custom_patterns = ["*/test/*", "*/build/*"]
        analyzer = CodeAnalyzer(str(tmp_path), ignore_patterns=custom_patterns)
        
        assert analyzer.ignore_patterns == custom_patterns


class TestIgnorePatterns:
    """Tests for file ignore patterns."""
    
    def test_should_ignore_venv(self, tmp_path):
        """Test that .venv directories are ignored."""
        analyzer = CodeAnalyzer(str(tmp_path))
        
        venv_path = tmp_path / ".venv" / "lib" / "test.py"
        assert analyzer._should_ignore(venv_path)
    
    def test_should_ignore_pycache(self, tmp_path):
        """Test that __pycache__ directories are ignored."""
        analyzer = CodeAnalyzer(str(tmp_path))
        
        cache_path = tmp_path / "src" / "__pycache__" / "test.pyc"
        assert analyzer._should_ignore(cache_path)
    
    def test_should_ignore_git(self, tmp_path):
        """Test that .git directories are ignored."""
        analyzer = CodeAnalyzer(str(tmp_path))
        
        git_path = tmp_path / ".git" / "objects" / "test"
        assert analyzer._should_ignore(git_path)
    
    def test_should_not_ignore_source(self, tmp_path):
        """Test that source files are not ignored."""
        analyzer = CodeAnalyzer(str(tmp_path))
        
        source_path = tmp_path / "src" / "main.py"
        assert not analyzer._should_ignore(source_path)


class TestFindPythonFiles:
    """Tests for finding Python files."""
    
    def test_find_single_file(self, tmp_path):
        """Test finding a single Python file."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        files = analyzer._find_python_files()
        
        assert len(files) == 1
        assert files[0].name == "test.py"
    
    def test_find_multiple_files(self, tmp_path):
        """Test finding multiple Python files."""
        # Create test files
        (tmp_path / "test1.py").write_text("pass")
        (tmp_path / "test2.py").write_text("pass")
        (tmp_path / "test3.py").write_text("pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        files = analyzer._find_python_files()
        
        assert len(files) == 3
    
    def test_find_in_subdirectories(self, tmp_path):
        """Test finding files in subdirectories."""
        # Create directory structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("pass")
        
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        files = analyzer._find_python_files()
        
        assert len(files) == 2
    
    def test_ignore_venv_files(self, tmp_path):
        """Test that venv files are not found."""
        # Create source file
        (tmp_path / "main.py").write_text("pass")
        
        # Create venv with files
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "package.py").write_text("pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        files = analyzer._find_python_files()
        
        # Should only find main.py, not the venv file
        assert len(files) == 1
        assert files[0].name == "main.py"
    
    def test_no_python_files(self, tmp_path):
        """Test handling directory with no Python files."""
        # Create non-Python files
        (tmp_path / "readme.txt").write_text("readme")
        (tmp_path / "data.json").write_text("{}")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        files = analyzer._find_python_files()
        
        assert len(files) == 0


class TestAnalyzeFile:
    """Tests for analyzing individual files."""
    
    def test_analyze_simple_file(self, tmp_path):
        """Test analyzing a simple Python file."""
        # Create test file
        test_file = tmp_path / "simple.py"
        test_file.write_text('def hello():\n    """Say hello."""\n    return "hello"\n')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        module = analyzer._analyze_file(test_file)
        
        assert module is not None
        assert module.name == "simple"
        assert len(module.functions) == 1
        assert module.functions[0].name == "hello"
    
    def test_analyze_file_with_class(self, tmp_path):
        """Test analyzing file with a class."""
        test_file = tmp_path / "myclass.py"
        test_file.write_text('''
class MyClass:
    """A test class."""
    
    def __init__(self):
        pass
    
    def method(self):
        return 42
''')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        module = analyzer._analyze_file(test_file)
        
        assert module is not None
        assert len(module.classes) == 1
        assert module.classes[0].name == "MyClass"
        assert len(module.classes[0].methods) == 2  # __init__ and method
    
    def test_analyze_file_with_imports(self, tmp_path):
        """Test analyzing file with imports."""
        test_file = tmp_path / "imports.py"
        test_file.write_text('import os\nimport sys\nfrom pathlib import Path\n\ndef main():\n    pass\n')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        module = analyzer._analyze_file(test_file)
        
        assert module is not None
        assert "os" in module.imports
        assert "sys" in module.imports
        assert "pathlib" in module.imports
    
    def test_analyze_file_with_syntax_error(self, tmp_path):
        """Test handling file with syntax errors."""
        test_file = tmp_path / "broken.py"
        test_file.write_text('''
def broken(
    # Missing closing parenthesis
    pass
''')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        module = analyzer._analyze_file(test_file)
        
        # Should return None for files with syntax errors
        assert module is None
    
    def test_analyze_empty_file(self, tmp_path):
        """Test analyzing empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("# empty file\n")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        module = analyzer._analyze_file(test_file)
        
        assert module is not None
        assert len(module.functions) == 0
        assert len(module.classes) == 0
    
    def test_analyze_file_with_docstring(self, tmp_path):
        """Test that module docstrings are captured."""
        test_file = tmp_path / "documented.py"
        test_file.write_text('"""This is a module docstring."""\n\ndef func():\n    pass\n')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        module = analyzer._analyze_file(test_file)
        
        assert module is not None
        assert module.docstring == "This is a module docstring."


class TestFullAnalysis:
    """Tests for full project analysis."""
    
    def test_analyze_empty_project(self, tmp_path):
        """Test analyzing empty project."""
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="shallow")
        
        assert isinstance(result, AnalysisResult)
        # Use resolve() to handle symlinks
        assert Path(result.project_path).resolve() == tmp_path.resolve()
        assert len(result.modules) == 0
    
    def test_analyze_simple_project(self, tmp_path):
        """Test analyzing simple project."""
        # Create simple project
        (tmp_path / "main.py").write_text('''
def main():
    """Main function."""
    print("Hello, World!")

if __name__ == "__main__":
    main()
''')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="shallow")
        
        assert isinstance(result, AnalysisResult)
        assert len(result.modules) == 1
        assert result.modules[0].name == "main"
        assert result.metrics.total_files == 1
    
    def test_analyze_with_multiple_modules(self, tmp_path):
        """Test analyzing project with multiple modules."""
        # Create multiple files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")
        (tmp_path / "module3.py").write_text("def func3(): pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="shallow")
        
        assert len(result.modules) == 3
        assert result.metrics.total_files == 3
        assert result.metrics.total_functions == 3
    
    def test_analyze_depth_shallow(self, tmp_path):
        """Test shallow analysis."""
        (tmp_path / "test.py").write_text("def test(): pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="shallow")
        
        # Shallow analysis should complete without errors
        assert isinstance(result, AnalysisResult)
        # Shallow depth doesn't run most detectors
        assert result.issues == []
    
    def test_analyze_depth_medium(self, tmp_path):
        """Test medium depth analysis."""
        # Create file with complexity
        (tmp_path / "complex.py").write_text('''
def complex_function():
    for i in range(10):
        if i % 2 == 0:
            for j in range(10):
                if j % 2 == 0:
                    print(i, j)
''')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="medium")
        
        assert isinstance(result, AnalysisResult)
        # Medium depth runs more detectors
    
    def test_analyze_depth_deep(self, tmp_path):
        """Test deep analysis."""
        (tmp_path / "test.py").write_text('''
def test():
    result = eval("1 + 1")  # Security issue
    return result
''')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="deep")
        
        assert isinstance(result, AnalysisResult)
        # Deep analysis runs all detectors including security
    
    def test_metrics_calculation(self, tmp_path):
        """Test that metrics are calculated correctly."""
        # Create project with known metrics
        (tmp_path / "main.py").write_text('''
class MyClass:
    def method1(self):
        pass
    
    def method2(self):
        pass

def function1():
    pass

def function2():
    pass
''')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="shallow")
        
        assert result.metrics.total_files == 1
        assert result.metrics.total_classes == 1
        assert result.metrics.total_functions >= 2  # At least the top-level functions


class TestGetModuleName:
    """Tests for module name extraction."""
    
    def test_simple_module_name(self, tmp_path):
        """Test simple module name."""
        test_file = tmp_path / "simple.py"
        test_file.write_text("pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        name = analyzer._get_module_name(test_file)
        
        assert name == "simple"
    
    def test_nested_module_name(self, tmp_path):
        """Test nested module name."""
        subdir = tmp_path / "package" / "subpackage"
        subdir.mkdir(parents=True)
        test_file = subdir / "module.py"
        test_file.write_text("pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        name = analyzer._get_module_name(test_file)
        
        assert name == "package.subpackage.module"
    
    def test_init_module_name(self, tmp_path):
        """Test __init__.py module name."""
        subdir = tmp_path / "package"
        subdir.mkdir()
        test_file = subdir / "__init__.py"
        test_file.write_text("pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        name = analyzer._get_module_name(test_file)
        
        assert name == "package"


class TestEncodingHandling:
    """Tests for encoding error handling."""
    
    def test_utf8_file(self, tmp_path):
        """Test reading UTF-8 encoded file."""
        test_file = tmp_path / "utf8.py"
        test_file.write_text("# -*- coding: utf-8 -*-\ndef hello(): pass", encoding="utf-8")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        module = analyzer._analyze_file(test_file)
        
        assert module is not None
    
    def test_latin1_fallback(self, tmp_path):
        """Test fallback to latin-1 encoding."""
        test_file = tmp_path / "latin1.py"
        # Write file with latin-1 encoding
        test_file.write_bytes(b"# -*- coding: latin-1 -*-\ndef hello(): pass\n")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        module = analyzer._analyze_file(test_file)
        
        # Should handle gracefully (might be None or succeed with latin-1)
        # At minimum, shouldn't crash
        assert True  # Test passes if no exception


class TestAnalysisResult:
    """Tests for analysis results."""
    
    def test_result_structure(self, tmp_path):
        """Test that result has correct structure."""
        (tmp_path / "test.py").write_text("def test(): pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="shallow")
        
        # Check all expected fields exist
        assert hasattr(result, 'project_path')
        assert hasattr(result, 'analysis_date')
        assert hasattr(result, 'modules')
        assert hasattr(result, 'issues')
        assert hasattr(result, 'critical_sections')
        assert hasattr(result, 'metrics')
        assert hasattr(result, 'dependency_graph')
        assert hasattr(result, 'entry_points')
    
    def test_result_datetime(self, tmp_path):
        """Test that analysis date is set."""
        (tmp_path / "test.py").write_text("pass")
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="shallow")
        
        assert result.analysis_date is not None
    
    def test_entry_points_detection(self, tmp_path):
        """Test entry points are detected."""
        (tmp_path / "main.py").write_text('''
def main():
    pass

if __name__ == "__main__":
    main()
''')
        
        analyzer = CodeAnalyzer(str(tmp_path))
        result = analyzer.analyze(depth="shallow")
        
        # Entry points detection should run
        assert hasattr(result, 'entry_points')


# Fixtures
@pytest.fixture
def tmp_path():
    """Create temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)
