# Plugin System & Code Library

This guide explains how to extend code-analyzer with custom plugins and code quality patterns.

## Table of Contents
- [Plugin System](#plugin-system)
- [Code Library](#code-library)
- [Examples](#examples)

---

## Plugin System

The plugin system allows you to add custom analysis logic and findings generation.

### Creating a Plugin

1. Create a Python file in your plugins directory
2. Subclass `AnalyzerPlugin` or `CustomRulePlugin`
3. Implement required methods

#### Basic Plugin Example

```python path=null start=null
from code_analyzer.plugins import AnalyzerPlugin
from code_analyzer.models import ModuleInfo, Issue, IssueType, IssueSeverity, CodeLocation

class MyCustomPlugin(AnalyzerPlugin):
    @property
    def name(self) -> str:
        return "my-custom-plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def analyze_module(self, module: ModuleInfo) -> List[Issue]:
        """Analyze a module and return issues."""
        issues = []
        
        # Your custom analysis logic here
        for func in module.functions:
            if len(func.name) < 3:
                issues.append(Issue(
                    issue_type=IssueType.CODE_SMELL,
                    severity=IssueSeverity.LOW,
                    title="Function name too short",
                    description=f"Function '{func.name}' has a very short name",
                    location=func.location,
                    recommendation="Use descriptive function names with at least 3 characters"
                ))
        
        return issues
```

#### Custom Rule Plugin Example

For simpler rule-based plugins, use `CustomRulePlugin`:

```python path=null start=null
from code_analyzer.plugins import CustomRulePlugin
from code_analyzer.models import IssueSeverity

class MyCustomRules(CustomRulePlugin):
    @property
    def name(self) -> str:
        return "my-rules"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        
        # Add rules in constructor
        self.add_rule(
            name="no-todo-comments",
            check=lambda obj: hasattr(obj, 'source_code') and 'TODO' in obj.source_code,
            severity=IssueSeverity.LOW,
            message="TODO comment found",
            recommendation="Complete or document the TODO item"
        )
        
        self.add_rule(
            name="require-docstrings",
            check=lambda obj: hasattr(obj, 'docstring') and not obj.docstring,
            severity=IssueSeverity.MEDIUM,
            message="Missing docstring",
            recommendation="Add a docstring to document this code"
        )
```

### Plugin Hooks

Plugins can implement hooks that run at different stages:

```python path=null start=null
class MyPlugin(AnalyzerPlugin):
    def pre_analysis_hook(self, modules: List[ModuleInfo]) -> None:
        """Called before analysis begins."""
        print(f"Starting analysis of {len(modules)} modules")
    
    def post_analysis_hook(self, modules: List[ModuleInfo], all_issues: List[Issue]) -> None:
        """Called after analysis completes."""
        print(f"Analysis found {len(all_issues)} total issues")
    
    def generate_custom_findings(self, modules: List[ModuleInfo]) -> Dict[str, Any]:
        """Generate custom metrics/findings."""
        return {
            "total_todo_comments": sum(
                1 for m in modules 
                for f in m.functions 
                if f.source_code and 'TODO' in f.source_code
            )
        }
```

### Using Plugins

#### Command Line

```bash
code-analyzer analyze /path/to/project --plugins /path/to/plugins/
```

#### Configuration File

```yaml
plugins:
  directory: "./my-plugins"
```

### Built-in Plugins

code-analyzer includes these example plugins:

- **NamingConventionPlugin**: Enforces Python naming conventions (PascalCase for classes, etc.)
- **LoggingBestPracticesPlugin**: Checks for proper logging usage (e.g., no print statements)

---

## Code Library

The code library system allows you to classify code examples and match them against analyzed code.

### Code Quality Levels

- **excellent**: Best practices, optimal implementations
- **good**: Acceptable code, minor improvements possible
- **smelly**: Code that works but has issues (code smells)
- **bad**: Problematic code that should be refactored

### Library File Format

Code libraries are stored in YAML files:

```yaml
examples:
  - id: "singleton-excellent-001"
    classification: excellent
    pattern_type: singleton
    language: python
    description: "Thread-safe singleton with double-checked locking"
    code: |
      class Singleton:
          _instance = None
          _lock = threading.Lock()
          
          def __new__(cls):
              if cls._instance is None:
                  with cls._lock:
                      if cls._instance is None:
                          cls._instance = super().__new__(cls)
              return cls._instance
    tags:
      - design-pattern
      - thread-safe

  - id: "eval-bad-001"
    classification: bad
    pattern_type: security
    language: python
    description: "Using eval() on user input"
    reason: "Arbitrary code execution vulnerability"
    code: |
      result = eval(user_input)
    alternative: "Use ast.literal_eval() for safe evaluation or validate/parse input explicitly"
    tags:
      - security
      - injection
```

### Pattern Types

Available pattern types:
- `singleton`, `factory`, `observer`, `strategy` - Design patterns
- `error_handling` - Exception handling patterns
- `validation` - Input validation patterns
- `security` - Security-related patterns
- `performance` - Performance patterns
- `testing` - Test code patterns
- `documentation` - Documentation patterns
- `naming` - Naming conventions
- `structure` - Code structure patterns
- `general` - General patterns

### Creating a Code Library

#### Method 1: YAML File

Create a YAML file with your examples:

```yaml
examples:
  - id: "my-example-001"
    classification: bad
    pattern_type: error_handling
    language: python
    description: "Bare except clause"
    reason: "Catches all exceptions including system exits"
    code: |
      try:
          risky_operation()
      except:
          pass
    alternative: "Catch specific exceptions: except ValueError: ..."
    tags: [error-handling, anti-pattern]
```

#### Method 2: Programmatically

```python path=null start=null
from code_analyzer.code_library import CodeLibrary, CodeExample, CodeQuality, PatternType

library = CodeLibrary()

library.add_example(CodeExample(
    id="my-example-001",
    classification=CodeQuality.BAD,
    pattern_type=PatternType.SECURITY,
    language="python",
    code="password = 'hardcoded123'",
    description="Hard-coded password",
    reason="Security vulnerability - credentials in source code",
    alternative="Load passwords from environment variables or secure vault",
    tags=["security", "credentials"]
))

# Save to file
library.save_to_file(Path("my_library.yaml"))
```

### Using Code Library

#### Command Line

```bash
# Use custom library
code-analyzer analyze /path/to/project --code-library /path/to/library.yaml

# Use default built-in library
code-analyzer analyze /path/to/project --use-default-library
```

#### Configuration File

```yaml
code_library:
  path: "./my-code-library.yaml"
  # OR
  use_default: true
```

### Pattern Matching

The pattern matcher uses multiple techniques to find similar code:
- **Text similarity**: Direct string comparison
- **AST structure similarity**: Compares abstract syntax tree structure
- **Token similarity**: Compares frequency of AST node types

Default similarity threshold: 70% (configurable)

### Default Library

code-analyzer includes a default library with examples for:
- Thread-safe singleton pattern (excellent)
- Proper error handling (excellent)
- Using eval() on user input (bad)
- Bare except clauses (bad)
- God classes (smelly)

---

## Examples

### Example 1: Custom Security Plugin

```python path=null start=null
# File: my-plugins/security_checks.py

from code_analyzer.plugins import CustomRulePlugin
from code_analyzer.models import IssueSeverity

class SecurityChecksPlugin(CustomRulePlugin):
    @property
    def name(self) -> str:
        return "security-checks"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        
        # Check for hardcoded secrets
        self.add_rule(
            name="no-hardcoded-passwords",
            check=lambda obj: (
                hasattr(obj, 'source_code') and 
                obj.source_code and
                any(word in obj.source_code.lower() 
                    for word in ['password =', 'api_key =', 'secret ='])
            ),
            severity=IssueSeverity.CRITICAL,
            message="Possible hardcoded credential detected",
            recommendation="Use environment variables or secure credential storage"
        )
        
        # Check for SQL concatenation
        self.add_rule(
            name="no-sql-concatenation",
            check=lambda obj: (
                hasattr(obj, 'source_code') and 
                obj.source_code and
                'execute(' in obj.source_code and
                ' + ' in obj.source_code
            ),
            severity=IssueSeverity.HIGH,
            message="Possible SQL injection vulnerability",
            recommendation="Use parameterized queries with placeholders"
        )
```

### Example 2: Code Library for Your Team's Standards

```yaml
# File: team-standards.yaml

examples:
  # Excellent: Our preferred logging pattern
  - id: "team-logging-001"
    classification: excellent
    pattern_type: general
    language: python
    description: "Standard logging pattern for our team"
    code: |
      import logging
      
      logger = logging.getLogger(__name__)
      
      def process_data(data):
          logger.info(f"Processing data: {data['id']}")
          try:
              result = do_work(data)
              logger.debug(f"Result: {result}")
              return result
          except Exception as e:
              logger.error(f"Processing failed: {e}", exc_info=True)
              raise
    tags: [logging, team-standard]

  # Bad: Anti-pattern we want to avoid
  - id: "team-antipattern-001"
    classification: bad
    pattern_type: structure
    language: python
    description: "Using global variables for state"
    reason: "Makes code hard to test and reason about"
    code: |
      # Global state
      user_data = {}
      
      def process_user(user_id):
          global user_data
          user_data[user_id] = fetch_user(user_id)
    alternative: "Pass state as parameters or use a class to encapsulate state"
    tags: [globals, state, team-antipattern]

  # Smelly: Acceptable but not ideal
  - id: "team-smell-001"
    classification: smelly
    pattern_type: structure
    language: python
    description: "Functions longer than 50 lines"
    reason: "Long functions are harder to understand and maintain"
    code: |
      def process_everything(data):
          # 50+ lines of code doing many things
          validate_input(data)
          transform_data(data)
          save_to_database(data)
          send_notifications(data)
          update_cache(data)
          log_analytics(data)
          # ... etc
    alternative: "Break into smaller, focused functions"
    tags: [complexity, team-standard]
```

### Example 3: Using Both Plugins and Library Together

```bash
# Analyze with custom plugins and team code library
code-analyzer analyze ./my-project \
  --plugins ./my-plugins \
  --code-library ./team-standards.yaml \
  --depth deep \
  --generate-docs \
  --logseq-graph ~/logseq
```

This will:
1. Run your custom plugin checks
2. Match code against your team's library
3. Generate issues for bad/smelly patterns found
4. Document everything in Logseq

---

## Configuration Example

Complete `.code-analyzer.yaml` with plugins and library:

```yaml
analysis:
  depth: deep
  ignore_patterns:
    - "*/tests/*"
    - "*/migrations/*"

plugins:
  directory: "./code-analyzer-plugins"

code_library:
  path: "./team-code-library.yaml"
  # OR use built-in examples:
  # use_default: true

documentation:
  logseq_graph: "~/logseq"
  create_index: true

tickets:
  enabled: true
```

---

## Best Practices

### For Plugins

1. **Keep plugins focused**: One plugin = one concern (security, naming, etc.)
2. **Use meaningful severity levels**: Critical for security issues, Low for style issues
3. **Provide helpful recommendations**: Tell developers how to fix the issue
4. **Handle errors gracefully**: Use try/except to avoid breaking analysis
5. **Test your plugins**: Test with various code patterns before deploying

### For Code Libraries

1. **Start small**: Begin with 5-10 key patterns your team cares about
2. **Be specific**: Avoid overly generic patterns that match everything
3. **Document why**: Always include `reason` for bad/smelly patterns
4. **Provide alternatives**: Show the better way to write the code
5. **Tag appropriately**: Use tags to organize and search examples
6. **Team review**: Have team review library additions to ensure consensus

---

## Troubleshooting

### Plugin Not Loading

- Check file is in plugins directory
- Verify plugin class extends `AnalyzerPlugin`
- Check for Python syntax errors
- Look for error messages in output

### Code Library Not Matching

- Lower similarity threshold (if configurable in future)
- Make library examples more general
- Check AST structure is similar (indentation doesn't matter)
- Ensure language is set to "python"

### Performance Issues

- Reduce library size (fewer examples)
- Use more specific patterns (fewer false matches)
- Run with `--depth medium` instead of `deep`
- Disable features you don't need
