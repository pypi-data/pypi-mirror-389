# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Essential Commands

### Development Setup
```bash
# Install in development mode (from project root)
pip install -e .

# Install with all optional dependencies
pip install -e ".[full,dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=code_analyzer --cov-report=html

# Run specific test file
pytest tests/test_analyzer.py

# Run specific test function
pytest tests/test_analyzer.py::test_function_name
```

### Code Analysis
```bash
# Self-analysis (quick check)
code-analyzer analyze . --depth shallow

# Full onboarding documentation generation
code-analyzer analyze /path/to/project --onboarding --output ./analysis

# Intelligence reports (trends, debt, performance, security, coverage)
code-analyzer analyze /path/to/project --intelligence --track-trends --output ./analysis

# Complete analysis with all features
code-analyzer analyze /path/to/project \
  --depth deep \
  --onboarding \
  --intelligence \
  --auto-fix \
  --vcs-analysis \
  --track-trends \
  --generate-cicd github \
  --create-tickets \
  --generate-docs \
  --logseq-graph ~/logseq

# Natural language search (v0.8.0)
code-analyzer search . "functions that handle HTTP requests"

# LLM-powered analysis (requires OPENAI_API_KEY or ANTHROPIC_API_KEY)
code-analyzer llm . --question "How does the plugin system work?"
code-analyzer llm . --explain-module analyzer
code-analyzer llm . --generate-docs
```

### Pre-commit Hook
```bash
# The project uses pre-commit hooks for automated analysis
# See .pre-commit-config.yaml - runs shallow analysis on commit
```

## Architecture Overview

### Multi-Language Analysis System

The codebase uses a **plugin-based architecture** with language-specific analyzers:

- **Base Interface**: `base_analyzer.py` defines `LanguageAnalyzer` abstract class
- **Python Analyzer**: Primary analyzer in `analyzer.py` using AST-based parsing
- **JavaScript/TypeScript**: `js_analyzer.py` using regex-based parsing + complexity calculation
- **Language Detection**: `language_detection.py` automatically detects project languages
- **Extensibility**: New languages can be added by implementing `LanguageAnalyzer` interface

### Core Analysis Pipeline

1. **Discovery** (`analyzer.py`): Scan project files, filter by ignore patterns
2. **Language Detection** (`language_detection.py`): Identify file types
3. **Parsing** (language-specific analyzers): Build AST/structure representations
4. **Analysis Phases**:
   - Critical section identification (`important_sections.py`)
   - Complexity analysis (via `radon` for Python, custom for JS)
   - Bug detection (static analysis patterns)
   - VCS history analysis (`vcs_analysis.py`) - hotspots, churn, blame
5. **Documentation Generation**:
   - Onboarding docs (`onboarding.py`, `onboarding_formatter.py`)
   - Intelligence reports (`quality_trends.py`, `tech_debt.py`, `performance.py`, `security.py`, `coverage_analysis.py`)
   - Call graphs (`call_graph.py`)
   - Architecture diagrams (`architecture_diagrams.py`)
6. **Output**:
   - JSON reports (`.code-analyzer/analysis.json`)
   - Markdown docs (ONBOARDING.md, INTELLIGENCE.md, TRENDS.md)
   - Logseq integration (`logseq_integration.py`)
   - Ticket creation (`tickets_integration.py`)

### Plugin System

Two plugin types are supported:

1. **AnalyzerPlugin**: Full control over module analysis
   - Implement `analyze_module()` to inspect `ModuleInfo` objects
   - Add custom `Issue` objects based on analysis
   - Hooks: `pre_analysis_hook()`, `post_analysis_hook()`, `generate_custom_findings()`

2. **CustomRulePlugin**: Simplified rule-based checks
   - Use `add_rule()` to register lambda-based checks
   - Automatically applied to all code objects

Plugins are discovered from `--plugins` directory and loaded dynamically.

### Data Models (`models.py`)

Core data structures:
- `ModuleInfo`: AST-derived module structure (classes, functions, imports)
- `FunctionInfo`, `ClassInfo`: Detailed code element information
- `Issue`: Detected problems with severity, location, recommendations
- `AnalysisResult`: Complete analysis output with metrics
- `CodeLocation`: Source location with file, line, column, context

Issues use **fingerprinting** (`Issue.fingerprint()`) for stable tracking across runs.

### Code Library System (`code_library.py`)

Pattern matching against classified examples:
- Classifications: `excellent`, `good`, `smelly`, `bad`
- YAML-based library format with code snippets
- Matches analyzed code against patterns
- Suggests alternatives for problematic patterns

