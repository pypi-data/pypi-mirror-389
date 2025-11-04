# Engineering Onboarding Enhancement Plan

## Vision
Create the most comprehensive, engineer-friendly onboarding tool that reduces time-to-first-commit from days to hours.

## Research: What Makes Great Engineering Onboarding?

### Best Practices from Top Companies

**Stripe:**
- "Why this exists" for every major component
- Runnable examples with expected output
- Common workflows documented
- Architecture decision records (ADRs)

**GitHub:**
- Visual architecture diagrams
- Interactive tutorials
- "If you only read one thing" prioritization
- Link to related issues/PRs for context

**Netflix:**
- Glossary of domain terms
- "What could go wrong" sections
- Real production examples
- Troubleshooting playbooks

**Basecamp:**
- "Start here" path with time estimates
- Code reading guides with annotations
- Common pitfalls with solutions
- Design philosophy documentation

### Key Principles

1. **Show, Don't Tell** - Real code examples, not abstractions
2. **Why Over What** - Explain design decisions and trade-offs
3. **Progressive Disclosure** - Start simple, add depth gradually
4. **Actionable** - Clear next steps at every stage
5. **Searchable** - Keywords, glossary, cross-references
6. **Living Document** - Auto-update from codebase changes

## Features to Implement

### 🎯 Phase 1: Code Deep Dive (TODAY)

#### 1. Actual Code Extraction
**What**: Extract real code snippets (10-20 lines) with context

```python
# Example output:
## Class: CodeAnalyzer
**Purpose**: Main analyzer that parses Python files and detects issues

**Code Signature**:
```python
class CodeAnalyzer:
    """Main code analyzer that parses and analyzes Python code."""
    
    def __init__(self, project_path: str, 
                 ignore_patterns: Optional[List[str]] = None,
                 plugin_dir: Optional[Path] = None):
        self.project_path = Path(project_path)
        self.ignore_patterns = ignore_patterns or DEFAULT_IGNORE
        self.plugins = self._load_plugins(plugin_dir)
        
    def analyze(self, depth: str = "deep") -> AnalysisResult:
        """Run analysis with specified depth."""
        # Core analysis logic...
```

**Key Methods**:
- `analyze()` - Main entry point, orchestrates analysis
- `_find_python_files()` - Discovers files to analyze
- `_analyze_file()` - Parses individual Python file

**Usage Example**:
```python
analyzer = CodeAnalyzer("/path/to/project")
result = analyzer.analyze(depth="deep")
print(f"Found {result.metrics.total_issues} issues")
```

**Related Files**: 
- `models.py` - Data structures used
- `cli.py` - CLI integration
```

#### 2. Call Graph Visualization
**What**: ASCII diagrams showing function call relationships

```
User Entry Point: cli.analyze()
    │
    ├─> CodeAnalyzer.__init__()
    │   └─> _load_plugins()
    │       └─> PluginManager.discover()
    │
    ├─> CodeAnalyzer.analyze()
    │   ├─> _find_python_files()
    │   ├─> _analyze_file() [foreach file]
    │   │   ├─> ast.parse()
    │   │   ├─> _extract_functions()
    │   │   ├─> _extract_classes()
    │   │   └─> _calculate_complexity()
    │   │
    │   ├─> _detect_issues()
    │   │   └─> IssueDetector.detect()
    │   │
    │   └─> _generate_metrics()
    │
    └─> LogseqDocGenerator.generate_documentation()
        └─> _create_pages()
```

#### 3. "Why This Exists" Documentation
**What**: Extract design decisions from git history and docstrings

```markdown
### Why: Plugin System

**Problem**: Different projects need different analysis rules. Hard-coding all rules makes the tool inflexible.

**Solution**: Plugin architecture allows users to write custom analyzers without modifying core code.

**Design Decision** (from commit abc123):
> "Chose plugin discovery via directory scanning over explicit registration to reduce boilerplate."

**Trade-offs**:
- ✅ Easy to add new analyzers
- ✅ No core code changes needed
- ⚠️  Plugins must follow naming convention
- ⚠️  Harder to validate at startup
```

#### 4. Interactive Examples
**What**: Runnable examples with expected output

