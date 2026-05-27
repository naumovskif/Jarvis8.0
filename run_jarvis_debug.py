#!/usr/bin/env python
"""Run JARVIS with full error reporting"""

import sys
import traceback
import io

# Force unbuffered output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

try:
    print("[DEBUG] Starting JARVIS...", flush=True)
    from main import main
    print("[DEBUG] main.py imported successfully", flush=True)
    
    main()
    
except KeyboardInterrupt:
    print("\n[SHUTDOWN] User interrupted", flush=True)
    sys.exit(0)
    
except Exception as e:
    print("\n" + "="*70, flush=True)
    print("[CRASH] JARVIS crashed during execution:", flush=True)
    print("="*70, flush=True)
    traceback.print_exc()
    sys.stderr.flush()
    print("="*70, flush=True)
    print(f"\nError Type: {type(e).__name__}", flush=True)
    print(f"Error Message: {str(e)}", flush=True)
    print("\nPlease share this output with the developer.", flush=True)
    print("="*70, flush=True)
    sys.exit(1)
