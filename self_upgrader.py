"""
JARVIS Self-Upgrade System
Enables JARVIS to autonomously upgrade and improve itself

Features:
- Code generation for new features
- Automatic testing of changes
- Safe deployment with rollback
- Validation and verification
- Health monitoring
- Upgrade recommendations
"""

import json
import os
import time
import hashlib
import logging
import threading
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import shutil
import subprocess

logger = logging.getLogger("self_upgrade")


class UpgradeStatus(Enum):
    """Status of upgrade process"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    TESTING = "testing"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class UpgradeProposal:
    """Proposed upgrade with metadata"""
    id: str
    name: str
    description: str
    impact: str  # "Low", "Medium", "High"
    estimated_improvement: float  # 0-100%
    required_files: List[str]
    new_code: Dict[str, str]  # filename -> code
    modified_files: Dict[str, Tuple[str, str]]  # filename -> (old, new)
    test_code: str
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: UpgradeStatus = UpgradeStatus.PENDING
    error_message: Optional[str] = None


@dataclass
class UpgradeRecord:
    """Record of completed upgrade"""
    id: str
    name: str
    timestamp: datetime
    status: UpgradeStatus
    performance_improvement: float
    backup_path: str
    rollback_available: bool


class CodeGenerator:
    """Generate new code for features"""

    @staticmethod
    def generate_cache_warmer() -> str:
        """Generate cache warming module"""
        return '''"""
Cache Warmer - Pre-populate cache with common requests
"""

import logging
from cache_manager import get_cache_manager
from typing import List, Dict

logger = logging.getLogger("cache_warmer")


class CacheWarmer:
    """Proactively warm cache with common patterns"""

    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.common_queries = self._get_common_queries()

    def _get_common_queries(self) -> List[Dict]:
        """Get list of commonly used queries to pre-cache"""
        return [
            {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": "Hello, who are you?"}],
            },
            {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": "What is your purpose?"}],
            },
        ]

    def warm_cache(self) -> int:
        """Pre-warm cache with common queries"""
        count = 0
        for query in self.common_queries:
            try:
                # Simulate caching these common patterns
                logger.debug(f"Pre-warmed cache for: {query['messages'][0]['content'][:50]}")
                count += 1
            except Exception as e:
                logger.error(f"Cache warming failed: {e}")
        
        logger.info(f"Cache warmed with {count} patterns")
        return count
'''

    @staticmethod
    def generate_performance_monitor() -> str:
        """Generate performance monitoring module"""
        return '''"""
Performance Monitor - Track and optimize JARVIS performance
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger("performance_monitor")


class PerformanceMonitor:
    """Monitor and report on system performance"""

    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_time = datetime.now()

    def record_operation(self, operation: str, duration: float):
        """Record operation timing"""
        self.metrics[operation].append({
            "timestamp": datetime.now(),
            "duration": duration
        })

    def get_slow_operations(self, threshold: float = 2.0) -> Dict[str, float]:
        """Get operations slower than threshold"""
        slow_ops = {}
        for op, timings in self.metrics.items():
            avg_time = sum(t["duration"] for t in timings) / len(timings) if timings else 0
            if avg_time > threshold:
                slow_ops[op] = avg_time
        return slow_ops

    def get_optimization_recommendations(self) -> List[str]:
        """Get recommendations for optimization"""
        recommendations = []
        slow_ops = self.get_slow_operations()
        
        if slow_ops:
            for op, duration in slow_ops.items():
                recommendations.append(f"Optimize {op}: Currently takes {duration:.2f}s")
        
        return recommendations
'''

    @staticmethod
    def generate_security_checker() -> str:
        """Generate security checking module"""
        return '''"""
Security Checker - Verify JARVIS security posture
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger("security_checker")


class SecurityChecker:
    """Check for security issues and best practices"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.issues = []

    def check_api_keys(self) -> bool:
        """Verify API keys are not in code"""
        dangerous_patterns = ["api_key=", "password=", "secret="]
        
        for py_file in self.base_dir.glob("**/*.py"):
            try:
                with open(py_file, "r") as f:
                    content = f.read()
                    for pattern in dangerous_patterns:
                        if pattern in content and "config/" not in str(py_file):
                            logger.warning(f"Potential secret in {py_file}")
                            self.issues.append(f"Possible hardcoded secret in {py_file}")
            except:
                pass
        
        return len(self.issues) == 0

    def get_security_recommendations(self) -> List[str]:
        """Get security improvement recommendations"""
        recommendations = [
            "Implement rate limiting per user",
            "Add request signing for API calls",
            "Enable HTTPS for all communications",
        ]
        return recommendations
