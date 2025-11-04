"""Example plugin for code-analyzer.

This is a template/example showing how to create custom analyzer plugins.
Copy this to your plugins directory and customize.
"""

from typing import List
from code_analyzer.plugins import CustomRulePlugin, AnalyzerPlugin
from code_analyzer.models import (
    ModuleInfo, Issue, IssueType, IssueSeverity, CodeLocation
)


# Example 1: Simple custom rule plugin
class ExampleRulesPlugin(CustomRulePlugin):
    """Example plugin using rule-based approach."""
    
    @property
    def name(self) -> str:
        return "example-rules"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        
        # Rule: Check for TODO comments
        self.add_rule(
            name="no-todo-comments",
            check=lambda obj: (
                hasattr(obj, 'source_code') and 
                obj.source_code and 
                'TODO' in obj.source_code
            ),
            severity=IssueSeverity.LOW,
            message="TODO comment found - should be tracked as a ticket",
            recommendation="Create a ticket for this TODO and reference it in the comment"
        )
        
        # Rule: Require type hints on functions
        self.add_rule(
            name="require-type-hints",
            check=lambda obj: (
                hasattr(obj, 'parameters') and 
                hasattr(obj, 'return_type') and
                not obj.return_type
            ),
            severity=IssueSeverity.LOW,
            message="Function missing return type hint",
            recommendation="Add return type hint to improve code clarity"
        )
        
        # Rule: No single-letter variable names (except loop counters)
        self.add_rule(
            name="no-single-letter-vars",
            check=lambda obj: (
                hasattr(obj, 'name') and 
                len(obj.name) == 1 and 
                obj.name not in ['i', 'j', 'k', 'x', 'y', 'z', 'f']
            ),
            severity=IssueSeverity.LOW,
            message="Single-letter variable name (not a loop counter)",
            recommendation="Use descriptive variable names"
        )


# Example 2: Advanced custom plugin with full control
class ExampleAdvancedPlugin(AnalyzerPlugin):
    """Example plugin with full custom analysis logic."""
    
    @property
    def name(self) -> str:
        return "example-advanced"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        self.total_analyzed = 0
        self.issues_found = 0
    
    def analyze_module(self, module: ModuleInfo) -> List[Issue]:
        """Custom analysis logic for a module."""
        issues = []
        self.total_analyzed += 1
        
        # Check for missing module docstring
        if not module.docstring:
            issues.append(Issue(
                issue_type=IssueType.DOCUMENTATION,
                severity=IssueSeverity.LOW,
                title="Module missing docstring",
                description=f"Module {module.name} has no docstring",
                location=CodeLocation(
                    file_path=module.file_path,
                    line_start=1,
                    line_end=1
                ),
                recommendation="Add a module-level docstring explaining the module's purpose"
            ))
        
        # Check for very long functions
        for func in module.functions:
            if func.lines_of_code and func.lines_of_code > 50:
                issues.append(Issue(
                    issue_type=IssueType.CODE_SMELL,
                    severity=IssueSeverity.MEDIUM,
                    title="Function too long",
                    description=f"Function '{func.name}' has {func.lines_of_code} lines",
                    location=func.location,
                    recommendation="Consider breaking this function into smaller, focused functions"
                ))
        
        # Check for classes with too many methods
        for cls in module.classes:
            if len(cls.methods) > 15:
                issues.append(Issue(
                    issue_type=IssueType.CODE_SMELL,
                    severity=IssueSeverity.MEDIUM,
                    title="Class has too many methods",
                    description=f"Class '{cls.name}' has {len(cls.methods)} methods",
                    location=cls.location,
                    recommendation="Consider splitting this class (Single Responsibility Principle)"
                ))
        
        self.issues_found += len(issues)
        return issues
    
    def pre_analysis_hook(self, modules: List[ModuleInfo]) -> None:
        """Called before analysis begins."""
        print(f"   [ExampleAdvancedPlugin] Starting analysis of {len(modules)} modules")
    
    def post_analysis_hook(self, modules: List[ModuleInfo], all_issues: List[Issue]) -> None:
        """Called after analysis completes."""
        print(f"   [ExampleAdvancedPlugin] Found {self.issues_found} issues in {self.total_analyzed} modules")
    
    def generate_custom_findings(self, modules: List[ModuleInfo]) -> dict:
        """Generate custom metrics."""
        total_functions = sum(len(m.functions) for m in modules)
        total_classes = sum(len(m.classes) for m in modules)
        
        # Calculate average methods per class
        avg_methods = 0
        if total_classes > 0:
            total_methods = sum(len(cls.methods) for m in modules for cls in m.classes)
            avg_methods = total_methods / total_classes
        
        return {
            "total_functions": total_functions,
            "total_classes": total_classes,
            "average_methods_per_class": round(avg_methods, 2),
            "modules_analyzed": self.total_analyzed
        }


# Example 3: Security-focused plugin
class ExampleSecurityPlugin(CustomRulePlugin):
    """Example security-focused plugin."""
    
    @property
    def name(self) -> str:
        return "example-security"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        
        # Check for hardcoded secrets
        self.add_rule(
            name="no-hardcoded-secrets",
            check=lambda obj: (
                hasattr(obj, 'source_code') and 
                obj.source_code and
                any(pattern in obj.source_code.lower() 
                    for pattern in ['password =', 'api_key =', 'secret =', 'token ='])
            ),
            severity=IssueSeverity.CRITICAL,
            message="Possible hardcoded credential detected",
            recommendation="Use environment variables or secure credential management system"
        )
        
        # Check for eval() usage
        self.add_rule(
            name="no-eval",
            check=lambda obj: (
                hasattr(obj, 'source_code') and 
                obj.source_code and
                'eval(' in obj.source_code
            ),
            severity=IssueSeverity.CRITICAL,
            message="Use of eval() detected",
            recommendation="Use ast.literal_eval() or safer alternatives"
        )
        
        # Check for exec() usage
        self.add_rule(
            name="no-exec",
            check=lambda obj: (
                hasattr(obj, 'source_code') and 
                obj.source_code and
                'exec(' in obj.source_code
            ),
            severity=IssueSeverity.HIGH,
            message="Use of exec() detected",
            recommendation="Avoid dynamic code execution - consider safer alternatives"
        )
        
        # Check for shell=True in subprocess
        self.add_rule(
            name="no-shell-true",
            check=lambda obj: (
                hasattr(obj, 'source_code') and 
                obj.source_code and
                'shell=True' in obj.source_code
            ),
            severity=IssueSeverity.HIGH,
            message="subprocess with shell=True detected",
            recommendation="Use shell=False and pass command as list to prevent injection"
        )


# To use these plugins:
# 1. Copy this file to a directory (e.g., ./my-plugins/)
# 2. Run: code-analyzer analyze /path/to/project --plugins ./my-plugins/
# 3. Or add to .code-analyzer.yaml:
#    plugins:
#      directory: "./my-plugins"
