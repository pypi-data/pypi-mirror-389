"""Tests for code library system."""

import pytest
from pathlib import Path
from code_analyzer.code_library import (
    CodeLibrary, CodeExample, CodeQuality, PatternType,
    PatternMatcher, PatternMatch, create_default_library
)
from code_analyzer.models import (
    ModuleInfo, FunctionInfo, ClassInfo, 
    CodeLocation, Issue, IssueSeverity
)


class TestCodeQuality:
    """Tests for CodeQuality enum."""
    
    def test_quality_levels(self):
        """Test all quality levels exist."""
        assert CodeQuality.EXCELLENT.value == "excellent"
        assert CodeQuality.GOOD.value == "good"
        assert CodeQuality.SMELLY.value == "smelly"
        assert CodeQuality.BAD.value == "bad"


class TestPatternType:
    """Tests for PatternType enum."""
    
    def test_pattern_types(self):
        """Test common pattern types exist."""
        assert PatternType.SECURITY.value == "security"
        assert PatternType.ERROR_HANDLING.value == "error_handling"
        assert PatternType.STRUCTURE.value == "structure"
        assert PatternType.PERFORMANCE.value == "performance"


class TestCodeExample:
    """Tests for CodeExample model."""
    
    def test_create_example(self):
        """Test creating a code example."""
        example = CodeExample(
            id="test-001",
            classification=CodeQuality.EXCELLENT,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="secure_code = True",
            description="Test example"
        )
        
        assert example.id == "test-001"
        assert example.classification == CodeQuality.EXCELLENT
        assert example.pattern_type == PatternType.SECURITY
        assert example.language == "python"
    
    def test_example_with_strings(self):
        """Test creating example with string values."""
        example = CodeExample(
            id="test-002",
            classification="bad",  # String instead of enum
            pattern_type="security",  # String instead of enum
            language="python",
            code="bad_code = True"
        )
        
        # Should convert strings to enums
        assert example.classification == CodeQuality.BAD
        assert example.pattern_type == PatternType.SECURITY
    
    def test_example_with_alternative(self):
        """Test example with alternative code."""
        example = CodeExample(
            id="test-003",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="eval(user_input)",
            description="Using eval",
            reason="Security risk",
            alternative="Use ast.literal_eval() instead",
            tags=["security", "eval"]
        )
        
        assert example.reason == "Security risk"
        assert example.alternative is not None
        assert "security" in example.tags


class TestCodeLibrary:
    """Tests for CodeLibrary."""
    
    def test_create_empty_library(self):
        """Test creating an empty library."""
        library = CodeLibrary()
        assert len(library.examples) == 0
    
    def test_add_example(self):
        """Test adding an example to library."""
        library = CodeLibrary()
        example = CodeExample(
            id="test-001",
            classification=CodeQuality.GOOD,
            pattern_type=PatternType.GENERAL,
            language="python",
            code="good_code()"
        )
        
        library.add_example(example)
        assert len(library.examples) == 1
        assert library.examples[0].id == "test-001"
    
    def test_get_by_quality(self):
        """Test filtering examples by quality."""
        library = CodeLibrary()
        
        library.add_example(CodeExample(
            id="excellent-001",
            classification=CodeQuality.EXCELLENT,
            pattern_type=PatternType.GENERAL,
            language="python",
            code="excellent()"
        ))
        
        library.add_example(CodeExample(
            id="bad-001",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.GENERAL,
            language="python",
            code="bad()"
        ))
        
        excellent = library.get_by_quality(CodeQuality.EXCELLENT)
        bad = library.get_by_quality(CodeQuality.BAD)
        
        assert len(excellent) == 1
        assert len(bad) == 1
        assert excellent[0].id == "excellent-001"
        assert bad[0].id == "bad-001"
    
    def test_get_by_pattern(self):
        """Test filtering examples by pattern type."""
        library = CodeLibrary()
        
        library.add_example(CodeExample(
            id="security-001",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="insecure()"
        ))
        
        library.add_example(CodeExample(
            id="performance-001",
            classification=CodeQuality.SMELLY,
            pattern_type=PatternType.PERFORMANCE,
            language="python",
            code="slow()"
        ))
        
        security = library.get_by_pattern(PatternType.SECURITY)
        performance = library.get_by_pattern(PatternType.PERFORMANCE)
        
        assert len(security) == 1
        assert len(performance) == 1
    
    def test_get_by_tag(self):
        """Test filtering examples by tag."""
        library = CodeLibrary()
        
        library.add_example(CodeExample(
            id="test-001",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="bad()",
            tags=["injection", "security"]
        ))
        
        library.add_example(CodeExample(
            id="test-002",
            classification=CodeQuality.GOOD,
            pattern_type=PatternType.GENERAL,
            language="python",
            code="good()",
            tags=["best-practice"]
        ))
        
        security_tagged = library.get_by_tag("security")
        practice_tagged = library.get_by_tag("best-practice")
        
        assert len(security_tagged) == 1
        assert len(practice_tagged) == 1