```markdown
### Try It: Adding a Custom Issue Detector

**Create this file** (`my_detector.py`):
```python
from code_analyzer.models import Issue, IssueType, IssueSeverity

class MyDetector:
    def detect(self, module_info):
        issues = []
        # Your detection logic
        return issues
```

**Run**:
```bash
code-analyzer analyze . --plugins ./my_detector.py
```

**Expected Output**:
```
📊 Loaded 1 custom plugin
✅ Found custom issues...
```

**What You Should See**:
- Plugin loaded message
- Your custom issues in the report
- All standard issues still work
```

#### 5. Common Workflows
**What**: Step-by-step guides for common tasks

```markdown
## Workflow: Adding a New Issue Type

**Time**: ~15 minutes

**Steps**:

1. **Define the issue type** (`models.py`):
   ```python
   class IssueType(Enum):
       MY_NEW_TYPE = "my_new_type"  # Add here
   ```

2. **Create detector logic** (`analyzer.py`):
   ```python
   def _detect_my_issue(self, module: ModuleInfo) -> List[Issue]:
       # Detection logic
       pass
   ```

3. **Integrate into analysis** (`analyzer.py` line 450):
   ```python
   issues.extend(self._detect_my_issue(module))
   ```

4. **Add test** (`tests/test_analyzer.py`):
   ```python
   def test_detect_my_issue():
       # Test your detector
       pass
   ```

5. **Run tests**:
   ```bash
   pytest tests/test_analyzer.py::test_detect_my_issue
   ```

**Verification**:
- Test passes
- Issue appears in analysis results
- Logseq documentation includes new type
```

### 🎯 Phase 2: Architecture & Concepts (TOMORROW)

#### 6. ASCII Architecture Diagrams
```
┌─────────────────────────────────────────────────────────────┐
│                         CLI (cli.py)                         │
│  Entry point - handles commands, options, output formatting  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   CodeAnalyzer (analyzer.py)   │
         │   Orchestrates analysis flow   │
         └───────────┬───────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌──────────┐
    │ AST    │  │ Radon  │  │ Issue    │
    │ Parser │  │ (CCN)  │  │ Detector │
    └────────┘  └────────┘  └──────────┘
         │           │           │
         └───────────┼───────────┘
                     ▼
              ┌─────────────┐
              │  Models      │
              │  (data)      │
              └──────┬──────┘
                     │
         ┌───────────┼───────────────┐
         │           │               │
         ▼           ▼               ▼
    ┌────────┐  ┌────────┐  ┌────────────┐
    │ Logseq │  │ Trends │  │ Tickets    │
    │ Docs   │  │ SQLite │  │ (Jira)     │
    └────────┘  └────────┘  └────────────┘

Data Flow:
  Python Files → AST → Analysis → Models → Output (Docs/DB/Tickets)
```

