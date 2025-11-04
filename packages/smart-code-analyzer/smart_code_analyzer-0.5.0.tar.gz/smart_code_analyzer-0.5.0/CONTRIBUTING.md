# Contributing to Code Analyzer

Thank you for your interest in contributing to Code Analyzer! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Adding New Features](#adding-new-features)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the project
- Show empathy towards others

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git for version control
- Basic understanding of AST and static analysis
- Familiarity with pytest for testing

### First Contribution

1. **Find an issue** - Look for issues labeled `good-first-issue` or `help-wanted`
2. **Ask questions** - Comment on the issue if you need clarification
3. **Fork and clone** - Fork the repository and clone it locally
4. **Create a branch** - Use descriptive branch names
5. **Make changes** - Follow our coding standards
6. **Test** - Ensure all tests pass
7. **Submit** - Create a pull request

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/code-analyzer.git
cd code-analyzer
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black pylint mypy
```

### 4. Verify Installation

```bash
# Run self-analysis
code-analyzer analyze . --depth shallow

# Should complete without errors
```

## Project Structure

```
code-analyzer/
├── code_analyzer/          # Main package
│   ├── __init__.py        # Package initialization
│   ├── models.py          # Data models
│   ├── analyzer.py        # Core analysis engine
│   ├── anonymizer.py      # Code anonymization
│   ├── logseq_integration.py   # Logseq documentation
│   ├── tickets_integration.py  # Repo-tickets integration
│   └── cli.py             # CLI interface
├── tests/                  # Test suite (to be created)
│   ├── test_analyzer.py
│   ├── test_anonymizer.py
│   └── ...
├── docs/                   # Documentation
├── examples/               # Example projects
└── setup.py               # Package setup
```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line length**: 100 characters (not 79)
- **Imports**: Group stdlib, third-party, local (separated by blank lines)
- **Docstrings**: Google style for all public functions/classes
- **Type hints**: Required for all public APIs

### Example

```python
"""Module docstring describing purpose."""

import ast
from typing import List, Optional
from pathlib import Path

from .models import AnalysisResult


class CodeAnalyzer:
    """Analyzes Python code for issues and metrics.
    
    Args:
        project_path: Path to the project to analyze
        ignore_patterns: List of glob patterns to ignore
    
    Example:
        >>> analyzer = CodeAnalyzer("/path/to/project")
        >>> result = analyzer.analyze(depth="deep")
        >>> print(f"Found {len(result.issues)} issues")
    """
    
    def __init__(self, project_path: str, ignore_patterns: Optional[List[str]] = None):
        self.project_path = Path(project_path).resolve()
        self.ignore_patterns = ignore_patterns or []
    
    def analyze(self, depth: str = "deep") -> AnalysisResult:
        """Analyze the project and return results.
        
        Args:
            depth: Analysis depth - 'shallow', 'medium', or 'deep'
        
        Returns:
            AnalysisResult containing all findings
        
        Raises:
            ValueError: If depth is invalid
        """
        if depth not in ["shallow", "medium", "deep"]:
            raise ValueError(f"Invalid depth: {depth}")
        
        # Implementation...
```

### Documentation Requirements

#### Functions and Methods

All public functions must have:
- Brief description
- Args section with type and description
- Returns section with type and description
- Raises section if applicable
- Example usage when helpful

#### Classes

All classes must have:
- Brief description of purpose
- Args section for `__init__` parameters
- Example usage
- Attributes section if complex state

#### Modules

All modules must have:
- Module-level docstring explaining purpose
- List of main classes/functions if not obvious

## Testing Guidelines

### Writing Tests

We use **pytest** for all tests. Tests should be:

- **Isolated**: Each test should be independent
- **Fast**: Aim for tests that run in milliseconds
- **Clear**: Test names should describe what they test
- **Complete**: Test happy paths and edge cases

### Test Structure

```python
import pytest
from code_analyzer.analyzer import CodeAnalyzer

class TestCodeAnalyzer:
    """Tests for CodeAnalyzer class."""
    
    @pytest.fixture
    def sample_project(self, tmp_path):
        """Create a sample project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create sample file
        (project_dir / "main.py").write_text("""
def hello():
    print("Hello")
""")
        return project_dir
    
    def test_analyze_simple_project(self, sample_project):
        """Test analysis of a simple project."""
        analyzer = CodeAnalyzer(str(sample_project))
        result = analyzer.analyze(depth="shallow")
        
        assert result.metrics.total_files == 1
        assert result.metrics.total_functions >= 1
    
    def test_analyze_invalid_depth(self):
        """Test that invalid depth raises ValueError."""
        analyzer = CodeAnalyzer("/tmp/test")
        
        with pytest.raises(ValueError, match="Invalid depth"):
            analyzer.analyze(depth="invalid")
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=code_analyzer --cov-report=html

# Run specific test file
pytest tests/test_analyzer.py

# Run specific test
pytest tests/test_analyzer.py::TestCodeAnalyzer::test_analyze_simple_project
```

### Test Coverage

- Aim for **>80% code coverage**
- All new features must include tests
- Bug fixes should include regression tests

## Submitting Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-type-checking` - New features
- `fix/handle-empty-files` - Bug fixes
- `docs/update-examples` - Documentation
- `refactor/simplify-parser` - Refactoring
- `test/add-anonymizer-tests` - Tests only

### Commit Messages

Follow conventional commits:

```
type(scope): brief description

Longer explanation if needed.

Fixes #123
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

**Examples**:
```
feat(analyzer): add support for async functions

- Parse AsyncFunctionDef nodes
- Track async functions separately
- Add is_async flag to FunctionInfo

Fixes #42
```

```
fix(cli): handle missing config file gracefully

Previously crashed with FileNotFoundError when config
file didn't exist. Now falls back to defaults.

Fixes #56
```

### Pull Request Process

1. **Update documentation** - If you change APIs
2. **Add tests** - For new functionality
3. **Update CHANGELOG** - Add entry for your change
4. **Run linters** - Ensure code passes checks
5. **Describe changes** - Write clear PR description
6. **Link issues** - Reference related issues

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
```

## Adding New Features

### 1. Issue Detection Rules

To add a new issue detection rule:

**1. Update `models.py`**:
```python
class IssueType(Enum):
    # ... existing types ...
    YOUR_NEW_TYPE = "your_new_type"
```

**2. Add detection in `analyzer.py`**:
```python
def _detect_your_issue(self):
    """Detect your specific issue type."""
    for module in self.modules:
        for func in module.functions:
            # Your detection logic
            if some_condition:
                self.issues.append(Issue(
                    issue_type=IssueType.YOUR_NEW_TYPE,
                    severity=IssueSeverity.MEDIUM,
                    title="Issue title",
                    description="Issue description",
                    location=func.location,
                    recommendation="How to fix"
                ))
```

**3. Call in `analyze()` method**:
```python
def analyze(self, depth: str = "deep") -> AnalysisResult:
    # ... existing code ...
    
    if depth in ["medium", "deep"]:
        self._detect_your_issue()  # Add here
```

**4. Add tests**:
```python
def test_detect_your_issue(self, sample_code):
    """Test detection of your issue type."""
    analyzer = CodeAnalyzer(sample_code)
    result = analyzer.analyze()
    
    your_issues = result.get_issues_by_type(IssueType.YOUR_NEW_TYPE)
    assert len(your_issues) > 0
```

**5. Update documentation**:
- Add to EXAMPLES.md with sample code
- Update README.md feature list

### 2. CLI Commands

To add a new CLI command:

**1. Add command in `cli.py`**:
```python
@main.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--your-option", help="Description")
def your_command(project_path, your_option):
    """Brief description of command."""
    # Implementation
```

**2. Add tests**:
```python
def test_your_command(cli_runner):
    """Test your command."""
    result = cli_runner.invoke(your_command, ["/tmp/test"])
    assert result.exit_code == 0
```

**3. Update documentation**:
- Add to README.md
- Add to QUICKSTART.md
- Add example to EXAMPLES.md

### 3. Output Formats

To add a new output format:

**1. Create formatter** in new file:
```python
class YourFormatter:
    """Formats analysis results in your format."""
    
    def format(self, result: AnalysisResult) -> str:
        """Format the result."""
        # Implementation
```

**2. Add CLI option**:
```python
@main.command()
@click.option("--format", type=click.Choice(["json", "html", "your-format"]))
def report(format):
    # Handle your format
```

## Code Review Process

### What We Look For

- **Correctness**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Documentation**: Is it well documented?
- **Style**: Does it follow guidelines?
- **Performance**: Is it efficient?
- **Maintainability**: Is it easy to understand?

### Review Checklist

- [ ] Code is clear and understandable
- [ ] Edge cases are handled
- [ ] Error messages are helpful
- [ ] No unnecessary complexity
- [ ] No performance issues
- [ ] Tests are comprehensive
- [ ] Documentation is complete
- [ ] No breaking changes (or properly documented)

## Development Tools

### Linting

```bash
# Run pylint
pylint code_analyzer/

# Run black (formatting)
black code_analyzer/

# Run mypy (type checking)
mypy code_analyzer/
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Run checks before committing

echo "Running black..."
black code_analyzer/

echo "Running pylint..."
pylint code_analyzer/ || exit 1

echo "Running tests..."
pytest tests/ || exit 1

echo "All checks passed!"
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Getting Help

### Where to Ask

- **GitHub Issues** - Bug reports, feature requests
- **Discussions** - General questions, ideas
- **Pull Requests** - Code-specific questions

### Issue Templates

Use provided templates for:
- Bug reports
- Feature requests
- Documentation improvements

## Recognition

Contributors are recognized in:
- CHANGELOG.md for their contributions
- README.md contributors section
- Release notes

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Code Analyzer! 🎉
