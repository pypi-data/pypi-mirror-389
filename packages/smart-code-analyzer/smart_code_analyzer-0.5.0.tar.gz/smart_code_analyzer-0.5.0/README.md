# Code Analyzer

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub issues](https://img.shields.io/github/issues/thinmanj/code-analyzer)](https://github.com/thinmanj/code-analyzer/issues)
[![GitHub stars](https://img.shields.io/github/stars/thinmanj/code-analyzer)](https://github.com/thinmanj/code-analyzer/stargazers)

**Deep source code analysis and documentation tool for multiple programming languages**

Code Analyzer is a comprehensive tool that reads source code, understands its structure, identifies critical sections, detects potential issues, and generates detailed documentation. Currently supports **Python** and **JavaScript/TypeScript** with a language-agnostic architecture ready for Go, Java, and more.

## Supported Languages

| Language | Support | Features |
|----------|---------|----------|
| **Python** | ✅ Full | All 16 features, AST-based parsing |
| **JavaScript/TypeScript** | ✅ Full | All 16 features, regex-based parsing + complexity calculation |
| **Go, Java, Ruby, etc.** | 🔄 Planned | Extensible architecture ready |

**Multi-Language Intelligence**: Onboarding, tech debt, and performance analysis automatically adapt to detect language-specific patterns (React hooks, async/await, etc.).

## Features

### Core Analysis
- 🔍 **Deep Code Analysis**: AST-based parsing to understand code structure and dependencies
- 🎯 **Critical Section Identification**: Automatically identifies important code locations and critical paths
- 🐛 **Bug Detection**: Static analysis to find potential bugs, security issues, and code smells
- 📊 **VCS History Analysis**: Analyzes git history for hotspots, churn, and maintenance patterns
- 📈 **Trends Tracking**: SQLite database for tracking code quality over time
- 🔧 **Auto-Fix Generation**: Automatic fixes for common issues with confidence levels
- 🎫 **CI/CD Integration**: Generate GitHub Actions and GitLab CI workflows

### 🎉 World-Class Engineering Onboarding (v0.5.0-v0.6.0)

**Transform onboarding from days to hours** with comprehensive, actionable documentation:

#### Phase 1: Core Onboarding (v0.5.0)

1. **📝 Real Code Snippets** - Extract 10-20 line examples from key components
   - Multi-editor deep links (VS Code, IntelliJ, Neovim, Vim, Emacs, Sublime, Atom)
   - Actual implementation with full context and docstrings
   - Jump directly to code in your favorite editor

2. **🔄 Call Graph Visualization** - Understand how functions connect
   - ASCII call trees showing execution flow
   - Hot paths analysis (most-called functions)
   - System flow diagrams with module structure
   - Data transformation pipeline visualization

3. **🎯 "Why This Exists" Documentation** - Learn from git history
   - Mines commit messages for component rationale
   - Shows design decisions and evolution timeline
   - Identifies main contributors per component
   - Extracts "why" patterns from commit history

4. **🎨 Interactive Runnable Examples** - Copy-paste and run immediately
   - Smart parameter inference for realistic examples
   - Expected output shown for each example
   - Multiple use cases (classes, functions, workflows)
   - Copy-paste ready with zero configuration

5. **🔧 Common Developer Workflows** - Step-by-step guides
   - 6 complete workflows with time estimates (20-90 min each)
   - Add analyzers, create plugins, debug issues, contribute
   - Code examples with file locations
   - Pro tips and prerequisites for each workflow

#### Phase 2: Advanced Understanding (v0.6.0)

6. **🏛️ Architecture Diagrams** - 5 visualization types
   - Layered architecture (presentation/application/domain/infrastructure)
   - Component interaction maps
   - Package structure with dependencies
   - Dependency graph with coupling analysis
   - Complexity heatmap by module

7. **🔧 Troubleshooting Playbook** - Issue-driven solutions
   - Categorized by pattern (complexity/unused/imports/errors/security)
   - Targeted solutions with code examples
   - Common causes and symptoms
   - General troubleshooting guidance

8. **📖 Glossary & Key Concepts** - Auto-generated terminology
   - Technical terms from imports and patterns
   - Domain concepts from class/function names
   - Definitions mined from docstrings
   - Alphabetically organized

9. **⚠️ Edge Cases Documentation** - Boundary conditions
   - Detected edge case handling
   - Validation recommendations
   - General guidelines for safety

**Result**: Engineers onboard in **<4 hours instead of days**! ✨
**Output**: 2,151 lines of comprehensive onboarding (v0.6.0)

### 🧠 Intelligence & Metrics (v0.7.0)

**NEW**: Comprehensive intelligence reports for technical leadership and team health:

10. **📈 Quality Trends** - Historical metrics analysis
    - Insights by category (improvement/warning/regression/stable)
    - Velocity analysis (accelerating/degrading)
    - ASCII trend charts
    - Issue density tracking

11. **💳 Technical Debt** - Quantified debt tracking
    - Scoring by category (complexity/docs/design/duplication)
    - Effort estimates in hours/days/weeks
    - Quick wins identification (<2 hours)
    - Remediation strategy roadmap

12. **⚡ Performance Hotspots** - Static pattern detection
    - Nested loops and high complexity
    - Inefficient search patterns
    - Deep recursion warnings
    - Optimization suggestions

13. **🔒 Security & Dependencies** - Vulnerability scanning
    - Known CVE checking
    - Outdated package detection
    - Security best practices
    - Upgrade recommendations

14. **🧪 Test Coverage** - Multi-format analysis
    - Parse coverage.xml, .coverage, htmlcov
    - Critical gap identification
    - Module-by-module breakdown
    - Coverage recommendations

**Usage**: `--intelligence --track-trends` generates INTELLIGENCE.md (238-287 lines)

### 🤖 AI-Powered Features (v0.8.0)

**NEW**: Natural language search and LLM-powered code understanding:

15. **🔍 Natural Language Search** - Query codebase in plain English
    - Search functions, classes, and modules using natural language
    - Pattern matching for common intents (HTTP, database, validation)
    - Keyword-based semantic scoring
    - CLI: `code-analyzer search . "functions that handle requests"`

16. **🤖 LLM Integration** - AI-powered code analysis
    - Explain complex code snippets in plain English
    - Summarize modules and their purpose
    - Answer questions about your codebase
    - Generate comprehensive documentation
    - Support for OpenAI (GPT-4) and Anthropic (Claude 3.5)
    - CLI: `code-analyzer llm . --question "What does the auth module do?"`

**Usage**:
```bash
# Search codebase
code-analyzer search /path/to/project "database connection classes"

# Ask questions (requires API key)
code-analyzer llm /path/to/project --question "How does authentication work?"

# Explain a module
code-analyzer llm /path/to/project --explain-module auth_handler

# Generate AI documentation
code-analyzer llm /path/to/project --generate-docs
```

**Setup**: Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable

### Integration & Extensibility
- 🔌 **Plugin System**: Extensible architecture for custom analyzers and rules
- 📚 **Code Library**: Learn from classified code examples (excellent/good/smelly/bad patterns)
- 🔒 **Privacy-First**: Code anonymization for external LLM analysis while keeping sensitive code local
- 📝 **Logseq Integration**: Automatic documentation generation in your Logseq graph
- 🎫 **Ticket Management**: Auto-creates epics and prioritized tickets for discovered issues
- 🚫 **Non-Invasive**: Never modifies source code, stores all analysis in separate directory
- ⚡ **Fast & Efficient**: 28.5 files/sec, 10k+ lines/sec, < 10 MB memory

## Installation

```bash
cd /Volumes/Projects/code-analyzer
pip install -e .
```

## Quick Start

```bash
# Generate world-class onboarding documentation
code-analyzer analyze /path/to/project --onboarding --output ./analysis

# Generate intelligence reports (trends, debt, performance, security, coverage)
code-analyzer analyze /path/to/project --intelligence --track-trends --output ./analysis

# Full analysis with all features
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

# Use custom plugins and code library
code-analyzer analyze /path/to/project \
  --plugins ./my-plugins \
  --code-library ./team-code-library.yaml

# Use built-in default code library
code-analyzer analyze /path/to/project --use-default-library

# Anonymize code for external analysis
code-analyzer anonymize /path/to/project --output /tmp/anonymized
```

## Example Onboarding Output

Running onboarding on real projects generates comprehensive documentation:

### Onboarding Output (v0.6.0)

| Project | Files | Lines | Onboarding Lines | Features |
|---------|-------|-------|-----------------|----------|
| code-analyzer | 41 | 12,845 | 2,151 | ✅ All 9 |
| python-optimizer | 71 | 23,894 | ~2,000 | ✅ All 9 |
| agentscript | 58 | ~15K | ~1,900 | ✅ All 9 |
| logseq-python | 75 | ~25K | ~2,100 | ✅ All 9 |

**Each includes**: Real code snippets, call graphs, git history, interactive examples, workflows, architecture diagrams, troubleshooting playbook, glossary, and edge cases.

### Intelligence Output (v0.7.0)

| Project | Files | Intelligence Lines | Reports |
|---------|-------|--------------------|----------|
| code-analyzer | 41 | 281 | ✅ All 5 |
| agentscript | 58 | 238 | ✅ All 5 |
| python-optimizer | 71 | 271 | ✅ All 5 |
| logseq-python | 75 | 287 | ✅ All 5 |

**Each includes**: Quality trends, technical debt, performance hotspots, security scan, and test coverage analysis.

## Configuration

Create `.code-analyzer.yaml` in your project root:

```yaml
analysis:
  depth: deep  # shallow, medium, deep
  include_tests: true
  ignore_patterns:
    - "*/migrations/*"
    - "*/build/*"

plugins:
  directory: "./code-analyzer-plugins"

code_library:
  path: "./team-code-library.yaml"
  # OR use built-in examples:
  # use_default: true

documentation:
  logseq_graph: ~/logseq
  create_index: true
  
tickets:
  enabled: true
  auto_prioritize: true
  create_epics: true

privacy:
  anonymize_for_llm: true
  keep_structure: true
```

## How It Works

1. **Parse**: Analyzes Python code using AST and static analysis
2. **Identify**: Finds critical sections, entry points, and dependencies
3. **Detect**: Discovers bugs, security issues, and code smells
4. **Document**: Generates comprehensive Logseq documentation
5. **Track**: Creates prioritized tickets for issues in repo-tickets
6. **Report**: Produces detailed analysis reports

All analysis data is stored in `.code-analyzer/` directory, never modifying source code.

## Extensibility

### Plugin System

Create custom analyzers to enforce team-specific rules:

```python
from code_analyzer.plugins import CustomRulePlugin
from code_analyzer.models import IssueSeverity

class MyTeamRules(CustomRulePlugin):
    @property
    def name(self) -> str:
        return "my-team-rules"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.add_rule(
            name="no-print-statements",
            check=lambda obj: 'print(' in str(obj.source_code),
            severity=IssueSeverity.LOW,
            message="Use logging instead of print",
            recommendation="Import logging and use logger.info()"
        )
```

See [docs/PLUGINS.md](docs/PLUGINS.md) for complete guide.

### Code Library

Build a library of code patterns classified by quality:

```yaml
examples:
  - id: "eval-bad-001"
    classification: bad
    pattern_type: security
    language: python
    reason: "Arbitrary code execution vulnerability"
    code: |
      result = eval(user_input)
    alternative: "Use ast.literal_eval() for safe evaluation"
```

The analyzer will match your code against the library and flag bad/smelly patterns.

## Performance

Benchmarked on 4 real-world Python projects (176 files, 62,814 lines):

- **Throughput**: 28.5 files/sec, 10,182 lines/sec
- **Memory**: 7.6 MB average, < 20 MB peak
- **Speed**: 0.5-3.5s for typical projects
- **Scaling**: Linear growth, handles 70+ files easily

Suitable for:
- ✅ Interactive CLI usage
- ✅ Pre-commit hooks (< 5s)
- ✅ CI/CD pipelines
- ✅ IDE integration

See [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for detailed benchmarks.

## Integration

- **logseq-python**: Documentation generation in Logseq format
- **repo-tickets**: Epic and ticket management for discovered issues
- **Plugins**: Custom analyzers and rules
- **Code Library**: Pattern matching against classified examples
- **Local Analysis**: Most analysis runs locally for privacy
- **LLM Support**: Optional anonymized code analysis for complex patterns

## License

MIT License