#### 7. Troubleshooting Playbook
```markdown
## Problem: "No Python files found"

**Symptoms**:
```
Found 0 Python files
```

**Common Causes**:
1. Wrong directory path
2. Files ignored by patterns
3. No .py files in directory

**Solutions**:
1. Check path: `ls /path/to/project/*.py`
2. View ignore patterns: `code-analyzer analyze . --verbose`
3. Override ignores: `code-analyzer analyze . --ignore-patterns=[]`

**Prevention**: Use `--verbose` flag to see which files are being skipped
```

#### 8. Glossary
```markdown
## Glossary

**AST (Abstract Syntax Tree)**: Python's internal representation of code structure. We parse this to understand code without executing it.

**Cyclomatic Complexity (CCN)**: Measure of code complexity. Higher = more complex. We use `radon` library for this.

**Issue Fingerprint**: SHA256 hash of issue location + title. Used to track same issue across analysis runs.

**Depth (shallow/medium/deep)**: Analysis thoroughness level:
- shallow: Basic metrics only
- medium: + Issue detection
- deep: + Pattern matching, improvement suggestions

**Critical Section**: Code that's complex, frequently changed, or handles important functionality.

**Churn**: How often a file changes (from git history). High churn + high complexity = risky file.
```

#### 9. Edge Cases & Gotchas
```markdown
### Component: Issue Detection

**⚠️  Gotchas**:

1. **Decorator Detection**
   - Problem: Functions with framework decorators (e.g., @pytest.fixture) may be flagged as unused
   - Why: Static analysis can't see runtime registration
   - Solution: We check for common framework decorators (Click, pytest, Flask)
   - Code: `analyzer.py:_has_framework_decorators()`

2. **Dynamic Imports**
   - Problem: `importlib.import_module()` won't be tracked
   - Why: We only analyze static imports from AST
   - Workaround: Add explicit imports for dependency graph

3. **Generated Code**
   - Problem: Build-time generated files may cause false positives
   - Solution: Add `__pycache__`, `build/` to ignore patterns
   - Code: `DEFAULT_IGNORE_PATTERNS` in `analyzer.py`

**🔒 Safety Checks**:
- Never executes analyzed code (AST parsing only)
- All file writes go to `.code-analyzer/` output directory
- Original code is never modified (unless --apply-fixes)
```

## Implementation Priority

**Today (4-6 hours)**:
1. ✅ Code extraction with context (2h)
2. ✅ Call graph generation (1h)
3. ✅ "Why this exists" from git (1h)
4. ✅ Interactive examples (1h)
5. ✅ Common workflows (1h)

**Tomorrow**:
6. ASCII diagrams
7. Troubleshooting playbook
8. Glossary
9. Edge cases documentation
10. Integration testing on 5+ projects

## Success Metrics

- Time to first commit: < 4 hours (from days)
- Onboarding satisfaction: 9+/10
- Questions answered by docs: 90%+
- Code understanding: 80%+ after 1 day

## Technical Approach

### Code Extraction
```python
def extract_code_with_context(cls: ClassInfo, module_path: Path) -> CodeSnapshot:
    """Extract class definition with 10 lines of context."""
    source = module_path.read_text()
    lines = source.splitlines()
    
    start = cls.location.line_start - 1
    end = min(start + 20, len(lines))  # 20 lines max
    
    return CodeSnapshot(
        file_path=str(module_path),
        line_start=start + 1,
        line_end=end,
        code='\n'.join(lines[start:end]),
        context=cls.docstring or "No description",
        entity_type="class",
        entity_name=cls.name
    )
```

### Call Graph
```python
def build_call_graph(modules: List[ModuleInfo]) -> Dict[str, List[str]]:
    """Build function -> [callees] mapping."""
    graph = {}
    for module in modules:
        for func in module.functions:
            graph[f"{module.name}.{func.name}"] = func.calls
    return graph
```

### Git History Mining
```python
def extract_why_from_commits(file_path: str, entity_name: str) -> Optional[str]:
    """Find commit that introduced this class/function."""
    result = subprocess.run(
        ["git", "log", "--all", "-S", entity_name, 
         "--pretty=format:%H|%s|%b", file_path],
        capture_output=True, text=True
    )
    # Parse and return commit message
```

## Documentation Structure

```
ONBOARDING.md
├── 1. Executive Summary (1 min read)
├── 2. Quick Start (5 min)
├── 3. Architecture Deep Dive (30 min)
│   ├── System Overview Diagram
│   ├── Component Breakdown
│   └── Data Flow
├── 4. Code Walkthrough (2 hours)
│   ├── Entry Points
│   ├── Core Classes (with code)
│   ├── Key Functions (with code)
│   └── Call Graphs
├── 5. Common Workflows (1 hour)
│   ├── Adding Features
│   ├── Fixing Bugs
│   └── Writing Tests
├── 6. Debugging & Troubleshooting (reference)
│   ├── Common Problems
│   ├── Error Messages
│   └── Debug Setup
├── 7. Reference
│   ├── Glossary
│   ├── Architecture Decisions
│   └── Edge Cases
└── 8. Next Steps
    ├── Your First Task
    ├── Code Review Checklist
    └── Resources
```

## Next Actions

1. Implement code extraction in `onboarding.py`
2. Add call graph generator
3. Create git history miner
4. Update formatter with new sections
5. Test on code-analyzer itself
6. Generate sample onboarding doc
7. Review and iterate
