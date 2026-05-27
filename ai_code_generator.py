"""
Phase 4: AI-Powered Code Generation Engine
JARVIS uses LLM models to generate high-quality Python code for upgrades

Features:
- AI-generated custom code (not templates)
- Multi-model fallback (10+ free APIs)
- Code quality validation
- Context-aware generation
- Dependency analysis
- Best practices enforcement
- Automatic documentation generation
"""

import logging
import json
import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from or_client_v2 import OpenRouterClientV2
except ImportError:
    from or_client import OpenRouterClient as OpenRouterClientV2

logger = logging.getLogger("ai_code_generator")


@dataclass
class GeneratedCode:
    """AI-generated code artifact"""
    code: str
    language: str = "python"
    quality_score: float = 0.0
    model_used: str = ""
    generation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)
    docstring: str = ""
    test_cases: List[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class CodeGenerationRequest:
    """Request for AI code generation"""
    description: str
    context: str = ""
    language: str = "python"
    requirements: List[str] = field(default_factory=list)
    quality_level: str = "production"  # draft, production, research
    include_tests: bool = True
    include_docs: bool = True


class CodeQualityAnalyzer:
    """Analyzes and scores generated code quality"""
    
    QUALITY_METRICS = {
        "has_docstring": 5,
        "has_type_hints": 5,
        "has_error_handling": 10,
        "has_logging": 5,
        "has_tests": 15,
        "follows_pep8": 5,
        "uses_context_managers": 5,
        "no_bare_excepts": 5,
        "no_hardcoded_values": 5,
        "proper_imports": 10,
    }
    
    def __init__(self):
        self.logger = logging.getLogger("code_quality_analyzer")
    
    def analyze(self, code: str) -> Dict[str, any]:
        """Analyze code quality and return metrics"""
        metrics = {
            "score": 0,
            "max_score": sum(self.QUALITY_METRICS.values()),
            "issues": [],
            "warnings": [],
            "passed_checks": []
        }
        
        # Check for docstring
        if '"""' in code or "'''" in code:
            metrics["score"] += self.QUALITY_METRICS["has_docstring"]
            metrics["passed_checks"].append("Has docstring")
        else:
            metrics["issues"].append("Missing module/function docstring")
        
        # Check for type hints
        if "->" in code and ":" in code:
            metrics["score"] += self.QUALITY_METRICS["has_type_hints"]
            metrics["passed_checks"].append("Has type hints")
        else:
            metrics["warnings"].append("Missing type hints in function signatures")
        
        # Check for error handling
        if "try:" in code and "except" in code:
            metrics["score"] += self.QUALITY_METRICS["has_error_handling"]
            metrics["passed_checks"].append("Has error handling")
        else:
            metrics["issues"].append("Missing try/except blocks")
        
        # Check for logging
        if "logger" in code or "logging" in code:
            metrics["score"] += self.QUALITY_METRICS["has_logging"]
            metrics["passed_checks"].append("Uses logging")
        else:
            metrics["warnings"].append("No logging statements")
        
        # Check for tests
        if "def test_" in code or "assert " in code:
            metrics["score"] += self.QUALITY_METRICS["has_tests"]
            metrics["passed_checks"].append("Has test cases")
        
        # Check for context managers
        if "with " in code:
            metrics["score"] += self.QUALITY_METRICS["uses_context_managers"]
            metrics["passed_checks"].append("Uses context managers")
        
        # Check for bare excepts
        if "except:" in code:
            metrics["issues"].append("Bare except clause found")
        else:
            metrics["score"] += self.QUALITY_METRICS["no_bare_excepts"]
            metrics["passed_checks"].append("No bare except clauses")
        
        # Check for hardcoded values (simple heuristic)
        hardcoded_count = len(re.findall(r'=\s*["\'][\w@.-]+["\']', code))
        if hardcoded_count <= 3:
            metrics["score"] += self.QUALITY_METRICS["no_hardcoded_values"]
            metrics["passed_checks"].append("Minimal hardcoded values")
        
        # Calculate percentage
        max_score = metrics["max_score"]
        metrics["percentage"] = (metrics["score"] / max_score * 100) if max_score > 0 else 0
        
        return metrics


class DependencyExtractor:
    """Extracts and analyzes code dependencies"""
    
    STANDARD_LIBS = {
        'os', 'sys', 'json', 're', 'logging', 'pathlib', 'datetime',
        'typing', 'dataclasses', 'collections', 'itertools', 'functools',
        'threading', 'asyncio', 'urllib', 'socket', 'time', 'random',
        'math', 'hashlib', 'hmac', 'base64', 'pickle', 'csv', 'sqlite3',
    }
    
    def __init__(self):
        self.logger = logging.getLogger("dependency_extractor")
    
    def extract(self, code: str) -> Dict[str, List[str]]:
        """Extract imports and dependencies from code"""
        results = {
            "standard_libs": [],
            "third_party": [],
            "local_imports": [],
            "all_imports": []
        }
        
        # Extract import statements
        import_pattern = r'^(?:from|import)\s+(\S+)'
        for match in re.finditer(import_pattern, code, re.MULTILINE):
            module = match.group(1).split('.')[0]
            
            if module in self.STANDARD_LIBS:
                results["standard_libs"].append(module)
            elif module.startswith('.'):
                results["local_imports"].append(module)
            else:
                results["third_party"].append(module)
            
            results["all_imports"].append(module)
        
        # Remove duplicates
        for key in results:
            results[key] = list(set(results[key]))
        
        return results


class AICodeGenerator:
    """
    AI-powered code generation engine
    Generates high-quality Python code using LLM models
    """
    
    SYSTEM_PROMPT = """You are an expert Python code generator. Generate production-ready Python code that:
1. Includes comprehensive docstrings
2. Has proper type hints on all functions
3. Includes error handling with try/except
4. Uses logging statements
5. Follows PEP 8 style guide
6. Includes unit tests
7. Has clear variable names
8. Includes comments for complex logic
9. Validates inputs
10. Returns meaningful error messages

Format your response as pure Python code without markdown formatting."""

    GENERATION_PROMPT_TEMPLATE = """Generate Python code for: {description}

Context: {context}

Requirements:
{requirements}

Quality Level: {quality_level}

Include:
- Docstrings for all functions
- Type hints
- Error handling
- Logging
- Unit tests (if quality_level is 'production')

Return only the Python code, no explanations."""

    def __init__(self):
        self.logger = logging.getLogger("ai_code_generator")
        self.quality_analyzer = CodeQualityAnalyzer()
        self.dependency_extractor = DependencyExtractor()
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenRouter client"""
        try:
            self.client = OpenRouterClientV2()
            self.logger.info("AI Code Generator initialized with OpenRouter client")
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenRouter client: {e}")
            self.client = None
    
    def generate(self, request: CodeGenerationRequest) -> GeneratedCode:
        """Generate code using AI model"""
        import time
        start_time = time.time()
        
        if not self.client:
            self.logger.error("OpenRouter client not initialized")
            return self._generate_fallback(request)
        
        try:
            # Prepare requirements string
            requirements_str = "\n".join(f"- {req}" for req in request.requirements) if request.requirements else "- None specified"
            
            # Build prompt
            prompt = self.GENERATION_PROMPT_TEMPLATE.format(
                description=request.description,
                context=request.context,
                requirements=requirements_str,
                quality_level=request.quality_level
            )
            
            self.logger.info(f"Generating code: {request.description[:50]}...")
            
            # Call AI model
            response = self.client.query(
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                temperature=0.3,  # Lower for more deterministic output
                max_tokens=2000
            )
            
            code = response.strip()
            
            # Extract metadata
            quality_metrics = self.quality_analyzer.analyze(code)
            deps = self.dependency_extractor.extract(code)
            docstring = self._extract_docstring(code)
            tests = self._extract_tests(code)
            
            generation_time = time.time() - start_time
            
            generated = GeneratedCode(
                code=code,
                quality_score=quality_metrics["percentage"],
                model_used=self.client.model if hasattr(self.client, 'model') else "unknown",
                generation_time=generation_time,
                dependencies=deps["all_imports"],
                docstring=docstring,
                test_cases=tests,
                explanation=f"Generated using AI model with quality score {quality_metrics['percentage']:.1f}%"
            )
            
            self.logger.info(f"Code generated successfully (quality: {generated.quality_score:.1f}%, time: {generation_time:.2f}s)")
            return generated
            
        except Exception as e:
            self.logger.error(f"Error generating code: {e}")
            return self._generate_fallback(request)
    
    def _generate_fallback(self, request: CodeGenerationRequest) -> GeneratedCode:
        """Fallback template-based code generation"""
        self.logger.info("Using template-based fallback code generation")
        
        template = f'''"""
{request.description}

Auto-generated code module.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main execution function.
    
    {request.description}
    """
    try:
        logger.info("Starting execution...")
        # TODO: Implement {request.description}
        logger.info("Execution completed successfully")
    except Exception as e:
        logger.error(f"Execution failed: {{e}}")
        raise


if __name__ == "__main__":
    main()
'''
        
        return GeneratedCode(
            code=template,
            quality_score=40.0,
            model_used="template-fallback",
            dependencies=[],
            explanation="Fallback template (API unavailable)"
        )
    
    def _extract_docstring(self, code: str) -> str:
        """Extract module-level docstring from code"""
        match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_tests(self, code: str) -> List[str]:
        """Extract test function names from code"""
        tests = []
        for match in re.finditer(r'def (test_\w+)\(', code):
            tests.append(match.group(1))
        return tests
    
    def validate_and_improve(self, generated: GeneratedCode) -> GeneratedCode:
        """Validate generated code and suggest improvements"""
        quality_metrics = self.quality_analyzer.analyze(generated.code)
        
        improvements = []
        
        if "has_docstring" not in str(quality_metrics.get("passed_checks", [])):
            improvements.append("Add module and function docstrings")
        
        if "has_type_hints" not in str(quality_metrics.get("passed_checks", [])):
            improvements.append("Add type hints to function signatures")
        
        if "has_error_handling" not in str(quality_metrics.get("passed_checks", [])):
            improvements.append("Add try/except error handling")
        
        if quality_metrics.get("percentage", 0) < 70:
            generated.explanation += f"\n\nSuggested improvements:\n" + "\n".join(f"- {i}" for i in improvements)
        
        return generated


class CodeGenerationPipeline:
    """Complete pipeline for request → generation → validation → deployment"""
    
    def __init__(self):
        self.generator = AICodeGenerator()
        self.logger = logging.getLogger("code_generation_pipeline")
    
    def process(self, description: str, context: str = "", requirements: List[str] = None) -> GeneratedCode:
        """Process a code generation request end-to-end"""
        
        # Create request
        request = CodeGenerationRequest(
            description=description,
            context=context,
            requirements=requirements or [],
            quality_level="production",
            include_tests=True,
            include_docs=True
        )
        
        self.logger.info(f"Processing code generation request: {description}")
        
        # Generate code
        generated = self.generator.generate(request)
        
        # Validate and improve
        generated = self.generator.validate_and_improve(generated)
        
        self.logger.info(f"Generated code with quality score: {generated.quality_score:.1f}%")
        
        return generated
    
    def save_generated_code(self, generated: GeneratedCode, filename: str) -> Path:
        """Save generated code to file"""
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(generated.code)
        self.logger.info(f"Generated code saved to {filepath}")
        return filepath
    
    def get_summary(self, generated: GeneratedCode) -> Dict[str, any]:
        """Get summary of generated code"""
        return {
            "quality_score": generated.quality_score,
            "model_used": generated.model_used,
            "generation_time": f"{generated.generation_time:.2f}s",
            "dependencies": generated.dependencies,
            "test_count": len(generated.test_cases),
            "has_docstring": bool(generated.docstring),
            "timestamp": generated.timestamp.isoformat(),
            "explanation": generated.explanation
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test code generation
    pipeline = CodeGenerationPipeline()
    
    # Example 1: Simple function
    print("\n=== Example 1: URL Validator ===")
    generated = pipeline.process(
        description="Create a URL validator function that checks if a URL is valid using regex",
        requirements=["validate HTTP/HTTPS URLs", "support subdomains", "return boolean"]
    )
    print(f"Quality Score: {generated.quality_score:.1f}%")
    print(f"Model: {generated.model_used}")
    print(f"Generated in: {generated.generation_time:.2f}s")
    print(f"\n{generated.code[:500]}...")
    
    # Example 2: Data processing module
    print("\n=== Example 2: CSV Processor ===")
    generated = pipeline.process(
        description="Create a CSV file processor that reads, validates, and cleans data",
        requirements=["handle missing values", "validate data types", "log processing steps"]
    )
    print(f"Quality Score: {generated.quality_score:.1f}%")
    print(f"Tests: {len(generated.test_cases)} test cases")
    print(f"Summary: {pipeline.get_summary(generated)}")
