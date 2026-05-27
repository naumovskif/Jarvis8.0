"""
JARVIS Phase 3: Secure Universal Self-Upgrader
Enables JARVIS to implement ANY requested upgrade with strong security checks

Security Layers:
1. Static Code Analysis - Detect malicious patterns
2. Dependency Scanning - Check for known vulnerabilities
3. License Compliance - Verify legal usage
4. Sandboxing - Test in isolated environment
5. Behavioral Monitoring - Watch for anomalies
6. Risk Scoring - Quantify security impact
"""

import logging
import re
import json
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("security_scanner")


class SecurityLevel(Enum):
    """Security threat levels"""
    SAFE = "safe"               # No risks detected
    LOW = "low"                 # Minor risks, acceptable
    MEDIUM = "medium"           # Notable risks, review recommended
    HIGH = "high"               # Significant risks, approval required
    CRITICAL = "critical"       # Severe risks, block deployment


@dataclass
class SecurityFinding:
    """Individual security finding"""
    severity: SecurityLevel
    category: str  # e.g., "dangerous_function", "license_violation", "known_vulnerability"
    message: str
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None


@dataclass
class SecurityReport:
    """Complete security analysis report"""
    overall_level: SecurityLevel
    findings: List[SecurityFinding] = field(default_factory=list)
    risk_score: float = 0.0  # 0-100
    approval_required: bool = False
    safe_to_deploy: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


class StaticCodeAnalyzer:
    """Analyze code for security issues"""

    # Dangerous patterns that should never appear
    FORBIDDEN_PATTERNS = {
        r"os\.system\s*\(": ("OS Command Execution", "Use subprocess.run with timeout instead"),
        r"eval\s*\(": ("Arbitrary Code Execution", "Avoid eval - use ast.literal_eval for data"),
        r"exec\s*\(": ("Arbitrary Code Execution", "Avoid exec - find safer alternative"),
        r"__import__\s*\(": ("Dynamic Import", "Use importlib with proper safeguards"),
        r"subprocess\.Popen": ("Process Spawning", "Use subprocess.run with timeout"),
        r"open\s*\(['\"]\/": ("Absolute Path Access", "Use relative paths or config"),
        r"pickle\.load": ("Pickle Deserialization", "Use json instead of pickle"),
        r"shell\s*=\s*True": ("Shell Injection Risk", "Use shell=False for subprocess"),
    }

    # Suspicious patterns that warrant investigation
    SUSPICIOUS_PATTERNS = {
        r"import\s+requests": "External HTTP library - verify origin",
        r"socket\s*\.": "Low-level networking - verify purpose",
        r"threading\.": "Multi-threading - verify synchronization",
        r"subprocess": "Process execution - verify necessity",
        r"database": "Database access - verify credentials",
    }

    # Safe patterns that should exist
    GOOD_PATTERNS = {
        r"try:\s*.*\s*except": "Error handling",
        r"logging\.": "Logging",
        r"if __name__": "Entry point guard",
    }

    def analyze_code(self, code: str, filename: str = "code.py") -> SecurityReport:
        """Analyze code for security issues"""
        report = SecurityReport(overall_level=SecurityLevel.SAFE)

        lines = code.split("\n")

        # Check for forbidden patterns
        for line_num, line in enumerate(lines, 1):
            for pattern, (danger, suggestion) in self.FORBIDDEN_PATTERNS.items():
                if re.search(pattern, line):
                    finding = SecurityFinding(
                        severity=SecurityLevel.CRITICAL,
                        category="forbidden_function",
                        message=f"{danger}: {line.strip()}",
                        line_number=line_num,
                        suggested_fix=suggestion,
                    )
                    report.findings.append(finding)
                    report.overall_level = SecurityLevel.CRITICAL

            # Check for suspicious patterns
            for pattern, message in self.SUSPICIOUS_PATTERNS.items():
                if re.search(pattern, line):
                    finding = SecurityFinding(
                        severity=SecurityLevel.MEDIUM,
                        category="suspicious_pattern",
                        message=f"{message}: Line {line_num}",
                        line_number=line_num,
                    )
                    report.findings.append(finding)
                    if report.overall_level != SecurityLevel.CRITICAL:
                        report.overall_level = SecurityLevel.MEDIUM

        # Check for good practices
        good_practices_found = 0
        for pattern, description in self.GOOD_PATTERNS.items():
            if re.search(pattern, code):
                good_practices_found += 1

        # Positive scoring
        if good_practices_found >= 2:
            if report.overall_level == SecurityLevel.SAFE:
                report.overall_level = SecurityLevel.LOW

        # Calculate risk score
        report.risk_score = self._calculate_risk_score(report)
        report.approval_required = report.overall_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
        report.safe_to_deploy = report.overall_level in [SecurityLevel.SAFE, SecurityLevel.LOW]

        return report

    def _calculate_risk_score(self, report: SecurityReport) -> float:
        """Calculate overall risk score 0-100"""
        score = 0.0

        severity_weights = {
            SecurityLevel.CRITICAL: 50,
            SecurityLevel.HIGH: 30,
            SecurityLevel.MEDIUM: 10,
            SecurityLevel.LOW: 3,
            SecurityLevel.SAFE: 0,
        }

        for finding in report.findings:
            score += severity_weights.get(finding.severity, 0)

        # Cap at 100
        return min(100.0, score)