class TestPatternMatcher:
    """Tests for PatternMatcher."""
    
    def test_create_matcher(self):
        """Test creating a pattern matcher."""
        library = CodeLibrary()
        matcher = PatternMatcher(library)
        
        assert matcher.library == library
        assert matcher.similarity_threshold == 0.7  # Default
    
    def test_custom_threshold(self):
        """Test creating matcher with custom threshold."""
        library = CodeLibrary()
        matcher = PatternMatcher(library, similarity_threshold=0.5)
        
        assert matcher.similarity_threshold == 0.5
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        library = CodeLibrary()
        matcher = PatternMatcher(library)
        
        # Identical code
        code1 = "def foo():\n    pass"
        code2 = "def foo():\n    pass"
        similarity = matcher._calculate_similarity(code1, code2)
        assert similarity > 0.9  # Should be very high
        
        # Completely different
        code3 = "def bar():\n    return 42"
        similarity = matcher._calculate_similarity(code1, code3)
        assert similarity < 1.0  # Should be lower
    
    def test_find_matches(self):
        """Test finding pattern matches in code."""
        library = CodeLibrary()
        library.add_example(CodeExample(
            id="eval-bad",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="result = eval(user_input)",
            reason="Security risk"
        ))
        
        matcher = PatternMatcher(library, similarity_threshold=0.5)
        
        # Create module with similar code
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=3)
        func = FunctionInfo(
            name="process",
            location=loc,
            parameters=[],
            return_type=None,
            docstring=None,
            complexity=1,
            source_code="output = eval(data)"  # Similar to library example
        )
        module = ModuleInfo(
            name="test",
            file_path="test.py",
            docstring=None,
            functions=[func]
        )
        
        matches = matcher.find_matches(module)
        
        # Should find at least one match
        assert len(matches) >= 1
        assert matches[0].example.id == "eval-bad"
        assert matches[0].similarity >= 0.5
    
    def test_no_matches(self):
        """Test when no patterns match."""
        library = CodeLibrary()
        library.add_example(CodeExample(
            id="eval-bad",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="result = eval(user_input)"
        ))
        
        matcher = PatternMatcher(library, similarity_threshold=0.9)
        
        # Create module with completely different code
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=3)
        func = FunctionInfo(
            name="process",
            location=loc,
            parameters=[],
            return_type=None,
            docstring=None,
            complexity=1,
            source_code="return 42"  # Very different
        )
        module = ModuleInfo(
            name="test",
            file_path="test.py",
            docstring=None,
            functions=[func]
        )
        
        matches = matcher.find_matches(module)
        assert len(matches) == 0
    
    def test_generate_issues_from_matches(self):
        """Test generating issues from bad/smelly matches."""
        library = CodeLibrary()
        
        # Create a bad pattern
        bad_example = CodeExample(
            id="bad-001",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="bad()",
            reason="This is bad",
            alternative="Do this instead"
        )
        
        # Create a match
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=1)
        match = PatternMatch(
            example=bad_example,
            location=loc,
            similarity=0.85,
            matched_code="bad()",
            context="Function: test"
        )
        
        matcher = PatternMatcher(library)
        issues = matcher.generate_issues_from_matches([match])
        
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.HIGH  # Bad = HIGH
        assert "bad" in issues[0].title.lower()
    
    def test_no_issues_for_good_patterns(self):
        """Test that excellent/good patterns don't generate issues."""
        library = CodeLibrary()
        
        # Create an excellent pattern
        good_example = CodeExample(
            id="good-001",
            classification=CodeQuality.EXCELLENT,
            pattern_type=PatternType.GENERAL,
            language="python",
            code="good()"
        )
        
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=1)
        match = PatternMatch(
            example=good_example,
            location=loc,
            similarity=0.95,
            matched_code="good()",
            context="Function: test"
        )
        
        matcher = PatternMatcher(library)
        issues = matcher.generate_issues_from_matches([match])
        
        # Excellent patterns should not generate issues
        assert len(issues) == 0
    
    def test_generate_quality_report(self):
        """Test generating quality report from matches."""
        library = CodeLibrary()
        matcher = PatternMatcher(library)
        
        # Create matches with different qualities
        excellent = CodeExample(
            id="excellent-001",
            classification=CodeQuality.EXCELLENT,
            pattern_type=PatternType.GENERAL,
            language="python",
            code="excellent()"
        )
        
        bad = CodeExample(
            id="bad-001",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="bad()"
        )
        
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=1)
        
        matches = [
            PatternMatch(excellent, loc, 0.9, "excellent()", "test"),
            PatternMatch(bad, loc, 0.8, "bad()", "test")
        ]
        
        report = matcher.generate_quality_report(matches)
        
        assert report['total_matches'] == 2
        assert 'quality_score' in report
        assert report['quality_distribution']['excellent'] == 1
        assert report['quality_distribution']['bad'] == 1


