#!/usr/bin/env python3
"""
CrashLens Retry Detection Integration
This script integrates retry loop detection into the existing email categorizer.
"""

import json
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional

class RetryLoopDetector:
    """Detects and manages retry loops based on CrashLens policy."""
    
    def __init__(self, policy_file: str = "crashlens_retry_policy.yaml"):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.policy = self._load_policy(policy_file)
        
    def _load_policy(self, policy_file: str) -> Dict:
        """Load retry detection policy from YAML file."""
        try:
            with open(policy_file, 'r') as f:
                policy = yaml.safe_load(f)
            self.logger.info(f"Loaded retry policy from {policy_file}")
            return policy
        except FileNotFoundError:
            self.logger.error(f"Policy file {policy_file} not found")
            return self._get_default_policy()
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing policy file: {e}")
            return self._get_default_policy()
    
    def _get_default_policy(self) -> Dict:
        """Return default policy if file loading fails."""
        return {
            'global': {'max_violations_per_rule': 10},
            'cost_thresholds': {'critical_threshold': 0.05},
            'budget_limits': {
                'max_retry_cost_per_trace': 0.20,
                'daily_retry_budget': 5.00
            }
        }
    
    def check_retry_violation(self, log_entry: Dict) -> List[Dict]:
        """Check if a log entry violates retry policies."""
        violations = []
        
        retry_count = log_entry.get('metadata', {}).get('retry_count', 0)
        cost = log_entry.get('cost', 0)
        model = log_entry.get('input', {}).get('model', '')
        total_tokens = log_entry.get('usage', {}).get('total_tokens', 0)
        fallback_count = log_entry.get('metadata', {}).get('fallback_count', 0)
        
        # Rule 1: Excessive retry pattern
        if retry_count > 3:
            violations.append({
                'rule_id': 'excessive_retry_pattern',
                'severity': 'critical',
                'message': f'Excessive retries detected: {retry_count}',
                'action': 'fail',
                'suggestion': 'Implement exponential backoff and circuit breaker patterns',
                'trace_id': log_entry.get('traceId', 'unknown')
            })
        
        # Rule 2: Expensive model retries
        expensive_models = ['gpt-4', 'gpt-4-turbo', 'claude-3-opus']
        if model in expensive_models and retry_count > 1:
            violations.append({
                'rule_id': 'expensive_model_retries',
                'severity': 'high',
                'message': f'Expensive model {model} used in retry scenario',
                'action': 'warn',
                'suggestion': 'Use cheaper fallback models for retry scenarios',
                'trace_id': log_entry.get('traceId', 'unknown')
            })
        
        # Rule 3: High cost retry cascade
        if cost > 0.05 and retry_count > 0:
            violations.append({
                'rule_id': 'high_cost_retry_cascade',
                'severity': 'high',
                'message': f'High-cost retry detected: ${cost:.4f}',
                'action': 'warn',
                'suggestion': 'Review error handling and consider model downgrade',
                'trace_id': log_entry.get('traceId', 'unknown')
            })
        
        # Rule 4: Rapid retry detection
        if retry_count > 2 and total_tokens < 200:
            violations.append({
                'rule_id': 'rapid_retry_detection',
                'severity': 'medium',
                'message': f'Rapid retries on short requests: {retry_count} retries',
                'action': 'warn',
                'suggestion': 'Implement proper backoff delays',
                'trace_id': log_entry.get('traceId', 'unknown')
            })
        
        # Rule 5: Fallback chain monitoring
        if fallback_count > 0:
            violations.append({
                'rule_id': 'fallback_chain_monitoring',
                'severity': 'low',
                'message': f'Fallback model used (count: {fallback_count})',
                'action': 'warn',
                'suggestion': 'Monitor if primary model issues are frequent',
                'trace_id': log_entry.get('traceId', 'unknown')
            })
        
        return violations
    
    def should_allow_retry(self, current_retry_count: int, cost_so_far: float, model: str) -> Dict:
        """Determine if retry should be allowed based on policy."""
        result = {
            'allow': True,
            'reason': '',
            'suggested_action': '',
            'fallback_model': None
        }
        
        # Check retry count limit
        if current_retry_count >= 3:
            result['allow'] = False
            result['reason'] = 'Excessive retry attempts'
            result['suggested_action'] = 'Implement circuit breaker pattern'
            return result
        
        # Check cost threshold
        budget_limits = self.policy.get('budget_limits', {})
        max_cost_per_trace = budget_limits.get('max_retry_cost_per_trace', 0.20)
        
        if cost_so_far >= max_cost_per_trace:
            result['allow'] = False
            result['reason'] = f'Cost threshold exceeded: ${cost_so_far:.4f}'
            result['suggested_action'] = 'Stop retries to prevent budget burn'
            return result
        
        # Suggest fallback model for expensive models
        expensive_models = {
            'gpt-4': 'gpt-3.5-turbo',
            'gpt-4-turbo': 'gpt-3.5-turbo',
            'claude-3-opus': 'claude-3-haiku',
            'gemini-2.0-flash': 'gemini-1.5-flash'
        }
        
        if model in expensive_models and current_retry_count > 0:
            result['fallback_model'] = expensive_models[model]
            result['suggested_action'] = f'Consider using fallback model: {result["fallback_model"]}'
        
        return result
    
    def log_retry_attempt(self, trace_id: str, retry_count: int, model: str, cost: float):
        """Log a retry attempt for monitoring."""
        retry_log = {
            'timestamp': datetime.now().isoformat(),
            'trace_id': trace_id,
            'retry_count': retry_count,
            'model': model,
            'cost': cost,
            'type': 'retry_attempt'
        }
        
        self.logger.info(f"Retry attempt logged: {json.dumps(retry_log)}")
        return retry_log