### Anonymization (`anonymizer.py`)

Privacy-preserving code transformation for LLM analysis:
- Renames identifiers while preserving structure
- Keeps stdlib/framework names if configured
- Maintains call relationships and dependencies

### Trends Database (`trends.py`)

SQLite-based historical tracking:
- Stores analysis results over time
- Tracks metrics by branch
- Generates trend reports with ASCII charts
- Identifies regressions/improvements

## Development Patterns

### Adding a New Language Analyzer

1. Create `{language}_analyzer.py` module
2. Subclass `LanguageAnalyzer` from `base_analyzer.py`
3. Implement required methods:
   - `analyze_file(file_path: Path) -> Optional[ModuleInfo]`
   - `get_supported_extensions() -> List[str]`
   - `get_language_name() -> str`
4. Register in `language_detection.py`
5. Add language-specific issue patterns

### Adding New Issue Types

1. Add enum value to `IssueType` in `models.py`
2. Create detection logic in appropriate analyzer or plugin
3. Return `Issue` objects with:
   - Descriptive `title` and `description`
   - Accurate `CodeLocation`
   - Actionable `recommendation`
   - Optional `code_snippet`

### Creating Onboarding Features

Onboarding components live in multiple modules:
- `onboarding.py`: Core insight generation
- `onboarding_formatter.py`: Enhanced markdown formatting
- `call_graph.py`: Function call relationship analysis
- `interactive_examples.py`: Runnable code examples
- `architecture_diagrams.py`: ASCII diagram generation
- `glossary.py`: Technical term extraction
- `edge_cases.py`: Boundary condition detection

New features should follow the pattern:
1. Add analyzer in dedicated module
2. Generate insights from `ModuleInfo` list
3. Return structured data (dataclasses preferred)
4. Format in `onboarding_formatter.py` as markdown section

### Adding Intelligence Reports

Intelligence modules follow consistent structure:
- Input: `modules` list, `issues` list, optional params
- Output: Markdown section as string
- Location: Separate module in `code_analyzer/`
- Integration: Called from CLI and aggregated into `INTELLIGENCE.md`

Examples: `quality_trends.py`, `tech_debt.py`, `performance.py`

## Performance Considerations

- **Throughput**: 28.5 files/sec, 10k+ lines/sec on typical projects
- **Scaling**: Use `--depth shallow` for large codebases (>50K lines)
- **Memory**: Peaks <20MB for most projects
- **Call Graph**: Most expensive operation (disable for huge codebases)
- **Git Operations**: 5-second timeout per operation, limited to 100 commits per file

## Testing Guidelines

- Test files in `tests/` mirror `code_analyzer/` structure
- Use pytest fixtures for common test data
- Mock file I/O and git operations where possible
- Phase 2 and 3 features have dedicated test files
- Run self-analysis regularly: `code-analyzer analyze . --depth shallow`

Edge cases are documented in TESTING.md - the analyzer handles:
- Minimal projects (1 file)
- Projects without git
- Invalid Python syntax (skips silently)
- Large codebases (tested on pandas: 612K lines)

## Configuration

Projects can include `.code-analyzer.yaml` with:
- `analysis.depth`: shallow/medium/deep
- `analysis.ignore_patterns`: Glob patterns to skip
- `plugins.directory`: Custom plugin location
- `code_library.path`: Team code library YAML
- `documentation.logseq_graph`: Logseq integration path
- `tickets.enabled`: Auto-create tickets for issues
- `privacy.anonymize_for_llm`: Anonymize before external LLM use

See `.code-analyzer.yaml.example` for full options.

## Important Notes

### Never Modify Source Code
All analysis output goes to `.code-analyzer/` directory. The tool is **read-only** on source files.

### Python Version Support
Requires Python 3.8+ (see setup.py). AST parsing uses features from Python 3.8+.

### Dependencies
- Core: `click`, `pyyaml`, `radon`, `rich`, `tqdm`
- Full: `bandit`, `pylint`, `jedi` (optional static analysis tools)
- Dev: `pytest`, `pytest-cov`, `black`, `mypy`

### Git Integration
- VCS features require `.git` directory
- Uses `git --no-pager` to avoid pagination issues
- Gracefully degrades if git unavailable

### LLM Integration (v0.8.0)
Set environment variable:
- `OPENAI_API_KEY` for GPT-4
- `ANTHROPIC_API_KEY` for Claude 3.5

LLM features are optional and only used when explicitly requested via `llm` command.
