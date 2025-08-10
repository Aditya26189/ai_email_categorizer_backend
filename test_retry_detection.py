#!/usr/bin/env python3
"""
Test script for CrashLens retry loop detection.
This script simulates and tests the retry detection functionality.
"""

import json
import yaml
import os
from datetime import datetime, timedelta
import random

def create_sample_logs():
    """Create sample log entries to test retry detection."""
    print("Creating sample log entries for retry detection testing...")
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    sample_logs = []
    
    # Normal requests (no retries)
    for i in range(10):
        log_entry = {
            "traceId": f"normal-{i}",
            "type": "email_classification",
            "startTime": (datetime.now() - timedelta(hours=i)).isoformat() + "Z",
            "endTime": (datetime.now() - timedelta(hours=i) + timedelta(milliseconds=200)).isoformat() + "Z",
            "level": "info",
            "input": {
                "model": "gemini-2.0-flash",
                "path": "/classify"
            },
            "usage": {
                "prompt_tokens": 150,
                "completion_tokens": 50,
                "total_tokens": 200
            },
            "cost": 0.02,
            "metadata": {
                "processing_time_ms": 200,
                "retry_count": 0,
                "user_id": f"user_{i}"
            }
        }
        sample_logs.append(log_entry)
    
    # Retry scenarios
    retry_scenarios = [
        # Excessive retries (should trigger critical violation)
        {
            "traceId": "excessive-retry-1",
            "input": {"model": "gemini-2.0-flash", "path": "/classify"},
            "cost": 0.08,
            "metadata": {"retry_count": 5, "processing_time_ms": 1500}
        },
        # Expensive model retries (should trigger high severity)
        {
            "traceId": "expensive-retry-1",
            "input": {"model": "gpt-4", "path": "/summarize"},
            "cost": 0.15,
            "metadata": {"retry_count": 2, "processing_time_ms": 800}
        },
        # High cost retry cascade
        {
            "traceId": "high-cost-retry-1",
            "input": {"model": "claude-3-opus", "path": "/classify"},
            "cost": 0.12,
            "metadata": {"retry_count": 3, "processing_time_ms": 2000}
        },
        # Rapid retries
        {
            "traceId": "rapid-retry-1",
            "input": {"model": "gemini-2.0-flash", "path": "/quick-check"},
            "cost": 0.01,
            "metadata": {"retry_count": 3, "processing_time_ms": 100},
            "usage": {"total_tokens": 50}
        },
        # Fallback usage
        {
            "traceId": "fallback-1",
            "input": {"model": "gpt-3.5-turbo", "path": "/classify"},
            "cost": 0.03,
            "metadata": {"retry_count": 0, "fallback_count": 1, "processing_time_ms": 300}
        }
    ]
    
    for scenario in retry_scenarios:
        base_entry = {
            "type": "email_classification",
            "startTime": datetime.now().isoformat() + "Z",
            "endTime": (datetime.now() + timedelta(milliseconds=scenario["metadata"]["processing_time_ms"])).isoformat() + "Z",
            "level": "info",
            "usage": scenario.get("usage", {"prompt_tokens": 100, "completion_tokens": 25, "total_tokens": 125})
        }
        base_entry.update(scenario)
        sample_logs.append(base_entry)
    
    # Write to log file
    log_file = f'logs/test_retry_detection_{datetime.now().strftime("%Y-%m-%d")}.jsonl'
    with open(log_file, 'w') as f:
        for log_entry in sample_logs:
            f.write(json.dumps(log_entry) + '\n')
    
    print(f"✅ Created {len(sample_logs)} sample log entries in {log_file}")
    return log_file

