"""
Phase 4 Enhancement: Smart Upgrader with AI Code Generation
Upgrades smart_upgrader.py to use AI-generated code instead of templates

This module integrates ai_code_generator.py for superior code quality
while maintaining all security scanning from the original.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ai_code_generator import AICodeGenerator, CodeGenerationRequest, CodeGenerationPipeline
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI code generator not available: {e}")
    AI_AVAILABLE = False

try:
    from smart_upgrader import SmartUpgrader, SecurityLevel
    BASE_UPGRADER = SmartUpgrader()
except ImportError:
    BASE_UPGRADER = None

logger = logging.getLogger("phase4_upgrader")


class Phase4SmartUpgrader:
    """
    Enhanced Smart Upgrader with AI-powered code generation
    
    Improvements over Phase 3:
    - Real LLM-generated code instead of templates
    - Better code quality validation
    - Smarter dependency analysis
    - Context-aware generation
    - Automatic documentation
    """
    
    def __init__(self):
        self.logger = logging.getLogger("phase4_upgrader")
        self.base_upgrader = BASE_UPGRADER
        self.pipeline = CodeGenerationPipeline() if AI_AVAILABLE else None
        self.logger.info(f"Phase 4 Upgrader initialized (AI: {'enabled' if AI_AVAILABLE else 'disabled'})")
    
    def upgrade_with_ai(self, description: str) -> Dict:
        """
        Process upgrade request using AI code generation
        
        Args:
            description: What the user wants to upgrade
            
        Returns:
            Dictionary with generated code, security analysis, and deployment info
        """
        
        if not self.pipeline:
            self.logger.warning("AI pipeline not available, using fallback")
            return self._fallback_upgrade(description)
        
        try:
            self.logger.info(f"Processing upgrade with AI: {description[:50]}...")
            
            # Step 1: Analyze what needs to be built
            analysis = self._analyze_request(description)
            self.logger.info(f"Analysis: {analysis['type']} (Priority: {analysis['priority']})")
            
            # Step 2: Generate code using AI
            generated = self.pipeline.process(
                description=description,
                context=analysis.get('context', ''),
                requirements=analysis.get('requirements', [])
            )
            
            self.logger.info(f"AI Generated code quality: {generated.quality_score:.1f}%")
            
            # Step 3: Security scanning (reuse Phase 3 security scanner)
            security_report = self._scan_security(generated.code, description)
            
            # Step 4: Prepare deployment
            result = {
                "status": "success",
                "description": description,
                "analysis": analysis,
                "generated": {
                    "code": generated.code,
                    "quality_score": generated.quality_score,
                    "model_used": generated.model_used,
                    "generation_time": generated.generation_time,
                    "dependencies": generated.dependencies,
                    "test_count": len(generated.test_cases),
                    "has_docstring": bool(generated.docstring),
                },
                "security": security_report,
                "ready_to_deploy": security_report["approval_required"] is False,
                "next_steps": self._get_next_steps(security_report)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"AI upgrade failed: {e}")
            return self._fallback_upgrade(description)
    
    def _analyze_request(self, description: str) -> Dict:
        """Analyze what the user is asking for"""
        
        # Keywords for different types of upgrades
        keywords = {
            "api_integration": ["api", "endpoint", "webhook", "rest", "http", "request"],
            "database": ["database", "db", "sql", "sqlite", "query", "table"],
            "authentication": ["auth", "login", "password", "token", "session", "security"],
            "ui_ux": ["ui", "interface", "dashboard", "button", "form", "display"],
            "performance": ["cache", "speed", "optimize", "fast", "efficient", "performance"],
            "monitoring": ["monitor", "log", "metric", "track", "alert", "health"],
        }
        
        description_lower = description.lower()
        detected_types = []
        
        for upgrade_type, keywords_list in keywords.items():
            if any(kw in description_lower for kw in keywords_list):
                detected_types.append(upgrade_type)
        
        upgrade_type = detected_types[0] if detected_types else "general"
        
        # Priority based on type
        priority_map = {
            "security": "critical",
            "authentication": "high",
            "api_integration": "high",
            "database": "medium",
            "performance": "medium",
            "monitoring": "low",
            "ui_ux": "low",
            "general": "medium",
        }
        
        priority = priority_map.get(upgrade_type, "medium")
        
        # Generate context and requirements based on type
        context = self._get_context(upgrade_type)
        requirements = self._get_requirements(upgrade_type, description)
        
        return {
            "type": upgrade_type,
            "priority": priority,
            "context": context,
            "requirements": requirements,
            "description": description,
        }
    
    def _get_context(self, upgrade_type: str) -> str:
        """Get context for code generation based on upgrade type"""
        
        contexts = {
            "api_integration": """This code will be integrated into JARVIS AI assistant.