# Integration example for existing email categorizer
def integrate_retry_detection():
    """Example of how to integrate retry detection into existing code."""
    
    detector = RetryLoopDetector()
    
    # Example: Before making an API call with retries
    def classify_email_with_retry_protection(email_content: str, model: str = "gemini-2.0-flash"):
        trace_id = f"classify-{datetime.now().timestamp()}"
        retry_count = 0
        total_cost = 0.0
        
        while retry_count <= 3:  # Max 3 retries
            # Check if retry should be allowed
            retry_decision = detector.should_allow_retry(retry_count, total_cost, model)
            
            if not retry_decision['allow']:
                print(f"❌ Retry blocked: {retry_decision['reason']}")
                print(f"💡 Suggestion: {retry_decision['suggested_action']}")
                break
            
            # Use fallback model if suggested
            current_model = retry_decision.get('fallback_model', model)
            if current_model != model:
                print(f"🔄 Using fallback model: {current_model} instead of {model}")
            
            try:
                # Simulate API call (replace with actual implementation)
                print(f"🔄 Attempting classification with {current_model} (attempt {retry_count + 1})")
                
                # Simulate processing
                import time
                time.sleep(0.1)  # Simulate API delay
                
                # Simulate success/failure
                import random
                if random.random() > 0.3:  # 70% success rate
                    cost = 0.02 if 'gpt-3.5' in current_model else 0.08
                    total_cost += cost
                    
                    # Log successful classification
                    result_log = {
                        'traceId': trace_id,
                        'type': 'email_classification',
                        'startTime': datetime.now().isoformat(),
                        'input': {'model': current_model},
                        'cost': cost,
                        'metadata': {
                            'retry_count': retry_count,
                            'processing_time_ms': 100,
                            'fallback_used': current_model != model
                        }
                    }
                    
                    # Check for violations
                    violations = detector.check_retry_violation(result_log)
                    if violations:
                        print(f"⚠️ Policy violations detected:")
                        for violation in violations:
                            print(f"   [{violation['severity'].upper()}] {violation['message']}")
                    
                    print(f"✅ Classification successful with {current_model}")
                    return result_log
                else:
                    raise Exception("Simulated API failure")
                    
            except Exception as e:
                retry_count += 1
                cost = 0.01  # Cost for failed attempt
                total_cost += cost
                
                # Log retry attempt
                detector.log_retry_attempt(trace_id, retry_count, current_model, cost)
                print(f"❌ Attempt {retry_count} failed: {e}")
                
                if retry_count > 3:
                    print(f"💀 Max retries exceeded for {trace_id}")
                    break
        
        return None
    
    # Test the integration
    print("=== Testing Retry Detection Integration ===")
    result = classify_email_with_retry_protection("Test email content")
    
    if result:
        print(f"Final result: {json.dumps(result, indent=2)}")
    else:
        print("Classification failed after all retries")

if __name__ == "__main__":
    integrate_retry_detection()
