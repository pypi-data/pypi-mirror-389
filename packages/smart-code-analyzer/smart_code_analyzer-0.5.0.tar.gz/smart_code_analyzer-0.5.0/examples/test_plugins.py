"""Test script to verify plugin and code library functionality.

Run this to test that the plugin system and code library work correctly.
"""

from pathlib import Path
from code_analyzer.plugins import CustomRulePlugin, PluginManager
from code_analyzer.models import ModuleInfo, FunctionInfo, IssueSeverity, CodeLocation
from code_analyzer.code_library import (
    CodeLibrary, CodeExample, CodeQuality, PatternType, PatternMatcher
)


def test_plugin_system():
    """Test that plugins can be created and registered."""
    print("\n=== Testing Plugin System ===\n")
    
    # Create a simple test plugin
    class TestPlugin(CustomRulePlugin):
        @property
        def name(self):
            return "test-plugin"
        
        @property
        def version(self):
            return "1.0.0"
        
        def __init__(self):
            super().__init__()
            self.add_rule(
                name="test-rule",
                check=lambda obj: hasattr(obj, 'name') and obj.name == "test_function",
                severity=IssueSeverity.LOW,
                message="Test rule triggered",
                recommendation="This is a test"
            )
    
    # Create plugin manager and register plugin
    manager = PluginManager()
    plugin = TestPlugin()
    manager.register_plugin(plugin)
    
    print(f"✅ Registered plugin: {plugin.name} v{plugin.version}")
    
    # Create a test module
    test_module = ModuleInfo(
        name="test_module",
        file_path="test.py",
        docstring=None,
        functions=[
            FunctionInfo(
                name="test_function",
                location=CodeLocation(file_path="test.py", line_start=1, line_end=5),
                parameters=[],
                return_type=None,
                docstring="Test function",
                complexity=1
            )
        ]
    )
    
    # Run analysis
    issues = manager.run_analysis([test_module])
    
    print(f"✅ Plugin analysis complete: {len(issues)} issue(s) found")
    if issues:
        print(f"   - {issues[0].title}: {issues[0].description}")
    
    return len(issues) > 0


def test_code_library():
    """Test that code library can classify and match code."""
    print("\n=== Testing Code Library ===\n")
    
    # Create a library with test examples
    library = CodeLibrary()
    
    # Add a bad example
    library.add_example(CodeExample(
        id="test-bad-001",
        classification=CodeQuality.BAD,
        pattern_type=PatternType.SECURITY,
        language="python",
        code="password = 'hardcoded123'",
        description="Hardcoded password",
        reason="Security vulnerability",
        alternative="Use environment variables"
    ))
    
    print(f"✅ Created code library with {len(library.examples)} example(s)")
    
    # Create pattern matcher
    matcher = PatternMatcher(library, similarity_threshold=0.5)
    
    print(f"✅ Created pattern matcher (threshold: 50%)")
    
    # Create test module with similar code
    test_module = ModuleInfo(
        name="test_module",
        file_path="test.py",
        docstring=None,
        functions=[
            FunctionInfo(
                name="connect",
                location=CodeLocation(file_path="test.py", line_start=1, line_end=5),
                parameters=[],
                return_type=None,
                docstring="Test function",
                complexity=1,
                source_code="password = 'secret123'"  # Similar to library example
            )
        ]
    )
    
    # Find matches
    matches = matcher.find_matches(test_module)
    
    print(f"✅ Pattern matching complete: {len(matches)} match(es) found")
    if matches:
        print(f"   - Matched '{matches[0].example.id}' with {matches[0].similarity:.1%} similarity")
    
    # Generate issues from matches
    issues = matcher.generate_issues_from_matches(matches)
    print(f"✅ Generated {len(issues)} issue(s) from matches")
    
    return len(matches) > 0


def test_quality_levels():
    """Test that all quality levels work."""
    print("\n=== Testing Quality Levels ===\n")
    
    library = CodeLibrary()
    
    # Add examples of each quality level
    quality_levels = [
        (CodeQuality.EXCELLENT, "excellent-001"),
        (CodeQuality.GOOD, "good-001"),
        (CodeQuality.SMELLY, "smelly-001"),
        (CodeQuality.BAD, "bad-001"),
    ]
    
    for quality, example_id in quality_levels:
        library.add_example(CodeExample(
            id=example_id,
            classification=quality,
            pattern_type=PatternType.GENERAL,
            language="python",
            code=f"# {quality.value} code example",
            description=f"Example of {quality.value} code"
        ))
        print(f"✅ Added {quality.value} example: {example_id}")
    
    # Test filtering by quality
    for quality in CodeQuality:
        examples = library.get_by_quality(quality)
        print(f"   - {quality.value}: {len(examples)} example(s)")
    
    return len(library.examples) == 4


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Plugin System & Code Library Tests")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Plugin System", test_plugin_system()))
    except Exception as e:
        print(f"❌ Plugin system test failed: {e}")
        results.append(("Plugin System", False))
    
    try:
        results.append(("Code Library", test_code_library()))
    except Exception as e:
        print(f"❌ Code library test failed: {e}")
        results.append(("Code Library", False))
    
    try:
        results.append(("Quality Levels", test_quality_levels()))
    except Exception as e:
        print(f"❌ Quality levels test failed: {e}")
        results.append(("Quality Levels", False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