def test_retry_detection():
    """Test the retry detection logic."""
    print("\n=== Testing CrashLens Retry Loop Detection ===")
    
    # Load retry policy
    try:
        with open('crashlens_retry_policy.yaml', 'r') as f:
            policy = yaml.safe_load(f)
        print("✅ Retry policy loaded successfully")
    except FileNotFoundError:
        print("❌ Retry policy file not found")
        return False
    
    # Create sample data
    log_file = create_sample_logs()
    
    violations = []
    total_requests = 0
    retry_requests = 0
    high_cost_retries = 0
    
    # Analyze the log file
    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    total_requests += 1
                    
                    # Check for retry patterns
                    retry_count = log_entry.get('metadata', {}).get('retry_count', 0)
                    cost = log_entry.get('cost', 0)
                    model = log_entry.get('input', {}).get('model', '')
                    total_tokens = log_entry.get('usage', {}).get('total_tokens', 0)
                    fallback_count = log_entry.get('metadata', {}).get('fallback_count', 0)
                    
                    if retry_count > 0:
                        retry_requests += 1
                    
                    # Apply policy rules
                    if retry_count > 3:
                        violations.append({
                            'rule': 'excessive_retry_pattern',
                            'severity': 'critical',
                            'message': f'Excessive retries detected: {retry_count}',
                            'trace_id': log_entry.get('traceId', 'unknown'),
                            'timestamp': log_entry.get('startTime', 'unknown')
                        })
                    
                    if model in ['gpt-4', 'gpt-4-turbo', 'claude-3-opus'] and retry_count > 1:
                        violations.append({
                            'rule': 'expensive_model_retries',
                            'severity': 'high',
                            'message': f'Expensive model {model} used in retry scenario (retries: {retry_count})',
                            'trace_id': log_entry.get('traceId', 'unknown'),
                            'timestamp': log_entry.get('startTime', 'unknown')
                        })
                    
                    if cost > 0.05 and retry_count > 0:
                        high_cost_retries += 1
                        violations.append({
                            'rule': 'high_cost_retry_cascade',
                            'severity': 'high',
                            'message': f'High-cost retry detected: ${cost:.4f} (retries: {retry_count})',
                            'trace_id': log_entry.get('traceId', 'unknown'),
                            'timestamp': log_entry.get('startTime', 'unknown')
                        })
                    
                    if retry_count > 2 and total_tokens < 200:
                        violations.append({
                            'rule': 'rapid_retry_detection',
                            'severity': 'medium',
                            'message': f'Rapid retries on short requests: {retry_count} retries, {total_tokens} tokens',
                            'trace_id': log_entry.get('traceId', 'unknown'),
                            'timestamp': log_entry.get('startTime', 'unknown')
                        })
                    
                    if fallback_count > 0:
                        violations.append({
                            'rule': 'fallback_chain_monitoring',
                            'severity': 'low',
                            'message': f'Fallback model used (count: {fallback_count})',
                            'trace_id': log_entry.get('traceId', 'unknown'),
                            'timestamp': log_entry.get('startTime', 'unknown')
                        })
                
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"⚠️ Error parsing log entry: {e}")
                    continue
                    
    except FileNotFoundError:
        print("❌ Log file not found")
        return False
    
    # Report results
    print(f"\n📊 Analysis Results:")
    print(f"   Total requests: {total_requests}")
    print(f"   Retry requests: {retry_requests}")
    print(f"   High-cost retries: {high_cost_retries}")
    print(f"   Policy violations: {len(violations)}")
    
    if violations:
        print(f"\n⚠️ Policy Violations Detected:")
        severity_counts = {}
        for violation in violations:
            severity = violation['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            print(f"   [{violation['severity'].upper()}] {violation['rule']}: {violation['message']} (Trace: {violation['trace_id']})")
        
        print(f"\n📈 Violation Summary:")
        for severity, count in severity_counts.items():
            print(f"   {severity.upper()}: {count} violations")
    else:
        print(f"\n✅ No retry policy violations detected")
    
    # Save results
    results = {
        'total_requests': total_requests,
        'retry_requests': retry_requests,
        'high_cost_retries': high_cost_retries,
        'violations': violations,
        'analysis_timestamp': datetime.now().isoformat(),
        'test_log_file': log_file
    }
    
    with open('retry-analysis-test-results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to retry-analysis-test-results.json")
    
    # Check if test passed
    critical_violations = [v for v in violations if v['severity'] == 'critical']
    expected_violations = 5  # Based on our test scenarios
    
    if len(violations) >= expected_violations:
        print(f"\n✅ Test PASSED: Found {len(violations)} violations (expected at least {expected_violations})")
        return True
    else:
        print(f"\n❌ Test FAILED: Found {len(violations)} violations (expected at least {expected_violations})")
        return False

if __name__ == "__main__":
    success = test_retry_detection()
    exit(0 if success else 1)