class TestDefaultLibrary:
    """Tests for default code library."""
    
    def test_create_default_library(self):
        """Test creating default library."""
        library = create_default_library()
        
        # Should have some examples
        assert len(library.examples) > 0
        
        # Should have different quality levels
        excellent = library.get_by_quality(CodeQuality.EXCELLENT)
        bad = library.get_by_quality(CodeQuality.BAD)
        
        assert len(excellent) > 0
        assert len(bad) > 0
    
    def test_default_has_security_examples(self):
        """Test that default library has security examples."""
        library = create_default_library()
        
        security = library.get_by_pattern(PatternType.SECURITY)
        assert len(security) > 0
    
    def test_default_has_error_handling(self):
        """Test that default library has error handling examples."""
        library = create_default_library()
        
        error_handling = library.get_by_pattern(PatternType.ERROR_HANDLING)
        assert len(error_handling) > 0


class TestPatternMatch:
    """Tests for PatternMatch model."""
    
    def test_create_pattern_match(self):
        """Test creating a pattern match."""
        example = CodeExample(
            id="test-001",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="bad()"
        )
        
        loc = CodeLocation(file_path="test.py", line_start=1, line_end=1)
        
        match = PatternMatch(
            example=example,
            location=loc,
            similarity=0.85,
            matched_code="bad()",
            context="Function: test"
        )
        
        assert match.example.id == "test-001"
        assert match.similarity == 0.85
        assert match.matched_code == "bad()"
        assert match.context == "Function: test"


class TestIntegration:
    """Integration tests for code library system."""
    
    def test_full_workflow(self):
        """Test complete workflow: library → matcher → issues."""
        # 1. Create library with bad pattern
        library = CodeLibrary()
        library.add_example(CodeExample(
            id="hardcoded-password",
            classification=CodeQuality.BAD,
            pattern_type=PatternType.SECURITY,
            language="python",
            code="password = 'secret123'",
            reason="Hardcoded credentials",
            alternative="Use environment variables"
        ))
        
        # 2. Create matcher
        matcher = PatternMatcher(library, similarity_threshold=0.6)
        
        # 3. Create code to analyze
        loc = CodeLocation(file_path="app.py", line_start=10, line_end=10)
        func = FunctionInfo(
            name="connect",
            location=loc,
            parameters=[],
            return_type=None,
            docstring=None,
            complexity=1,
            source_code="password = 'hardcoded123'"
        )
        module = ModuleInfo(
            name="app",
            file_path="app.py",
            docstring=None,
            functions=[func]
        )
        
        # 4. Find matches
        matches = matcher.find_matches(module)
        assert len(matches) > 0
        
        # 5. Generate issues
        issues = matcher.generate_issues_from_matches(matches)
        assert len(issues) > 0
        assert issues[0].severity == IssueSeverity.HIGH
        
        # 6. Generate report
        report = matcher.generate_quality_report(matches)
        assert report['total_matches'] > 0
        assert report['quality_distribution']['bad'] > 0
