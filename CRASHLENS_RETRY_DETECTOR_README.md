# CrashLens Retry Loop Detector Implementation

This document describes the implementation of the CrashLens Retry Loop Detector for the AI Email Categorizer Backend.

## 🎯 Overview

The CrashLens Retry Loop Detector is designed to identify and prevent expensive retry patterns in AI model interactions, specifically targeting:

- Excessive retry attempts that indicate poor error handling
- High-cost retry cascades that burn through budget
- Expensive model usage in retry scenarios
- Rapid successive retries without proper backoff
- Fallback model usage patterns

## 📁 Files Added

### Core Configuration Files

1. **`crashlens_retry_policy.yaml`** - Main policy configuration
   - Defines 5 detection rules with severity levels
   - Sets cost thresholds and budget limits
   - Configures global settings

2. **`crashlens_config.yaml`** - Updated main configuration
   - Added retry detection section
   - Model fallback mapping
   - Alert thresholds

### Implementation Files

3. **`crashlens_retry_integration.py`** - Integration class
   - `RetryLoopDetector` class for policy enforcement
   - Integration examples for existing code
   - Real-time retry decision making

4. **`test_retry_detection.py`** - Test suite
   - Creates sample log data with various retry scenarios
   - Tests all policy rules
   - Validates violation detection

### GitHub Actions Integration

5. **`.github/workflows/crashlens-scan.yml`** - Updated workflow
   - Added retry detection analysis step
   - Generates comprehensive reports
   - Uploads analysis artifacts

## 🔍 Detection Rules

### 1. Excessive Retry Pattern (CRITICAL)
- **Trigger**: `retry_count > 3`
- **Action**: Fail build
- **Suggestion**: Implement exponential backoff and circuit breaker patterns

### 2. Expensive Model Retries (HIGH)
- **Trigger**: Expensive models (`gpt-4`, `gpt-4-turbo`, `claude-3-opus`) + `retry_count > 1`
- **Action**: Warn
- **Suggestion**: Use cheaper fallback models for retries

### 3. High Cost Retry Cascade (HIGH)
- **Trigger**: `cost > $0.05` + `retry_count > 0`
- **Action**: Warn
- **Suggestion**: Review error handling and consider model downgrade

### 4. Rapid Retry Detection (MEDIUM)
- **Trigger**: `retry_count > 2` + `total_tokens < 200`
- **Action**: Warn
- **Suggestion**: Implement proper backoff delays

### 5. Fallback Chain Monitoring (LOW)
- **Trigger**: `fallback_count > 0`
- **Action**: Warn
- **Suggestion**: Monitor primary model issues

## 💰 Budget Controls

### Cost Thresholds
- **Warning**: $0.01 per operation
- **Critical**: $0.05 per operation

### Budget Limits
- **Daily retry budget**: $5.00
- **Monthly retry budget**: $100.00
- **Max cost per trace**: $0.20

## 🚀 Usage

### 1. Testing the System

```bash
# Run the test suite
python test_retry_detection.py

# Test integration
python crashlens_retry_integration.py
```

### 2. GitHub Actions

The workflow automatically runs:
- On pushes to `main`/`raj` branches
- On pull requests to `main`
- Daily at 6 AM UTC
- Manual triggers with scan options

### 3. Integration in Code

```python
from crashlens_retry_integration import RetryLoopDetector

# Initialize detector
detector = RetryLoopDetector()

# Check if retry should be allowed
retry_decision = detector.should_allow_retry(
    current_retry_count=retry_count,
    cost_so_far=total_cost,
    model=current_model
)

if not retry_decision['allow']:
    print(f"Retry blocked: {retry_decision['reason']}")
    break

# Check for violations in log entries
violations = detector.check_retry_violation(log_entry)
```

## 📊 Monitoring & Alerts

### Workflow Artifacts
- `retry-analysis-results.json` - Detailed violation report
- Security scan reports
- Performance analysis results
- Log analysis summaries

### PR Comments
Automatic comments on pull requests with:
- Violation counts by severity
- Cost analysis
- Recommendations for fixes

### Log Analysis
The system analyzes existing JSONL logs for:
- Retry patterns
- Cost accumulation
- Model usage efficiency
- Error handling effectiveness

## 🔧 Configuration

### Customizing Policies

Edit `crashlens_retry_policy.yaml` to:
- Adjust retry count limits
- Modify cost thresholds
- Add new detection rules
- Change severity levels

### Model Fallbacks

Configure in `crashlens_config.yaml`:
```yaml
retry_detection:
  fallback_models:
    "gpt-4": "gpt-3.5-turbo"
    "claude-3-opus": "claude-3-haiku"
    "gemini-2.0-flash": "gemini-1.5-flash"
```

## 🎯 Expected Results

### Test Output
```
📊 Analysis Results:
   Total requests: 15
   Retry requests: 4
   High-cost retries: 3
   Policy violations: 10

⚠️ Policy Violations Detected:
   [CRITICAL] excessive_retry_pattern: Excessive retries detected: 5
   [HIGH] expensive_model_retries: Expensive model gpt-4 used in retry scenario
   [HIGH] high_cost_retry_cascade: High-cost retry detected: $0.1500
```

### GitHub Actions
- ✅ Automatic analysis on every push/PR
- 📊 Comprehensive reporting
- 🚨 Build failures on critical violations
- 📈 Historical trend tracking

## 🔄 Next Steps

1. **Deploy**: Commit the files and push to trigger the workflow
2. **Monitor**: Review analysis reports and adjust thresholds
3. **Integrate**: Add retry detection to your existing email classification logic
4. **Optimize**: Use fallback models and implement circuit breakers based on recommendations

The system is now ready to detect and prevent expensive retry loops in your AI email categorizer backend!
