"""Generate interactive, runnable code examples for onboarding."""

from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path
from .models import ModuleInfo, ClassInfo, FunctionInfo


@dataclass
class CodeExample:
    """A runnable code example."""
    title: str
    description: str
    code: str
    expected_output: Optional[str] = None
    imports: List[str] = None
    prerequisites: List[str] = None


class InteractiveExamplesGenerator:
    """Generate runnable examples for key components."""
    
    def __init__(self, project_name: str, modules: List[ModuleInfo]):
        self.project_name = project_name
        self.modules = modules
        self.module_map = {m.name: m for m in modules}
    
    def generate_examples(self) -> List[CodeExample]:
        """Generate interactive examples for major components."""
        examples = []
        
        # Find main classes
        main_classes = self._find_main_classes()
        
        for cls_info in main_classes[:3]:  # Top 3 classes
            example = self._create_class_example(cls_info)
            if example:
                examples.append(example)
        
        # Find entry point functions
        entry_functions = self._find_entry_functions()
        for func_info, module in entry_functions[:2]:  # Top 2 functions
            example = self._create_function_example(func_info, module)
            if example:
                examples.append(example)
        
        # Generate common use case examples
        use_case_examples = self._generate_use_case_examples()
        examples.extend(use_case_examples[:2])
        
        return examples
    
    def _find_main_classes(self) -> List[tuple]:
        """Find the most important classes to demonstrate."""
        classes = []
        
        for module in self.modules:
            for cls in module.classes:
                # Score by: public class + has methods + reasonable complexity
                if not cls.name.startswith('_'):
                    score = 0
                    score += len(cls.methods) * 2
                    score += 10 if cls.docstring else 0
                    score += 5 if any(m.name in ['__init__', '__call__', 'run', 'execute', 'process'] 
                                    for m in cls.methods) else 0
                    
                    classes.append((score, cls, module))
        
        # Sort by score
        classes.sort(reverse=True, key=lambda x: x[0])
        return [(cls, mod) for _, cls, mod in classes]
    
    def _find_entry_functions(self) -> List[tuple]:
        """Find important entry point functions."""
        functions = []
        
        for module in self.modules:
            for func in module.functions:
                if func.name in ['main', 'run', 'execute', 'analyze', 'process', 'start']:
                    if not func.name.startswith('_'):
                        functions.append((func, module))
        
        return functions
    
    def _create_class_example(self, cls_info: tuple) -> Optional[CodeExample]:
        """Create a runnable example for a class."""
        cls, module = cls_info
        
        # Find __init__ method
        init_method = None
        for method in cls.methods:
            if method.name == '__init__':
                init_method = method
                break
        
        # Determine imports
        module_path = module.name.replace('/', '.').replace('.py', '')
        imports = [f"from {module_path} import {cls.name}"]
        
        # Generate example code
        code_lines = []
        
        # Create instance
        if init_method:
            # Try to infer parameters
            params = self._infer_init_params(init_method)
            code_lines.append(f"# Initialize {cls.name}")
            code_lines.append(f"instance = {cls.name}({params})")
        else:
            code_lines.append(f"# Create {cls.name} instance")
            code_lines.append(f"instance = {cls.name}()")
        
        code_lines.append("")
        
        # Call a main method if available
        main_methods = [m for m in cls.methods if m.name in ['run', 'execute', 'process', 'analyze', '__call__']]
        if main_methods:
            method = main_methods[0]
            params = self._infer_method_params(method)
            code_lines.append(f"# Use the {method.name} method")
            code_lines.append(f"result = instance.{method.name}({params})")
            code_lines.append("print(result)")
        else:
            # Just show the object
            code_lines.append("# Inspect the instance")
            code_lines.append("print(instance)")
        
        description = cls.docstring.split('\n')[0] if cls.docstring else f"Example usage of {cls.name}"
        
        return CodeExample(
            title=f"Using {cls.name}",
            description=description,
            code='\n'.join(code_lines),
            imports=imports,
            expected_output="# Output will show the result of the operation"
        )
    
    def _create_function_example(self, func_info: tuple, module: ModuleInfo) -> Optional[CodeExample]:
        """Create a runnable example for a function."""
        func = func_info
        
        # Determine imports
        module_path = module.name.replace('/', '.').replace('.py', '')
        imports = [f"from {module_path} import {func.name}"]
        
        # Generate example code
        code_lines = []
        params = self._infer_function_params(func)
        
        code_lines.append(f"# Call {func.name}")
        code_lines.append(f"result = {func.name}({params})")
        code_lines.append("print(result)")
        
        description = func.docstring.split('\n')[0] if func.docstring else f"Example usage of {func.name}()"
        
        return CodeExample(
            title=f"Calling {func.name}()",
            description=description,
            code='\n'.join(code_lines),
            imports=imports,
            expected_output="# Output will depend on your input parameters"
        )
    
    def _infer_init_params(self, method: 'MethodInfo') -> str:
        """Infer reasonable parameter values for __init__."""
        # Common parameter patterns
        param_examples = {
            'path': '"/path/to/project"',
            'project_path': '"."',
            'file_path': '"example.py"',
            'directory': '"."',
            'dir': '"."',
            'name': '"example"',
            'url': '"https://example.com"',
            'host': '"localhost"',
            'port': '8080',
            'debug': 'False',
            'verbose': 'False',
            'config': 'None',
            'options': 'None',
        }
        
        params = []
        if hasattr(method, 'args') and method.args:
            for arg in method.args[1:]:  # Skip 'self'
                if '=' in arg:
                    # Has default value
                    continue
                else:
                    # No default, need to provide
                    arg_name = arg.strip()
                    if arg_name in param_examples:
                        params.append(param_examples[arg_name])
                    elif 'path' in arg_name.lower():
                        params.append('"."')
                    elif 'name' in arg_name.lower():
                        params.append('"example"')
                    else:
                        params.append('...')  # Placeholder
        
        return ', '.join(params) if params else ''
    
    def _infer_method_params(self, method: 'MethodInfo') -> str:
        """Infer reasonable parameter values for a method."""
        return self._infer_function_params(method)
    
    def _infer_function_params(self, func: FunctionInfo) -> str:
        """Infer reasonable parameter values for a function."""
        if not hasattr(func, 'args') or not func.args:
            return ''
        
        param_examples = {
            'path': '"."',
            'file': '"example.py"',
            'text': '"Hello, World!"',
            'data': '{}',
            'value': '42',
            'name': '"example"',
        }
        
        params = []
        for arg in func.args:
            if '=' in arg:
                continue  # Has default
            arg_name = arg.strip()
            if arg_name in param_examples:
                params.append(param_examples[arg_name])
            else:
                params.append('...')
        
        return ', '.join(params) if params else ''
    
    def _generate_use_case_examples(self) -> List[CodeExample]:
        """Generate examples for common use cases."""
        examples = []
        
        # Example 1: Quick analysis
        if any('analyzer' in m.name.lower() for m in self.modules):
            examples.append(CodeExample(
                title="Quick Start: Analyze a Python Project",
                description="The fastest way to analyze a project and get insights",
                code=f"""# Analyze your project
from {self.project_name}.analyzer import CodeAnalyzer

analyzer = CodeAnalyzer('path/to/your/project')
result = analyzer.analyze(depth='deep')

# Print summary
print(f"Found {{len(result.issues)}} issues")
print(f"Analyzed {{len(result.modules)}} modules")

# Show critical issues
for issue in result.issues:
    if issue.severity == 'high':
        print(f"⚠️  {{issue.description}}")""",
                expected_output="""Found 18 issues
Analyzed 28 modules
⚠️  High complexity function detected""",
                imports=[f"from {self.project_name}.analyzer import CodeAnalyzer"]
            ))
        
        # Example 2: Generate documentation
        if any('logseq' in m.name.lower() or 'doc' in m.name.lower() for m in self.modules):
            examples.append(CodeExample(
                title="Generate Documentation",
                description="Generate Logseq documentation for your project",
                code=f"""# Generate Logseq docs
from {self.project_name}.analyzer import CodeAnalyzer
from {self.project_name}.logseq_doc import LogseqDocGenerator

# Analyze project
analyzer = CodeAnalyzer('path/to/project')
result = analyzer.analyze()

# Generate docs
doc_gen = LogseqDocGenerator('path/to/logseq/graph')
doc_gen.generate_documentation(result, 'MyProject')

print("Documentation generated!")""",
                expected_output="Documentation generated!\nCreated 5 pages in Logseq",
                imports=[
                    f"from {self.project_name}.analyzer import CodeAnalyzer",
                    f"from {self.project_name}.logseq_doc import LogseqDocGenerator"
                ]
            ))
        
        return examples


def format_example(example: CodeExample) -> List[str]:
    """Format an example as markdown."""
    output = []
    
    output.append(f"### {example.title}")
    output.append("")
    output.append(example.description)
    output.append("")
    
    if example.prerequisites:
        output.append("**Prerequisites**:")
        for prereq in example.prerequisites:
            output.append(f"- {prereq}")
        output.append("")
    
    if example.imports:
        output.append("**Imports**:")
        output.append("```python")
        for imp in example.imports:
            output.append(imp)
        output.append("```")
        output.append("")
    
    output.append("**Example**:")
    output.append("```python")
    output.append(example.code)
    output.append("```")
    output.append("")
    
    if example.expected_output:
        output.append("**Expected Output**:")
        output.append("```")
        output.append(example.expected_output)
        output.append("```")
        output.append("")
    
    return output
