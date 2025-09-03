#!/usr/bin/env python3
"""
Validation script for the vosk-api build system
Tests various build options and configurations
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test(name, cmd, expect_success=True):
    """Run a test command and report results"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if expect_success:
            if result.returncode == 0:
                print(f"✅ PASS: {name}")
                return True
            else:
                print(f"❌ FAIL: {name}")
                print(f"Exit code: {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr[:500]}")
                return False
        else:
            if result.returncode != 0:
                print(f"✅ PASS: {name} (expected failure)")
                return True
            else:
                print(f"❌ FAIL: {name} (expected failure but succeeded)")
                return False
                
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {name}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {name} - {str(e)}")
        return False

def main():
    """Run validation tests"""
    repo_root = Path(__file__).parent.absolute()
    build_script = repo_root / "build.py"
    
    if not build_script.exists():
        print(f"❌ Build script not found: {build_script}")
        sys.exit(1)
    
    os.chdir(repo_root)
    
    print("🧪 Starting vosk-api build system validation...")
    
    tests = [
        # Help and version tests
        ("Help message", "python3 build.py --help", True),
        ("Shell script help", "./build.sh help", True),
        
        # Dependency checking
        ("Dependency check", "python3 build.py --force --bindings-only --no-python", True),
        
        # Configuration tests  
        ("Debug config", "python3 build.py --force --bindings-only --no-python --config Debug", True),
        ("Release config", "python3 build.py --force --bindings-only --no-python --config Release", True),
        
        # Error handling tests
        ("Invalid config", "python3 build.py --config InvalidConfig", False),
        ("Invalid math lib", "python3 build.py --math-lib invalid", False),
        
        # Clean test
        ("Clean build dir", "python3 build.py --clean --force --bindings-only --no-python", True),
    ]
    
    # Run Python binding test only if no Kaldi issues
    try:
        # Quick check if we can at least try to build Python bindings
        result = subprocess.run(
            "python3 build.py --force --bindings-only --python --verbose", 
            shell=True, capture_output=True, text=True, timeout=120
        )
        if "cffi" in result.stdout.lower():
            tests.append(("Python bindings setup", "python3 build.py --force --bindings-only --python", True))
    except:
        pass
    
    passed = 0
    total = len(tests)
    
    for name, cmd, expect_success in tests:
        if run_test(name, cmd, expect_success):
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} tests failed")
        sys.exit(1)

if __name__ == '__main__':
    main()