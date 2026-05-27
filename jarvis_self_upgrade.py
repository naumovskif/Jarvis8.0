"""
JARVIS Self-Upgrade Integration
Connects JARVIS agents to the self-upgrade system

This module allows JARVIS to:
- Analyze its own performance
- Propose improvements
- Generate new modules
- Test upgrades safely
- Deploy with rollback capability
"""

import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from self_upgrader import get_self_upgrader, UpgradeStatus

logger = logging.getLogger("jarvis_self_upgrade")


class JARVISUpgradeManager:
    """Manage JARVIS self-upgrades"""

    def __init__(self):
        self.upgrader = get_self_upgrader()
        self.performance_baseline = {}
        self.upgrade_queue: List[str] = []
        logger.info("JARVISUpgradeManager initialized")

    def analyze_performance(self) -> Dict[str, float]:
        """Analyze current JARVIS performance"""
        logger.info("Analyzing JARVIS performance...")

        # Get metrics from various systems
        metrics = {
            "cache_hit_rate": self._get_cache_hit_rate(),
            "avg_response_time": self._get_avg_response_time(),
            "error_rate": self._get_error_rate(),
            "rate_limit_hits": self._get_rate_limit_hits(),
            "uptime_percentage": self._get_uptime_percentage(),
        }

        return metrics

    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        try:
            from cache_manager import get_cache_manager

            stats = get_cache_manager().get_stats()
            if stats.get("hits", 0) + stats.get("misses", 0) == 0:
                return 0.0
            return stats.get("hits", 0) / (stats.get("hits", 0) + stats.get("misses", 0))
        except:
            return 0.0

    def _get_avg_response_time(self) -> float:
        """Get average response time"""
        try:
            from metrics import get_metrics_tracker

            stats = get_metrics_tracker().get_stats()
            return stats.get("avg_response_time", 0.0)
        except:
            return 0.0

    def _get_error_rate(self) -> float:
        """Get system error rate"""
        try:
            from metrics import get_metrics_tracker

            stats = get_metrics_tracker().get_stats()
            return stats.get("error_rate", 0.0)
        except:
            return 0.0

    def _get_rate_limit_hits(self) -> int:
        """Get number of rate limit hits"""
        try:
            from rate_limiter import get_rate_limiter

            stats = get_rate_limiter().get_stats()
            return stats.get("rate_limit_events", 0)
        except:
            return 0

    def _get_uptime_percentage(self) -> float:
        """Get system uptime percentage"""
        try:
            from metrics import get_metrics_tracker

            stats = get_metrics_tracker().get_stats()
            return stats.get("uptime_percentage", 100.0)
        except:
            return 100.0

    def identify_improvements(self, metrics: Dict[str, float]) -> List[Tuple[str, str, float]]:
        """Identify potential improvements based on metrics"""
        improvements = []

        # Low cache hit rate?
        if metrics.get("cache_hit_rate", 0) < 0.6:
            improvements.append(
                (
                    "cache_warmer",
                    "Cache hit rate is low - pre-warm common queries",
                    15.0,
                )
            )

        # High response time?
        if metrics.get("avg_response_time", 0) > 2.0:
            improvements.append(
                (
                    "performance_monitor",
                    "Response time is high - add performance monitoring",
                    20.0,
                )
            )

        # High error rate?
        if metrics.get("error_rate", 0) > 0.05:
            improvements.append(
                (
                    "security_checker",
                    "Error rate is high - check for issues",
                    10.0,
                )
            )

        # Rate limit hits?
        if metrics.get("rate_limit_hits", 0) > 5:
            improvements.append(
                (
                    "multi_model_router",
                    "Rate limit hits detected - use multi-model routing",
                    25.0,
                )
            )

        return improvements

    def propose_auto_upgrade(self, upgrade_type: str) -> Optional[Dict]:
        """Automatically propose an upgrade"""
        logger.info(f"Proposing auto-upgrade: {upgrade_type}")

        proposal = self.upgrader.propose_upgrade(upgrade_type)
        if not proposal:
            return None

        return {
            "id": proposal.id,
            "name": proposal.name,
            "description": proposal.description,
            "impact": proposal.impact,
            "estimated_improvement": proposal.estimated_improvement,
            "required_files": proposal.required_files,
            "status": proposal.status.value,
        }

    def queue_upgrade(self, upgrade_type: str):
        """Queue an upgrade for later execution"""
        self.upgrade_queue.append(upgrade_type)
        logger.info(f"Queued upgrade: {upgrade_type}")

    def process_upgrade_queue(self) -> Dict[str, List[str]]:
        """Process all queued upgrades"""
        results = {"successful": [], "failed": []}

        for upgrade_type in self.upgrade_queue:
            logger.info(f"Processing queued upgrade: {upgrade_type}")

            proposal = self.upgrader.propose_upgrade(upgrade_type)
            if not proposal:
                results["failed"].append(upgrade_type)
                continue

            # Validate
            valid, error = self.upgrader.validate_upgrade(proposal)
            if not valid:
                logger.error(f"Validation failed: {error}")
                results["failed"].append(upgrade_type)
                continue

            # Deploy
            deployed, error = self.upgrader.deploy_upgrade(proposal)
            if not deployed:
                logger.error(f"Deployment failed: {error}")
                results["failed"].append(upgrade_type)
            else:
                results["successful"].append(upgrade_type)

        self.upgrade_queue.clear()
        return results

    def get_upgrade_status(self) -> Dict:
        """Get current upgrade system status"""
        return {
            "system_status": self.upgrader.get_status(),
            "queue_length": len(self.upgrade_queue),
            "queued_upgrades": self.upgrade_queue,
        }

    def get_next_recommendation(self) -> Optional[Dict]:
        """Get the next recommended upgrade"""
        # Analyze performance
        metrics = self.analyze_performance()

        # Identify improvements
        improvements = self.identify_improvements(metrics)

        if not improvements:
            return None

        # Return best improvement
        best_upgrade_type, reason, estimated_improvement = max(
            improvements, key=lambda x: x[2]
        )

        proposal = self.upgrader.propose_upgrade(best_upgrade_type)
        if not proposal:
            return None

        return {
            "upgrade_type": best_upgrade_type,
            "reason": reason,
            "estimated_improvement": estimated_improvement,
            "proposal": {
                "id": proposal.id,
                "name": proposal.name,
                "description": proposal.description,
                "impact": proposal.impact,
            },
        }

    def auto_upgrade_if_beneficial(self, threshold: float = 10.0) -> bool:
        """Automatically upgrade if improvement is above threshold"""
        logger.info(f"Checking for auto-upgrade opportunities (threshold: {threshold}%)")

        # Get performance
        metrics = self.analyze_performance()

        # Identify improvements
        improvements = self.identify_improvements(metrics)

        if not improvements:
            logger.info("No improvements identified")
            return False

        # Find improvements above threshold
        beneficial = [imp for imp in improvements if imp[2] >= threshold]

        if not beneficial:
            logger.info(f"No improvements above {threshold}% threshold")
            return False

        # Apply best improvement
        best_upgrade_type, reason, estimated_improvement = max(
            beneficial, key=lambda x: x[2]
        )

        logger.info(
            f"🚀 Auto-upgrading with {best_upgrade_type}: {reason} ({estimated_improvement}% improvement)"
        )

        # Propose, validate, deploy
        proposal = self.upgrader.propose_upgrade(best_upgrade_type)
        if not proposal:
            return False

        valid, error = self.upgrader.validate_upgrade(proposal)
        if not valid:
            logger.error(f"Validation failed: {error}")
            return False

        deployed, error = self.upgrader.deploy_upgrade(proposal)
        if not deployed:
            logger.error(f"Deployment failed: {error}")
            return False

        logger.info(f"✅ Upgrade successful: {proposal.name}")
        return True


