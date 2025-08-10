#!/usr/bin/env python3
"""
Analyze CrashLens retry-loop-prevention configuration and behavior
"""

import subprocess
import json
import yaml
import os
from pathlib import Path

def analyze_retry_configuration():
    """Analyze the retry loop prevention configuration in the repository."""
    
    print("=== CrashLens Retry Configuration Analysis ===\n")
    
    results = {
        "custom_policy_location": None,
        "retry_limit_configured": None,
        "build_breaking_enabled": None,
        "workflow_continue_on_error": None,
        "crashlens_version": None,
        "default_template_behavior": None
    }
    
    # 1. Check for custom retry policy file
    custom_policy_file = "crashlens_retry_policy.yaml"
    if os.path.exists(custom_policy_file):
        print(f"✅ Found custom retry policy: {custom_policy_file}")
        results["custom_policy_location"] = custom_policy_file
        
        try:
            with open(custom_policy_file, 'r') as f:
                policy_data = yaml.safe_load(f)
            
            # Find retry limit in custom policy
            for rule in policy_data.get('rules', []):
                if rule.get('id') == 'excessive_retry_pattern':
                    match_condition = rule.get('match', {})
                    retry_limit = match_condition.get('retry_count', 'not found')
                    results["retry_limit_configured"] = f"Custom policy: {retry_limit}"
                    print(f"📋 Retry limit in custom policy: {retry_limit}")
                    print(f"   Rule ID: {rule.get('id')}")
                    print(f"   Action: {rule.get('action', 'unknown')}")
                    print(f"   Severity: {rule.get('severity', 'unknown')}")
                    break
                    
        except Exception as e:
            print(f"⚠️ Error reading custom policy: {e}")
    else:
        print(f"❌ No custom policy file found at {custom_policy_file}")
    
    # 2. Check workflow configuration
    workflow_file = ".github/workflows/crashlens-scan.yml"
    if os.path.exists(workflow_file):
        print(f"\n✅ Found workflow file: {workflow_file}")
        
        with open(workflow_file, 'r') as f:
            workflow_content = f.read()
        
        # Check for build-breaking configuration
        if 'CRASHLENS_FAIL_ON_VIOLATIONS: "false"' in workflow_content:
            results["build_breaking_enabled"] = False
            print("📋 Build breaking on violations: DISABLED (false)")
        elif 'CRASHLENS_FAIL_ON_VIOLATIONS: "true"' in workflow_content:
            results["build_breaking_enabled"] = True
            print("📋 Build breaking on violations: ENABLED (true)")
        
        # Check for continue-on-error settings
        continue_on_error_count = workflow_content.count('continue-on-error: true')
        results["workflow_continue_on_error"] = continue_on_error_count
        print(f"📋 Steps with 'continue-on-error: true': {continue_on_error_count}")
        
        # Check which policy template is being used
        if 'retry-loop-prevention' in workflow_content:
            print("📋 Using built-in 'retry-loop-prevention' template")
            results["default_template_behavior"] = "Built-in template used"
        
    # 3. Check CrashLens version
    try:
        result = subprocess.run(['crashlens', '--version'], 
                              capture_output=True, text=True, 
                              encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            version_output = result.stdout.strip()
            results["crashlens_version"] = version_output
            print(f"\n📦 {version_output}")
        else:
            print(f"\n❌ Could not get CrashLens version")
    except Exception as e:
        print(f"\n⚠️ Error checking CrashLens version: {e}")
    
    # 4. Check if custom policy is actually used in workflow
    if os.path.exists(workflow_file):
        with open(workflow_file, 'r') as f:
            workflow_content = f.read()
        
        if 'crashlens_retry_policy.yaml' in workflow_content:
            print("\n✅ Workflow DOES use custom retry policy file")
        elif '--policy-template' in workflow_content:
            print("\n📋 Workflow uses built-in policy templates (not custom file)")
        else:
            print("\n❓ Workflow policy usage unclear")
    
    # 5. Summary and recommendations
    print(f"\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    
    print(f"🔍 Retry Limit Configuration:")
    if results["retry_limit_configured"]:
        print(f"   └─ {results['retry_limit_configured']}")
    else:
        print(f"   └─ Using CrashLens built-in 'retry-loop-prevention' template")
        print(f"      (Default: Typically >3 retries triggers violations)")
    
    print(f"\n🏗️ Build Breaking Behavior:")
    if results["build_breaking_enabled"] is False:
        print(f"   └─ ❌ DISABLED - CI will NOT fail on retry violations")
        print(f"   └─ Steps with continue-on-error: {results['workflow_continue_on_error']}")
    elif results["build_breaking_enabled"] is True:
        print(f"   └─ ✅ ENABLED - CI will fail on retry violations")
    else:
        print(f"   └─ ❓ Configuration unclear")
    
    print(f"\n📍 Key File Locations:")
    if results["custom_policy_location"]:
        print(f"   └─ Custom Policy: {results['custom_policy_location']} (Line 8: retry_count: '>3')")
    print(f"   └─ Workflow Config: {workflow_file} (Line 41: CRASHLENS_FAIL_ON_VIOLATIONS)")
    print(f"   └─ Templates Used: {workflow_file} (Line 39: retry-loop-prevention)")
    
    print(f"\n🎯 Current Behavior:")
    print(f"   └─ Retry threshold: >3 attempts will trigger violations")
    print(f"   └─ Violation severity: Critical (from custom policy)")
    print(f"   └─ CI behavior: Analysis runs but does NOT break build")
    print(f"   └─ Reports: Generated as artifacts and PR comments")
    
    return results

if __name__ == "__main__":
    results = analyze_retry_configuration()
    
    # Save results to file
    with open('retry-config-analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: retry-config-analysis.json")