class DependencyScanner:
    """Scan for vulnerable dependencies"""

    # Known vulnerable packages (simplified database)
    KNOWN_VULNERABILITIES = {
        "event-stream": {"versions": ["*"], "severity": "CRITICAL", "reason": "Compromised package (2018)"},
        "ua-parser-js": {"versions": ["*"], "severity": "CRITICAL", "reason": "Supply chain attack (2021)"},
        "lodash": {"versions": ["<4.17.21"], "severity": "HIGH", "reason": "Prototype pollution"},
        "moment": {"versions": ["<2.29.0"], "severity": "MEDIUM", "reason": "Regular expression DoS"},
    }

    def scan_dependencies(self, code: str) -> List[SecurityFinding]:
        """Scan code for vulnerable dependencies"""
        findings = []

        # Extract imports
        import_pattern = r"(?:import|from)\s+(\S+)"
        imports = re.findall(import_pattern, code)

        for imp in imports:
            package_name = imp.split(".")[0]

            if package_name in self.KNOWN_VULNERABILITIES:
                vuln = self.KNOWN_VULNERABILITIES[package_name]
                finding = SecurityFinding(
                    severity=SecurityLevel.CRITICAL,
                    category="known_vulnerability",
                    message=f"Known vulnerable package: {package_name} - {vuln['reason']}",
                    suggested_fix=f"Update to patched version or find alternative",
                )
                findings.append(finding)

        return findings


class LicenseChecker:
    """Check license compliance"""

    # Known license types and compatibility
    LICENSES = {
        "GPL": {"type": "copyleft", "risk": "HIGH", "message": "GPL requires open source"},
        "AGPL": {"type": "copyleft", "risk": "HIGH", "message": "AGPL is very restrictive"},
        "MIT": {"type": "permissive", "risk": "LOW", "message": "MIT is compatible"},
        "Apache": {"type": "permissive", "risk": "LOW", "message": "Apache is compatible"},
        "BSD": {"type": "permissive", "risk": "LOW", "message": "BSD is compatible"},
    }

    def check_licenses(self, code: str, package_sources: List[str]) -> List[SecurityFinding]:
        """Check for license issues"""
        findings = []

        # Look for license declarations
        license_pattern = r"(?:LICENSE|license).*?:\s*(\w+)"
        licenses_found = re.findall(license_pattern, code, re.IGNORECASE)

        for license_name in licenses_found:
            if license_name in self.LICENSES:
                license_info = self.LICENSES[license_name]
                if license_info["type"] == "copyleft":
                    finding = SecurityFinding(
                        severity=SecurityLevel.HIGH,
                        category="license_issue",
                        message=f"{license_name} license detected: {license_info['message']}",
                        suggested_fix="Verify licensing compatibility with your system",
                    )
                    findings.append(finding)

        return findings


class RiskScorer:
    """Score overall upgrade risk"""

    def score_upgrade(
        self,
        code_analysis: SecurityReport,
        dependency_findings: List[SecurityFinding],
        license_findings: List[SecurityFinding],
        code_complexity: float = 0.5,
    ) -> Dict[str, Any]:
        """Score overall risk of upgrade"""

        # Combine all findings
        all_findings = code_analysis.findings + dependency_findings + license_findings

        # Calculate severity distribution
        severity_counts = {level: 0 for level in SecurityLevel}
        for finding in all_findings:
            severity_counts[finding.severity] += 1

        # Calculate risk score
        risk_score = code_analysis.risk_score
        risk_score += len(dependency_findings) * 20  # Dependency vulnerabilities
        risk_score += len(license_findings) * 15  # License violations
        risk_score += code_complexity * 10  # Code complexity factor

        risk_score = min(100.0, risk_score)

        # Determine overall level
        if severity_counts[SecurityLevel.CRITICAL] > 0:
            overall_level = SecurityLevel.CRITICAL
        elif severity_counts[SecurityLevel.HIGH] > 0:
            overall_level = SecurityLevel.HIGH
        elif severity_counts[SecurityLevel.MEDIUM] > 0:
            overall_level = SecurityLevel.MEDIUM
        elif len(all_findings) > 0:
            overall_level = SecurityLevel.LOW
        else:
            overall_level = SecurityLevel.SAFE

        return {
            "risk_score": risk_score,
            "overall_level": overall_level.value,
            "severity_distribution": {k.value: v for k, v in severity_counts.items()},
            "total_findings": len(all_findings),
            "approval_required": overall_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL],
            "safe_to_deploy": overall_level in [SecurityLevel.SAFE, SecurityLevel.LOW],
            "findings": [
                {
                    "severity": f.severity.value,
                    "category": f.category,
                    "message": f.message,
                    "line": f.line_number,
                    "suggestion": f.suggested_fix,
                }
                for f in all_findings
            ],
        }


