# CrashLens Logger Integration

This document explains how to use the CrashLens Logger integration in the AI Email Categorizer Backend for comprehensive API usage tracking and analysis.

## Overview

The CrashLens Logger integration provides structured logging for:
- API requests and responses
- Email classification operations 
- Email summarization operations
- Processing times and token usage
- Error tracking and debugging

## Features

### 1. Structured Logging Format
All logs follow a consistent JSON structure with the following fields:
- `traceId`: Unique identifier for tracking requests
- `type`: Operation type (api_request, email_classification, email_summarization)
- `startTime` / `endTime`: ISO 8601 timestamps with millisecond precision
- `level`: Log level (info, error, warning)
- `input`: Request data and parameters
- `usage`: Token usage statistics (prompt_tokens, completion_tokens, total_tokens)
- `cost`: Associated costs (calculated based on token usage)
- `metadata`: Additional context-specific information
- `name`: Human-readable operation name

### 2. Automatic API Logging
All API endpoints are automatically logged via middleware:
```python
# Automatically captures:
# - HTTP method and endpoint path
# - Request/response data
# - Status codes and errors
# - Processing times
# - User context (when available)
```

### 3. AI Operation Logging
Email processing operations are logged with detailed metrics:
```python
# Email Classification Logging
email_logger.log_email_classification(
    email_subject="Job Application Follow-up",
    email_body="Dear hiring manager...",
    predicted_category="Job Offer",
    confidence=0.95,
    model_used="gemini-2.0-flash",
    processing_time_ms=234,
    user_id="user_123"
)

# Email Summarization Logging
email_logger.log_email_summarization(
    email_body="Long email content...",
    summary_bullets=["Key point 1", "Key point 2"],
    model_used="gemini-ai-summarizer", 
    processing_time_ms=156,
    user_id="user_123"
)
```

## Configuration

### 1. Environment Setup
The logging system is automatically initialized when the app starts. Log files are saved to:
```
logs/
├── api_calls_YYYY-MM-DD.jsonl
├── email_operations_YYYY-MM-DD.jsonl
└── errors_YYYY-MM-DD.jsonl
```

### 2. Log File Rotation
Log files are automatically rotated daily and organized by date for easy analysis.

### 3. Performance Impact
- Minimal overhead: < 2ms per request
- Asynchronous writing to prevent blocking
- Automatic batching for high-volume scenarios

## Usage Examples

### 1. Viewing Recent API Calls
```bash
# View last 10 API calls
tail -n 10 logs/api_calls_$(date +%Y-%m-%d).jsonl | jq .

# Filter by endpoint
grep '"/classify"' logs/api_calls_*.jsonl | jq .
```

### 2. Analyzing Email Processing Performance
```bash
# Average processing time for classifications
cat logs/email_operations_*.jsonl | jq -r 'select(.type=="email_classification") | .metadata.processing_time_ms' | awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'

# Token usage analysis
cat logs/email_operations_*.jsonl | jq -r '.usage.total_tokens' | awk '{sum+=$1; count++} END {print "Total tokens:", sum, "Average per operation:", sum/count}'
```

### 3. Error Analysis
```bash
# View errors from last 24 hours
cat logs/api_calls_$(date +%Y-%m-%d).jsonl | jq 'select(.level=="error")'

# Most common error types
cat logs/api_calls_*.jsonl | jq -r 'select(.level=="error") | .metadata.error' | sort | uniq -c | sort -nr
```

## Log Structure Examples

### API Request Log
```json
{
  "traceId": "req-abc123",
  "type": "api_request",
  "startTime": "2025-01-15T10:30:45.123Z",
  "endTime": "2025-01-15T10:30:45.275Z",
  "level": "info",
  "input": {
    "method": "POST",
    "path": "/classify",
    "request_data": {"email_id": "email_456"}
  },
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "cost": 0.0,
  "metadata": {
    "http_method": "POST",
    "endpoint": "/classify",
    "status_code": 200,
    "processing_time_ms": 152,
    "user_id": "user_789"
  },
  "name": "api_request"
}
```

### Email Classification Log
```json
{
  "traceId": "classify-def456",
  "type": "email_classification",
  "startTime": "2025-01-15T10:30:45.123Z",
  "endTime": "2025-01-15T10:30:45.357Z",
  "level": "info",
  "input": {
    "model": "gemini-2.0-flash",
    "subject": "Job Interview Invitation",
    "body_length": 450
  },
  "usage": {
    "prompt_tokens": 125,
    "completion_tokens": 15,
    "total_tokens": 140
  },
  "cost": 0.000875,
  "metadata": {
    "predicted_category": "Job Offer",
    "confidence": 0.96,
    "processing_time_ms": 234,
    "user_id": "user_789"
  },
  "name": "email_classification"
}
```

### Email Summarization Log
```json
{
  "traceId": "summary-ghi789",
  "type": "email_summarization", 
  "startTime": "2025-01-15T10:30:46.123Z",
  "endTime": "2025-01-15T10:30:46.279Z",
  "level": "info",
  "input": {
    "model": "gemini-ai-summarizer",
    "body_length": 1200
  },
  "usage": {
    "prompt_tokens": 300,
    "completion_tokens": 45,
    "total_tokens": 345
  },
  "cost": 0.002157,
  "metadata": {
    "summary_bullet_count": 4,
    "processing_time_ms": 156,
    "user_id": "user_789",
    "summary_bullets": [
      "Meeting scheduled for Thursday at 2pm",
      "Review quarterly performance metrics", 
      "Discuss budget allocation for Q2",
      "Plan team expansion strategy"
    ]
  },
  "name": "email_summarization"
}
```

## Integration with Analytics Tools

### 1. Data Pipeline
The structured JSONL format can be easily imported into:
- Elasticsearch for search and visualization
- InfluxDB for time-series analysis
- BigQuery for large-scale analytics
- Custom dashboards using the JSON data

### 2. Real-time Monitoring
Set up alerts based on:
```bash
# High error rates
# Processing time thresholds  
# Token usage spikes
# API rate limits
```

### 3. Cost Tracking
Monitor AI costs by:
- Token usage per user
- Model-specific costs
- Daily/monthly spending trends
- Cost per email processed

## Troubleshooting

### 1. Log Files Not Created
- Check directory permissions for `logs/` folder
- Verify Python logging configuration
- Check disk space availability

### 2. Missing Log Entries
- Ensure middleware is properly configured in `main.py`
- Check for exceptions during logging operations
- Verify CrashLens logger initialization

### 3. Performance Issues
- Monitor log file sizes (rotate if > 100MB)
- Consider adjusting log levels for production
- Use asynchronous logging for high-volume scenarios

## Security Considerations

### 1. Data Privacy
- Email subjects are truncated to 100 characters in logs
- Full email bodies are not logged (only length)
- Sensitive data is excluded from metadata

### 2. Log Retention
- Implement log rotation policies
- Consider encrypting log files for compliance
- Set up automated cleanup for old logs

### 3. Access Control
- Restrict access to log directories
- Use secure channels for log transmission
- Implement audit trails for log access

## Performance Metrics

The CrashLens integration provides comprehensive metrics for:

- **Latency Tracking**: Request/response times, AI processing times
- **Throughput Monitoring**: Requests per second, emails processed per hour
- **Resource Usage**: Token consumption, memory utilization
- **Error Rates**: Failed requests, AI model errors, system exceptions
- **User Analytics**: Per-user usage patterns, feature adoption

This structured logging enables data-driven optimization of the email categorization system and provides valuable insights into user behavior and system performance.
