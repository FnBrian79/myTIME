#!/usr/bin/env python3
"""
Test script to verify health endpoints are correctly implemented in all services.
"""
import sys
import os
import importlib.util

def load_module_from_file(module_name, file_path):
    """Dynamically load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def test_health_endpoints():
    print("🏥 Testing Health Endpoints Implementation...\n")
    
    services = [
        ("Foreman", "/home/runner/work/myTIME/myTIME/services/foreman/triage.py", "/health"),
        ("Actor", "/home/runner/work/myTIME/myTIME/services/actor/actor.py", "/health"),
        ("Architect", "/home/runner/work/myTIME/myTIME/services/architect/architect_stream.py", "/health"),
        ("Auditor", "/home/runner/work/myTIME/myTIME/services/auditor/auditor.py", "/health"),
        ("Steward", "/home/runner/work/myTIME/myTIME/services/steward/api.py", "/health"),
    ]
    
    all_passed = True
    
    for service_name, file_path, endpoint in services:
        print(f"Checking {service_name}...")
        
        # Read the file content
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if health endpoint exists
            if '@app.route(\'/health\')' in content or "@app.route('/health')" in content:
                print(f"  ✅ Health endpoint found at {endpoint}")
                
                # Check if it returns proper structure
                if '"status"' in content and '"service"' in content and '"integrity"' in content:
                    print(f"  ✅ Response structure looks correct")
                else:
                    print(f"  ⚠️  Warning: Response might be missing expected fields")
            else:
                print(f"  ❌ Health endpoint NOT found!")
                all_passed = False
        
        except FileNotFoundError:
            print(f"  ❌ Service file not found: {file_path}")
            all_passed = False
        except Exception as e:
            print(f"  ❌ Error checking service: {e}")
            all_passed = False
        
        print()
    
    if all_passed:
        print("✅ All services have health endpoints implemented!")
        return True
    else:
        print("❌ Some services are missing health endpoints.")
        return False

def test_bootstrap_artifacts():
    print("🔍 Testing Bootstrap Artifacts...\n")
    
    checks = [
        ("Bootstrap Script", "/home/runner/work/myTIME/myTIME/run.sh"),
        ("Health Check Script", "/home/runner/work/myTIME/myTIME/check_health.sh"),
        ("Master Key", "/home/runner/work/myTIME/myTIME/config/master.key"),
        ("Settings Config", "/home/runner/work/myTIME/myTIME/config/settings.yaml"),
        ("Learning Repo Vault", "/home/runner/work/myTIME/myTIME/learning_repo/vault"),
        ("Learning Repo Metadata", "/home/runner/work/myTIME/myTIME/learning_repo/metadata"),
        ("Logs Directory", "/home/runner/work/myTIME/myTIME/logs"),
    ]
    
    all_passed = True
    
    for name, path in checks:
        if os.path.exists(path):
            if os.path.isfile(path):
                size = os.path.getsize(path)
                print(f"✅ {name}: {size} bytes")
            else:
                print(f"✅ {name}: exists")
        else:
            print(f"❌ {name}: NOT FOUND")
            all_passed = False
    
    print()
    return all_passed

if __name__ == "__main__":
    print("=" * 60)
    print("myTIME Infrastructure Tests")
    print("=" * 60)
    print()
    
    bootstrap_ok = test_bootstrap_artifacts()
    health_ok = test_health_endpoints()
    
    print("=" * 60)
    if bootstrap_ok and health_ok:
        print("🎉 ALL TESTS PASSED! Infrastructure is ready.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Review the output above.")
        sys.exit(1)