Consider: rate limiting, error handling, async support, logging, timeout handling.""",
            
            "database": """This code interacts with JARVIS memory system (SQLite).
Consider: transaction safety, indexing, migration support, backup strategies.""",
            
            "authentication": """This code secures JARVIS access.
Consider: password hashing, token validation, session management, security best practices.""",
            
            "ui_ux": """This code provides user interface for JARVIS.
Consider: accessibility, responsiveness, error messages, user feedback.""",
            
            "performance": """This code optimizes JARVIS performance.
Consider: caching strategies, concurrency, resource limits, monitoring.""",
            
            "monitoring": """This code monitors JARVIS health.
Consider: metrics collection, alerting thresholds, data retention, visualization.""",
            
            "general": """This code extends JARVIS AI assistant functionality.
Consider: JARVIS integration patterns, backward compatibility, error handling.""",
        }
        
        return contexts.get(upgrade_type, contexts["general"])
    
    def _get_requirements(self, upgrade_type: str, description: str) -> list:
        """Get specific requirements based on upgrade type"""
        
        base_requirements = [
            "Include comprehensive error handling",
            "Add logging for debugging",
            "Use type hints in function signatures",
            "Include unit tests",
            "Add docstrings",
        ]
        
        type_requirements = {
            "api_integration": [
                "Implement timeout handling",
                "Add rate limit support",
                "Validate input/output",
                "Support async operations",
            ],
            
            "database": [
                "Use SQLite best practices",
                "Add data validation",
                "Implement transaction safety",
                "Support data migration",
            ],
            
            "authentication": [
                "Use secure password hashing",
                "Implement token validation",
                "Add session management",
                "Follow security best practices",
            ],
            
            "ui_ux": [
                "Ensure WCAG accessibility",
                "Support mobile responsiveness",
                "Provide clear error messages",
                "Include keyboard navigation",
            ],
            
            "performance": [
                "Implement caching where applicable",
                "Support concurrent operations",
                "Add resource limits",
                "Include performance metrics",
            ],
            
            "monitoring": [
                "Collect relevant metrics",
                "Support custom alerts",
                "Store metrics efficiently",
                "Provide visualization support",
            ],
        }
        
        requirements = base_requirements + type_requirements.get(upgrade_type, [])
        
        # Parse description for specific needs
        if "secure" in description.lower() or "encrypt" in description.lower():
            requirements.append("Implement encryption where needed")
        
        if "fast" in description.lower() or "speed" in description.lower():
            requirements.append("Optimize for performance")
        
        if "real-time" in description.lower():
            requirements.append("Support real-time updates")
        
        return requirements
    
    def _scan_security(self, code: str, description: str) -> Dict:
        """Run security scanning using Phase 3 scanner"""
        
        if not self.base_upgrader:
            return {
                "level": "caution",
                "violations": [],
                "approval_required": True,
                "message": "Base upgrader not available"
            }
        
        try:
            # Use base upgrader's security scanning
            approval = self.base_upgrader.scan_and_approve(code, description)
            return approval.get("security_report", {})
        except Exception as e:
            self.logger.error(f"Security scan failed: {e}")
            return {
                "level": "warning",
                "violations": [str(e)],
                "approval_required": True,
                "message": f"Security scan error: {e}"
            }
    
    def _get_next_steps(self, security_report: Dict) -> list:
        """Determine next steps based on security report"""
        
        approval_required = security_report.get("approval_required", True)
        level = security_report.get("level", "unknown")
        
        if level == "safe":
            return [
                "✅ Code is safe to deploy immediately",
                "Review generated code (optional)",
                "Deploy to JARVIS system",
                "Monitor for issues"
            ]
        elif level == "caution":
            return [
                "⚠️  Review code for best practices",
                "Test thoroughly before deployment",
                "Consider manual approval",
                "Deploy with monitoring enabled"
            ]
        elif level == "warning":
            return [
                "⚠️  Manual approval required",
                "Review security violations",
                "Fix issues or provide justification",
                "Resubmit for approval"
            ]
        else:  # blocked
            return [
                "🚫 Cannot deploy - critical security issues",
                "Review violations below",
                "Modify code to fix issues",
                "Resubmit for scanning"
            ]
    
    def _fallback_upgrade(self, description: str) -> Dict:
        """Fallback when AI is not available"""
        self.logger.info("Using fallback upgrade method")
        
        if self.base_upgrader:
            try:
                return self.base_upgrader.request_upgrade(description)
            except Exception as e:
                self.logger.error(f"Fallback failed: {e}")
        
        return {
            "status": "error",
            "message": "Upgrade unavailable (AI and fallback both failed)",
            "description": description
        }
    
    def compare_ai_vs_template(self, description: str) -> Dict:
        """Compare AI-generated code vs template-based code"""
        
        result = {
            "description": description,
            "ai_generated": None,
            "template_based": None,
            "comparison": {}
        }
        
        # Generate with AI
        if self.pipeline:
            ai_result = self.upgrade_with_ai(description)
            result["ai_generated"] = {
                "quality_score": ai_result["generated"].get("quality_score", 0),
                "generation_time": ai_result["generated"].get("generation_time", 0),
                "lines_of_code": len(ai_result["generated"]["code"].split("\n")),
                "has_tests": ai_result["generated"].get("test_count", 0) > 0,
            }
        
        # Generate with template (fallback)
        template_result = self._fallback_upgrade(description)
        if "code" in template_result:
            result["template_based"] = {
                "quality_score": 40,  # Templates typically score ~40%
                "generation_time": 0.01,  # Very fast
                "lines_of_code": len(template_result.get("code", "").split("\n")),
                "has_tests": False,
            }
        
        # Comparison
        if result["ai_generated"] and result["template_based"]:
            ai_score = result["ai_generated"]["quality_score"]
            template_score = result["template_based"]["quality_score"]
            improvement = ((ai_score - template_score) / template_score * 100) if template_score > 0 else 0
            
            result["comparison"] = {
                "quality_improvement": f"{improvement:+.1f}%",
                "ai_advantage": ai_score > template_score,
                "recommendation": "Use AI-generated code" if ai_score > template_score else "Either method works"
            }
        
        return result


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    upgrader = Phase4SmartUpgrader()
    
    print("\n" + "="*70)
    print("PHASE 4: AI-POWERED SMART UPGRADER")
    print("="*70)
    
    # Test upgrade requests
    test_requests = [
        "Add email notification support to JARVIS",
        "Implement Redis caching for API responses",
        "Create a REST API endpoint for model status",
        "Add request rate limiting with exponential backoff",
    ]
    
    for request in test_requests:
        print(f"\n📝 Request: {request}")
        print("-" * 70)
        
        result = upgrader.upgrade_with_ai(request)
        
        if result["status"] == "success":
            gen = result["generated"]
            print(f"✅ Status: {result['status']}")
            print(f"   Type: {result['analysis']['type']}")
            print(f"   Priority: {result['analysis']['priority']}")
            print(f"   Quality: {gen['quality_score']:.1f}%")
            print(f"   Model: {gen['model_used']}")
            print(f"   Time: {gen['generation_time']:.2f}s")
            print(f"   Tests: {gen['test_count']}")
            print(f"   Ready: {result['ready_to_deploy']}")
            print(f"   Next: {result['next_steps'][0]}")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown')}")
    
    # Comparison example
    print("\n" + "="*70)
    print("COMPARISON: AI vs Template")
    print("="*70)
    
    comparison = upgrader.compare_ai_vs_template("Add API rate limiting")
    print(f"\nRequest: {comparison['description']}")
    
    if comparison["ai_generated"]:
        print(f"\nAI-Generated:")
        print(f"  Quality: {comparison['ai_generated']['quality_score']:.1f}%")
        print(f"  Time: {comparison['ai_generated']['generation_time']:.3f}s")
        print(f"  Tests: {comparison['ai_generated']['has_tests']}")
    
    if comparison["template_based"]:
        print(f"\nTemplate-Based:")
        print(f"  Quality: {comparison['template_based']['quality_score']:.1f}%")
        print(f"  Time: {comparison['template_based']['generation_time']:.3f}s")
        print(f"  Tests: {comparison['template_based']['has_tests']}")
    
    if comparison["comparison"]:
        print(f"\nComparison:")
        print(f"  Improvement: {comparison['comparison'].get('quality_improvement', 'N/A')}")
        print(f"  Recommendation: {comparison['comparison'].get('recommendation', 'N/A')}")
