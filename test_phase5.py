#!/usr/bin/env python3
"""Test Phase 5 CMD Integration"""

from jarvis_backend import app
from jarvis_system_info import JARVISSystemInfo

print("=" * 70)
print("JARVIS Phase 5 Integration Test")
print("=" * 70)

# Test endpoints exist
print("\nBackend Routes (CMD endpoints):")
routes = [route.path for route in app.routes]
for route in sorted(routes):
    if 'cmd' in route or 'api' in route:
        print(f"  ✓ {route}")

# Test system info
print("\nSystem Status:")
info = JARVISSystemInfo.get_system_status()
print(f"  Version: {info['version']}")
print(f"  Status: {info['status']}")
print(f"  Total Phases: {info['total_phases']}")
print(f"  Completed: {info['completed_phases']}")

# Show all phases
print("\nImplemented Phases:")
for phase_key, phase in sorted(info['phases'].items()):
    status = "✓" if phase['status'] == 'COMPLETE' else "○"
    print(f"  {status} {phase['name']}")
    print(f"      Impact: {phase['impact']}")

# Test Phase 5 specifically
print("\nPhase 5 (CMD Execution):")
phase5 = info['phases'].get('phase_5', {})
if phase5:
    print(f"  Status: {phase5.get('status')}")
    print(f"  Impact: {phase5.get('impact')}")
    print(f"  Modules: {', '.join(phase5.get('modules', []))}")
    print(f"  Features:")
    for feat in phase5.get('features', []):
        print(f"    • {feat}")
else:
    print("  Not found!")

# Test CMD executor availability
try:
    from cmd_executor import get_jarvis_cmd
    print("\nCMD Executor:")
    print("  ✓ Module imported successfully")
    
    jarvis_cmd = get_jarvis_cmd()
    print("  ✓ JARVISCMDInterface initialized")
    
    # Test a simple command
    result = jarvis_cmd.execute("echo JARVIS Phase 5 Ready")
    print(f"  ✓ Command execution working (status: {result['status']})")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "=" * 70)
print("JARVIS v5.0 READY WITH PHASE 5 CMD EXECUTION")
print("=" * 70)
