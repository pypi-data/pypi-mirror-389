# Code Analyzer - API Reference

This document provides detailed API documentation for using Code Analyzer programmatically.

## Table of Contents

- [Core Classes](#core-classes)
- [Data Models](#data-models)
- [Integration Modules](#integration-modules)
- [CLI Interface](#cli-interface)
- [Usage Examples](#usage-examples)

---

## Core Classes

### CodeAnalyzer

Main class for analyzing Python projects.

```python
from code_analyzer import CodeAnalyzer

analyzer = CodeAnalyzer(project_path, ignore_patterns=None)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_path` | `str` | Required | Path to the project to analyze |
| `ignore_patterns` | `List[str]` | `None` | List of glob patterns to ignore |

**Default Ignore Patterns**:
- `*/venv/*`, `*/env/*`, `*/.venv/*`
- `*/migrations/*`, `*/build/*`, `*/dist/*`
- `*/.git/*`, `*/__pycache__/*`, `*.egg-info/*`

#### Methods

##### `analyze(depth="deep") -> AnalysisResult`

Analyze the project and return results.

**Parameters**:
- `depth` (`str`): Analysis depth - `"shallow"`, `"medium"`, or `"deep"`

**Returns**: `AnalysisResult` object

**Example**:
```python
analyzer = CodeAnalyzer("/path/to/project")
result = analyzer.analyze(depth="deep")

print(f"Files: {result.metrics.total_files}")
print(f"Issues: {len(result.issues)}")
```

**Analysis Depths**:
- **Shallow**: Basic structure analysis, minimal issue detection
- **Medium**: Adds complexity, unused code, and code smell detection
- **Deep**: All checks including security and conceptual issues

---

### CodeAnonymizer

Anonymizes code for external analysis while preserving structure.

```python
from code_analyzer.anonymizer import CodeAnonymizer

anonymizer = CodeAnonymizer(preserve_stdlib=True)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `preserve_stdlib` | `bool` | `True` | Whether to keep standard library names |

#### Methods

##### `anonymize_project(source_path, output_path)`

Anonymize entire project.

**Parameters**:
- `source_path` (`Path`): Source project directory
- `output_path` (`Path`): Output directory for anonymized code

**Example**:
```python
from pathlib import Path

anonymizer = CodeAnonymizer()
anonymizer.anonymize_project(
    Path("/path/to/project"),
    Path("/tmp/anonymized")
)
```

##### `anonymize_file(file_path) -> str`

Anonymize a single file.

**Parameters**:
- `file_path` (`Path`): Path to file

**Returns**: Anonymized code as string

---

### LogseqDocGenerator

Generates documentation in Logseq format.

```python
from code_analyzer.logseq_integration import LogseqDocGenerator

doc_gen = LogseqDocGenerator(logseq_graph_path)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `logseq_graph_path` | `str` | Required | Path to Logseq graph directory |

#### Methods

##### `generate_documentation(result, project_name)`

Generate complete documentation.

**Parameters**:
- `result` (`AnalysisResult`): Analysis results
- `project_name` (`str`): Name of the project

**Example**:
```python
doc_gen = LogseqDocGenerator("~/logseq")
doc_gen.generate_documentation(result, "MyProject")
```

**Generated Pages**:
- `Code Analysis: ProjectName` - Overview
- `ProjectName/Metrics` - Detailed metrics
- `ProjectName/Critical Sections` - High-risk areas
- `ProjectName/Issues` - Categorized issues
- `ProjectName/Modules` - Module documentation
- `ProjectName/Dependencies` - Dependency graph

---

### TicketsManager

Manages ticket creation for discovered issues.

```python
from code_analyzer.tickets_integration import TicketsManager

tickets_mgr = TicketsManager(repo_path)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_path` | `str` | Required | Path to repository root |

#### Methods

##### `create_epic_and_tickets(result, project_name)`

Create epic and tickets for analysis results.

**Parameters**:
- `result` (`AnalysisResult`): Analysis results
- `project_name` (`str`): Name of the project

**Example**:
```python
tickets_mgr = TicketsManager("/path/to/project")
tickets_mgr.create_epic_and_tickets(result, "MyProject")
```

**Created Items**:
- 1 Epic for overall code quality improvements
- Individual tickets for critical/high severity issues
- Sample of medium severity issues (max 10)
- 1 Summary ticket with action plan

---

## Data Models

### AnalysisResult

Complete result of code analysis.

```python
@dataclass
class AnalysisResult:
    project_path: str
    analysis_date: datetime
    modules: List[ModuleInfo]
    issues: List[Issue]
    critical_sections: List[CriticalSection]
    metrics: AnalysisMetrics
    dependency_graph: Dict[str, List[str]]
    entry_points: List[str]
```

#### Methods

##### `get_issues_by_severity(severity) -> List[Issue]`

Filter issues by severity level.

**Example**:
```python
critical_issues = result.get_issues_by_severity(IssueSeverity.CRITICAL)
```

##### `get_issues_by_type(issue_type) -> List[Issue]`

Filter issues by type.

**Example**:
```python
security_issues = result.get_issues_by_type(IssueType.SECURITY)
```

---

### Issue

Represents a detected issue in the code.

```python
@dataclass
class Issue:
    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    location: CodeLocation
    recommendation: Optional[str] = None
    code_snippet: Optional[str] = None
    related_locations: List[CodeLocation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### Methods

##### `to_dict() -> Dict[str, Any]`

Convert issue to dictionary.

**Example**:
```python
issue_dict = issue.to_dict()
print(issue_dict["severity"])  # "high"
```

---

### IssueType (Enum)

Types of issues that can be detected.

```python
class IssueType(Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_SMELL = "code_smell"
    UNUSED_CODE = "unused_code"
    COMPLEXITY = "complexity"
    CONCEPTUAL = "conceptual"
    DOCUMENTATION = "documentation"
    DEPRECATION = "deprecation"
    TYPE_ERROR = "type_error"
```

---

### IssueSeverity (Enum)

Severity levels for issues.

```python
class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
```

---

### CodeLocation

Represents a location in source code.

```python
@dataclass
class CodeLocation:
    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
```

#### Methods

##### `__str__() -> str`

String representation of location.

**Example**:
```python
print(str(location))
# Output: "main.py:10-15 in process_data() [DataProcessor]"
```

---

### AnalysisMetrics

Overall metrics from code analysis.

```python
@dataclass
class AnalysisMetrics:
    total_files: int = 0
    total_lines: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_issues: int = 0
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    average_complexity: float = 0.0
    max_complexity: int = 0
    test_coverage: Optional[float] = None
```

---

### ModuleInfo

Information about a module.

```python
@dataclass
class ModuleInfo:
    name: str
    file_path: str
    docstring: Optional[str]
    imports: List[str] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    constants: Dict[str, Any] = field(default_factory=dict)
    lines_of_code: int = 0
    complexity: int = 0
```

---

### FunctionInfo

Information about a function.

```python
@dataclass
class FunctionInfo:
    name: str
    location: CodeLocation
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    complexity: int
    is_async: bool = False
    is_generator: bool = False
    calls: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)
```

---

### ClassInfo

Information about a class.

```python
@dataclass
class ClassInfo:
    name: str
    location: CodeLocation
    bases: List[str]
    docstring: Optional[str]
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_abstract: bool = False
```

---

### CriticalSection

Represents a critical section of code.

```python
@dataclass
class CriticalSection:
    name: str
    location: CodeLocation
    reason: str
    risk_level: IssueSeverity
    dependencies: List[str] = field(default_factory=list)
    impact_areas: List[str] = field(default_factory=list)
```

---

## CLI Interface

### Commands

#### `analyze`

Analyze a Python project.

```bash
code-analyzer analyze PROJECT_PATH [OPTIONS]
```

**Options**:
- `--depth [shallow|medium|deep]` - Analysis depth (default: deep)
- `--logseq-graph PATH` - Logseq graph path for documentation
- `--create-tickets` - Create tickets for issues
- `--generate-docs` - Generate Logseq documentation
- `--output PATH` - Output directory (default: .code-analyzer)
- `--config PATH` - Configuration file path

#### `anonymize`

Anonymize code for external analysis.

```bash
code-analyzer anonymize PROJECT_PATH --output OUTPUT_PATH
```

**Options**:
- `--output PATH` - Output directory for anonymized code (required)

#### `report`

Generate report from analysis results.

```bash
code-analyzer report ANALYSIS_FILE [OPTIONS]
```

**Options**:
- `--severity [critical|high|medium|low]` - Filter by severity
- `--type TYPE` - Filter by issue type

---

## Usage Examples

### Basic Analysis

```python
from code_analyzer import CodeAnalyzer

# Initialize analyzer
analyzer = CodeAnalyzer("/path/to/project")

# Run analysis
result = analyzer.analyze(depth="deep")

# Access results
print(f"Total files: {result.metrics.total_files}")
print(f"Total issues: {len(result.issues)}")

# Filter issues
critical = result.get_issues_by_severity(IssueSeverity.CRITICAL)
for issue in critical:
    print(f"{issue.title} at {issue.location}")
```

### With Custom Ignore Patterns

```python
analyzer = CodeAnalyzer(
    "/path/to/project",
    ignore_patterns=[
        "*/tests/*",
        "*/migrations/*",
        "*/node_modules/*"
    ]
)
result = analyzer.analyze()
```

### Generate Documentation

```python
from code_analyzer import CodeAnalyzer
from code_analyzer.logseq_integration import LogseqDocGenerator

# Analyze
analyzer = CodeAnalyzer("/path/to/project")
result = analyzer.analyze()

# Generate docs
doc_gen = LogseqDocGenerator("~/logseq")
doc_gen.generate_documentation(result, "MyProject")
```

### Create Tickets

```python
from code_analyzer import CodeAnalyzer
from code_analyzer.tickets_integration import TicketsManager

# Analyze
analyzer = CodeAnalyzer("/path/to/project")
result = analyzer.analyze()

# Create tickets
tickets_mgr = TicketsManager("/path/to/project")
tickets_mgr.create_epic_and_tickets(result, "MyProject")
```

### Anonymize Code

```python
from pathlib import Path
from code_analyzer.anonymizer import CodeAnonymizer

anonymizer = CodeAnonymizer(preserve_stdlib=True)
anonymizer.anonymize_project(
    Path("/path/to/project"),
    Path("/tmp/anonymized")
)
```

### Save Results to JSON

```python
import json
from datetime import datetime

analyzer = CodeAnalyzer("/path/to/project")
result = analyzer.analyze()

# Convert to dict
result_dict = {
    "project_path": result.project_path,
    "analysis_date": result.analysis_date.isoformat(),
    "metrics": {
        "total_files": result.metrics.total_files,
        "total_issues": result.metrics.total_issues,
        # ... more metrics
    },
    "issues": [issue.to_dict() for issue in result.issues]
}

# Save to JSON
with open("analysis.json", "w") as f:
    json.dump(result_dict, f, indent=2)
```

### Filter and Process Issues

```python
analyzer = CodeAnalyzer("/path/to/project")
result = analyzer.analyze()

# Get high severity issues
high_issues = result.get_issues_by_severity(IssueSeverity.HIGH)

# Group by type
from collections import defaultdict
by_type = defaultdict(list)
for issue in high_issues:
    by_type[issue.issue_type].append(issue)

# Print summary
for issue_type, issues in by_type.items():
    print(f"{issue_type.value}: {len(issues)} issues")
    for issue in issues:
        print(f"  - {issue.title}")
```

---

## Error Handling

All main methods may raise exceptions:

```python
try:
    analyzer = CodeAnalyzer("/path/to/project")
    result = analyzer.analyze()
except ValueError as e:
    print(f"Invalid input: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Analysis error: {e}")
```

---

## Configuration File Format

YAML configuration file (`.code-analyzer.yaml`):

```yaml
analysis:
  depth: deep
  include_tests: true
  ignore_patterns:
    - "*/migrations/*"
    - "*/build/*"

documentation:
  logseq_graph: ~/logseq
  create_index: true

tickets:
  enabled: true
  auto_prioritize: true

privacy:
  anonymize_for_llm: true
  preserve_stdlib: true
```

Load configuration:

```python
import yaml

with open(".code-analyzer.yaml", "r") as f:
    config = yaml.safe_load(f)

ignore_patterns = config.get("analysis", {}).get("ignore_patterns")
analyzer = CodeAnalyzer(project_path, ignore_patterns=ignore_patterns)
```

---

## Performance Considerations

- **Large Projects**: Analysis time grows linearly with codebase size
- **Depth**: Shallow analysis is ~3x faster than deep
- **Ignore Patterns**: Use to skip non-essential files
- **Memory**: Holds entire project structure in memory

**Optimization Tips**:
- Use shallow depth for quick overview
- Add comprehensive ignore patterns
- Process in batches for very large projects
- Consider caching results for repeated analysis

---

For more examples, see [EXAMPLES.md](../EXAMPLES.md).