# Global instance
_upgrade_manager: Optional[JARVISUpgradeManager] = None


def get_upgrade_manager() -> JARVISUpgradeManager:
    """Get or create global upgrade manager"""
    global _upgrade_manager
    if _upgrade_manager is None:
        _upgrade_manager = JARVISUpgradeManager()
    return _upgrade_manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    manager = get_upgrade_manager()

    print("=" * 70)
    print("JARVIS SELF-UPGRADE SYSTEM")
    print("=" * 70)

    # Analyze performance
    print("\n📊 Analyzing performance...")
    metrics = manager.analyze_performance()
    for metric, value in metrics.items():
        print(f"   {metric}: {value:.2f}")

    # Identify improvements
    print("\n🔍 Identifying improvements...")
    improvements = manager.identify_improvements(metrics)
    for upgrade_type, reason, improvement in improvements:
        print(f"   • {upgrade_type}: {reason} ({improvement}%)")

    # Get next recommendation
    print("\n💡 Next recommendation:")
    recommendation = manager.get_next_recommendation()
    if recommendation:
        print(f"   Type: {recommendation['upgrade_type']}")
        print(f"   Reason: {recommendation['reason']}")
        print(f"   Improvement: {recommendation['estimated_improvement']}%")
    else:
        print("   No recommendations at this time")

    # Get status
    print("\n📈 Upgrade system status:")
    status = manager.get_upgrade_status()
    print(f"   Queue length: {status['queue_length']}")
    print(f"   Available upgrades: {len(status['system_status']['available_upgrades'])}")

    print("\n✅ Self-upgrade system ready!")