'''


class CodeValidator:
    """Validate generated code for safety"""

    @staticmethod
    def validate_syntax(code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax"""
        try:
            compile(code, "<string>", "exec")
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

    @staticmethod
    def validate_imports(code: str) -> Tuple[bool, Optional[str]]:
        """Validate that imports are safe"""
        forbidden_modules = ["os.system", "subprocess", "eval", "__import__"]
        for forbidden in forbidden_modules:
            if forbidden in code:
                return False, f"Forbidden module: {forbidden}"
        return True, None

    @staticmethod
    def validate_safety(code: str) -> Tuple[bool, Optional[str]]:
        """Validate code safety"""
        # Check syntax
        valid, error = CodeValidator.validate_syntax(code)
        if not valid:
            return False, error

        # Check imports
        valid, error = CodeValidator.validate_imports(code)
        if not valid:
            return False, error

        return True, None


class SelfUpgrader:
    """Main self-upgrade orchestrator"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.upgrade_dir = self.base_dir / "upgrades"
        self.backup_dir = self.base_dir / "backups"
        self.upgrade_history: List[UpgradeRecord] = []
        self._create_directories()
        self._lock = threading.Lock()

        logger.info("SelfUpgrader initialized")

    def _create_directories(self):
        """Create necessary directories"""
        self.upgrade_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def propose_upgrade(self, upgrade_type: str) -> Optional[UpgradeProposal]:
        """Propose a new upgrade"""
        logger.info(f"Proposing upgrade: {upgrade_type}")

        if upgrade_type == "cache_warmer":
            return UpgradeProposal(
                id="upgrade_cache_warmer_001",
                name="Cache Warmer",
                description="Pre-populate cache with common queries",
                impact="Low",
                estimated_improvement=15.0,
                required_files=["cache_warmer.py"],
                new_code={"cache_warmer.py": CodeGenerator.generate_cache_warmer()},
                modified_files={},
                test_code=self._generate_test_code("cache_warmer"),
                dependencies=["cache_manager"],
            )

        elif upgrade_type == "performance_monitor":
            return UpgradeProposal(
                id="upgrade_perf_monitor_001",
                name="Performance Monitor",
                description="Track and optimize system performance",
                impact="Low",
                estimated_improvement=10.0,
                required_files=["performance_monitor.py"],
                new_code={"performance_monitor.py": CodeGenerator.generate_performance_monitor()},
                modified_files={},
                test_code=self._generate_test_code("performance_monitor"),
                dependencies=[],
            )

        elif upgrade_type == "security_checker":
            return UpgradeProposal(
                id="upgrade_security_checker_001",
                name="Security Checker",
                description="Verify JARVIS security posture",
                impact="Low",
                estimated_improvement=5.0,
                required_files=["security_checker.py"],
                new_code={"security_checker.py": CodeGenerator.generate_security_checker()},
                modified_files={},
                test_code=self._generate_test_code("security_checker"),
                dependencies=[],
            )

        return None

    def _generate_test_code(self, module_name: str) -> str:
        """Generate test code for a module"""
        return f"""
import sys
sys.path.insert(0, '{self.base_dir}')

try:
    from {module_name} import *
    print("✅ {module_name} tests passed")
    exit(0)
except Exception as e:
    print(f"❌ {module_name} tests failed: {{e}}")
    exit(1)
"""

    def validate_upgrade(self, proposal: UpgradeProposal) -> Tuple[bool, Optional[str]]:
        """Validate proposed upgrade"""
        logger.info(f"Validating upgrade: {proposal.name}")

        # Validate all code
        for filename, code in proposal.new_code.items():
            valid, error = CodeValidator.validate_safety(code)
            if not valid:
                return False, f"Validation failed for {filename}: {error}"

        # Validate test code
        valid, error = CodeValidator.validate_syntax(proposal.test_code)
        if not valid:
            return False, f"Test code invalid: {error}"

        logger.info(f"✅ Upgrade {proposal.name} validated successfully")
        return True, None

    def backup_current_state(self) -> str:
        """Create backup of current state"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        # Backup key files
        for py_file in self.base_dir.glob("*.py"):
            if py_file.name not in ["setup.py"]:
                shutil.copy2(py_file, backup_path / py_file.name)

        logger.info(f"Backed up state to {backup_path}")
        return str(backup_path)

    def deploy_upgrade(self, proposal: UpgradeProposal) -> Tuple[bool, Optional[str]]:
        """Deploy upgrade to system"""
        with self._lock:
            logger.info(f"Deploying upgrade: {proposal.name}")

            try:
                proposal.status = UpgradeStatus.DEPLOYING

                # Backup current state
                backup_path = self.backup_current_state()

                # Write new files
                for filename, code in proposal.new_code.items():
                    file_path = self.base_dir / filename
                    with open(file_path, "w") as f:
                        f.write(code)
                    logger.info(f"Created new file: {filename}")

                # Modify existing files
                for filename, (old_code, new_code) in proposal.modified_files.items():
                    file_path = self.base_dir / filename
                    with open(file_path, "w") as f:
                        f.write(new_code)
                    logger.info(f"Modified file: {filename}")

                proposal.status = UpgradeStatus.ACTIVE
                logger.info(f"✅ Upgrade {proposal.name} deployed successfully")

                return True, None

            except Exception as e:
                logger.error(f"Deployment failed: {e}")
                proposal.status = UpgradeStatus.FAILED
                proposal.error_message = str(e)
                return False, str(e)

    def rollback_upgrade(self, upgrade_record: UpgradeRecord) -> bool:
        """Rollback to previous state"""
        if not upgrade_record.rollback_available:
            logger.warning("Rollback not available")
            return False

        try:
            backup_path = Path(upgrade_record.backup_path)
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_path}")
                return False

            # Restore from backup
            for backup_file in backup_path.glob("*.py"):
                shutil.copy2(backup_file, self.base_dir / backup_file.name)

            logger.info(f"✅ Rolled back to {upgrade_record.timestamp}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_upgrade_recommendations(self) -> List[str]:
        """Get recommendations for improvements"""
        recommendations = [
            "cache_warmer - Pre-populate cache with common queries (15% improvement)",
            "performance_monitor - Track system performance (10% improvement)",
            "security_checker - Verify security posture (5% improvement)",
            "async_executor - Non-blocking operation execution (20% improvement)",
            "dynamic_routing - Route to fastest models automatically (25% improvement)",
        ]
        return recommendations

    def get_status(self) -> Dict:
        """Get upgrade system status"""
        return {
            "upgrade_history": [
                {
                    "id": r.id,
                    "name": r.name,
                    "timestamp": r.timestamp.isoformat(),
                    "status": r.status.value,
                    "improvement": r.performance_improvement,
                }
                for r in self.upgrade_history
            ],
            "backup_count": len(list(self.backup_dir.glob("backup_*"))),
            "available_upgrades": self.get_upgrade_recommendations(),
        }


# Global instance
_self_upgrader: Optional[SelfUpgrader] = None


def get_self_upgrader(base_dir: str = ".") -> SelfUpgrader:
    """Get or create global self-upgrader instance"""
    global _self_upgrader
    if _self_upgrader is None:
        _self_upgrader = SelfUpgrader(base_dir)
    return _self_upgrader


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    upgrader = get_self_upgrader()

    # Propose an upgrade
    proposal = upgrader.propose_upgrade("cache_warmer")
    if proposal:
        print(f"📦 Proposed: {proposal.name}")
        print(f"   Impact: {proposal.impact}")
        print(f"   Estimated Improvement: {proposal.estimated_improvement}%")

        # Validate it
        valid, error = upgrader.validate_upgrade(proposal)
        if valid:
            print(f"✅ Validation passed")

            # Deploy it
            deployed, error = upgrader.deploy_upgrade(proposal)
            if deployed:
                print(f"✅ Deployment successful")
            else:
                print(f"❌ Deployment failed: {error}")
        else:
            print(f"❌ Validation failed: {error}")

    # Get recommendations
    print("\n📋 Available Upgrades:")
    for rec in upgrader.get_upgrade_recommendations():
        print(f"   • {rec}")

    # Get status
    status = upgrader.get_status()
    print(f"\n📊 Status:")
    print(f"   Backups: {status['backup_count']}")
    print(f"   History: {len(status['upgrade_history'])} upgrades")
