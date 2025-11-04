# Code Analyzer Project Documentation

## Overview
- **Project**: Code Analyzer
- **Purpose**: Deep source code analysis and documentation tool for Python projects
- **Status**: #development #active
- **Repository**: /Volumes/Projects/code-analyzer

## Key Features
- 🔍 **Deep Code Analysis** - AST-based parsing with complexity metrics
- 🎯 **Critical Section Identification** - Automatic detection of high-risk areas
- 🐛 **Issue Detection** - Static analysis for bugs, security, performance
- 🔒 **Code Anonymization** - Privacy-preserving external analysis
- 📚 **Logseq Integration** - Automatic documentation generation
- 🎫 **Ticket Management** - Auto-creates prioritized tickets
- 📊 **Comprehensive Reports** - Detailed metrics and insights

## Architecture

### Core Components
- **analyzer.py** - Main analysis engine using AST
  - Parses Python code
  - Identifies functions, classes, modules
  - Calculates complexity metrics
  - Builds call graphs
  
- **models.py** - Data models
  - AnalysisResult
  - Issue, IssueType, IssueSeverity
  - FunctionInfo, ClassInfo, ModuleInfo
  - CriticalSection, AnalysisMetrics

- **anonymizer.py** - Code anonymization
  - Hash-based name mapping
  - Preserves structure and stdlib
  - Secure mapping storage

- **logseq_integration.py** - Documentation generator
  - Creates hierarchical pages
  - Groups by severity and type
  - Links to critical sections

- **tickets_integration.py** - Issue tracking
  - Creates epics and tickets
  - Auto-prioritization
  - Links to code locations

- **cli.py** - Command-line interface
  - analyze, anonymize, report commands
  - Configuration file support
  - Rich terminal output

## Analysis Pipeline

```
1. File Discovery
   └─> Find all Python files
   └─> Filter by ignore patterns

2. Code Parsing
   └─> AST parsing per file
   └─> Extract structure (classes, functions)
   └─> Calculate complexity

3. Issue Detection
   └─> Complexity issues
   └─> Unused code
   └─> Code smells
   └─> Security issues
   └─> Conceptual problems

4. Critical Section Identification
   └─> High complexity functions
   └─> Large classes
   └─> Entry points

5. Output Generation
   └─> JSON report
   └─> Logseq documentation
   └─> Repo-tickets epics/tickets
```

## Issue Types

### Bug Detection
- Potential logic errors
- Type mismatches
- Undefined variables

### Security Analysis
- Dangerous imports (pickle, marshal)
- Input validation issues
- Unsafe deserialization

### Performance Issues
- High complexity algorithms
- Inefficient loops
- Memory leaks

### Code Smells
- Long parameter lists
- God classes
- Duplicate code
- Magic numbers

### Complexity Issues
- High cyclomatic complexity (>15)
- Deep nesting
- Long functions

### Unused Code
- Uncalled functions
- Unused imports
- Dead code paths

### Conceptual Issues
- Violation of SOLID principles
- Tight coupling
- Poor abstraction

### Documentation Issues
- Missing docstrings
- Incomplete documentation
- Outdated comments

## Configuration

### Analysis Options
```yaml
analysis:
  depth: deep  # shallow, medium, deep
  include_tests: true
  ignore_patterns:
    - "*/migrations/*"
    - "*/build/*"
```

### Documentation Options
```yaml
documentation:
  logseq_graph: ~/logseq
  create_index: true
  group_by_severity: true
```

### Tickets Options
```yaml
tickets:
  enabled: true
  auto_prioritize: true
  create_epics: true
```

### Privacy Options
```yaml
privacy:
  anonymize_for_llm: true
  keep_structure: true
  preserve_stdlib: true
```

## Usage Examples

### Basic Analysis
```bash
code-analyzer analyze /path/to/project
```

### Full Analysis with Documentation
```bash
code-analyzer analyze /path/to/project \
  --depth deep \
  --generate-docs \
  --logseq-graph ~/logseq \
  --create-tickets
```

### Code Anonymization
```bash
code-analyzer anonymize /path/to/project \
  --output /tmp/anonymized
```

### View Results
```bash
code-analyzer report .code-analyzer/analysis.json \
  --severity high
```

## Integration Points

### Logseq
- Creates pages: `Code Analysis: ProjectName`
- Sub-pages for metrics, issues, modules
- Cross-references between pages
- Tags for categorization

### Repo-Tickets
- Epic: "Code Quality Improvements"
- Individual tickets per issue
- Priority based on severity
- Labels for filtering

## Development Roadmap

### Phase 1: Core Functionality ✅
- [x] AST-based code analysis
- [x] Complexity calculation
- [x] Issue detection
- [x] Critical section identification

### Phase 2: Integration ✅
- [x] Logseq documentation generator
- [x] Repo-tickets integration
- [x] CLI interface
- [x] Configuration system

### Phase 3: Advanced Features 
- [ ] Type checking integration (mypy)
- [ ] Test coverage analysis
- [ ] Performance profiling
- [ ] Custom rule system
- [ ] LLM-powered analysis
- [ ] Continuous monitoring

### Phase 4: Enhancement
- [ ] Web UI dashboard
- [ ] Git history analysis
- [ ] Team collaboration features
- [ ] CI/CD integration
- [ ] Plugin system

## Testing Strategy

### Unit Tests
- Analyzer components
- Issue detection
- Anonymization
- Integration modules

### Integration Tests
- End-to-end analysis
- Logseq output validation
- Ticket creation verification

### Test Cases
- Simple Python project
- Complex multi-module project
- Projects with various issue types
- Edge cases (empty files, syntax errors)

## Best Practices

### For Users
1. Start with shallow analysis for quick overview
2. Use configuration files for consistent settings
3. Address critical issues first
4. Re-analyze after fixes to verify improvements
5. Use Logseq for tracking progress

### For Developers
1. Keep models separate from logic
2. Make analyzers extensible
3. Preserve privacy by default
4. Generate actionable recommendations
5. Document all issue types clearly

## Future Enhancements

### Machine Learning
- Learn from fixed issues
- Suggest refactorings
- Predict bug-prone areas

### Advanced Analysis
- Data flow analysis
- Taint tracking
- Symbolic execution
- Abstract interpretation

### Integration
- GitHub/GitLab integration
- Slack/Discord notifications
- VS Code extension
- Pre-commit hooks

## Contributing
See CONTRIBUTING.md for guidelines on:
- Code style
- Testing requirements
- Documentation standards
- Pull request process

## Resources
- README.md - Project overview
- QUICKSTART.md - Getting started guide
- .code-analyzer.yaml.example - Configuration template
- /docs - Additional documentation