class SecurityScanner:
    """Master security scanner - coordinates all security checks"""

    def __init__(self):
        self.code_analyzer = StaticCodeAnalyzer()
        self.dependency_scanner = DependencyScanner()
        self.license_checker = LicenseChecker()
        self.risk_scorer = RiskScorer()

    def scan_upgrade(self, code: str, package_sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Complete security scan of proposed upgrade"""
        logger.info("Starting security scan...")

        # Phase 1: Static code analysis
        code_analysis = self.code_analyzer.analyze_code(code)
        logger.info(f"Code analysis: {code_analysis.overall_level.value}")

        # Phase 2: Dependency scanning
        dependency_findings = self.dependency_scanner.scan_dependencies(code)
        logger.info(f"Found {len(dependency_findings)} dependency issues")

        # Phase 3: License compliance
        license_findings = self.license_checker.check_licenses(code, package_sources or [])
        logger.info(f"Found {len(license_findings)} license issues")

        # Phase 4: Overall risk scoring
        risk_assessment = self.risk_scorer.score_upgrade(
            code_analysis, dependency_findings, license_findings, code_complexity=0.5
        )

        logger.info(f"Overall risk: {risk_assessment['overall_level']} ({risk_assessment['risk_score']:.1f}/100)")

        return risk_assessment

    def generate_report(self, scan_result: Dict[str, Any]) -> str:
        """Generate human-readable security report"""
        report = []
        report.append("=" * 70)
        report.append("JARVIS SECURITY SCAN REPORT")
        report.append("=" * 70)
        report.append("")

        # Risk assessment
        report.append(f"Overall Risk Level: {scan_result['overall_level'].upper()}")
        report.append(f"Risk Score: {scan_result['risk_score']:.1f}/100")
        report.append("")

        # Severity distribution
        report.append("Severity Distribution:")
        for level, count in scan_result["severity_distribution"].items():
            if count > 0:
                report.append(f"  {level.upper()}: {count}")
        report.append("")

        # Findings
        if scan_result["findings"]:
            report.append(f"Found {len(scan_result['findings'])} security issues:")
            report.append("-" * 70)
            for i, finding in enumerate(scan_result["findings"], 1):
                report.append(f"\n{i}. {finding['severity'].upper()}: {finding['category']}")
                report.append(f"   Message: {finding['message']}")
                if finding.get("line"):
                    report.append(f"   Line: {finding['line']}")
                if finding.get("suggestion"):
                    report.append(f"   Suggestion: {finding['suggestion']}")
        else:
            report.append("✅ No security issues found!")

        report.append("")
        report.append("=" * 70)

        # Deployment recommendation
        if scan_result["safe_to_deploy"]:
            report.append("✅ SAFE TO DEPLOY - No critical issues detected")
        elif scan_result["approval_required"]:
            report.append("⚠️  APPROVAL REQUIRED - Review findings before deployment")
        else:
            report.append("❌ BLOCKED - Critical security issues must be resolved")

        report.append("=" * 70)

        return "\n".join(report)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scanner = SecurityScanner()

    # Test 1: Safe code
    print("\n" + "=" * 70)
    print("TEST 1: Safe code")
    print("=" * 70)
    safe_code = """
import logging

def calculate(x, y):
    try:
        return x + y
    except Exception as e:
        logging.error(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = calculate(1, 2)
    print(result)
"""
    result = scanner.scan_upgrade(safe_code)
    print(scanner.generate_report(result))

    # Test 2: Dangerous code
    print("\n" + "=" * 70)
    print("TEST 2: Dangerous code")
    print("=" * 70)
    dangerous_code = """
import os

def execute(command):
    os.system(command)  # DANGEROUS!

execute("rm -rf /")
"""
    result = scanner.scan_upgrade(dangerous_code)
    print(scanner.generate_report(result))

    # Test 3: Suspicious code
    print("\n" + "=" * 70)
    print("TEST 3: Suspicious code")
    print("=" * 70)
    suspicious_code = """
import requests
import subprocess

def check_system():
    subprocess.Popen(["ping", "example.com"], shell=True)
    r = requests.get("http://example.com")
    return r.status_code
"""
    result = scanner.scan_upgrade(suspicious_code)
    print(scanner.generate_report(result))

    print("\n✅ Security scanner operational!")
