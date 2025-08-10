"""
CrashLens logging integration for API call tracking.
"""

import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# FastAPI imports
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Local imports
from ..core.logger import logger

# Use the actual CrashLens Logger package
from crashlens_logger import CrashLensLogger, LogEvent

# Create a wrapper class to handle crashlens-logger v0.1.0 bugs
class SafeCrashLensLogger(CrashLensLogger):
    """Wrapper to handle bugs in crashlens-logger v0.1.0"""
    
    def write_logs(self, events: List[Any], output_path: str) -> None:
        """Safe write_logs that handles missing attributes and writes in simple format. Accepts a list of any event objects."""
        from pathlib import Path
        import json
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write events manually in simplified format
        with open(output_path, 'a', encoding='utf-8') as f:
            for event in events:
                try:
                    # Create simplified log format like the example
                    input_data = getattr(event, 'input', {})
                    # Remove prompt from input to keep logs clean
                    clean_input = {k: v for k, v in input_data.items() if k != 'prompt'}
                    
                    simple_log = {
                        "traceId": getattr(event, 'traceId', str(uuid.uuid4())),
                        "type": getattr(event, 'type', 'generation'),
                        "startTime": getattr(event, 'startTime', datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
                        "input": clean_input,
                        "usage": getattr(event, 'usage', {}),
                        "cost": getattr(event, 'cost', 0.0)
                    }
                    
                    json.dump(simple_log, f, ensure_ascii=False, default=str)
                    f.write('\n')
                except Exception as write_error:
                    logger.warning(f"Failed to write individual log event: {write_error}")

class APICallLogger:
    """Handles API call logging using CrashLens Logger."""
    
    def __init__(self, log_file_path: str = "logs/api_calls.jsonl"):
        self.log_file_path = log_file_path
        self.crashlens_logger = SafeCrashLensLogger(dev_mode=False)
        
        # Ensure log directory exists
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
    
    def log_api_call(
        self,
        endpoint: str,
        method: str,
        request_data: Dict[str, Any],
        
        
        response_data: Dict[str, Any],
        status_code: int,
        latency_ms: int,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Log an API call with simplified format."""
        
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        start_time = datetime.now(timezone.utc)
        
        # Estimate "tokens" based on data size (for tracking purposes)
        input_tokens = self._estimate_data_size(request_data)
        output_tokens = self._estimate_data_size(response_data)
        
        # Create simple event object
        class SimpleEvent:
            def __init__(self):
                self.traceId = trace_id
                self.type = "generation"
                self.startTime = start_time.isoformat().replace('+00:00', 'Z')
                self.input = {
                    "model": "api-server"
                }
                self.usage = {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
                self.cost = 0.0
        
        event = SimpleEvent()
        
        # Write to log file
        try:
            self.crashlens_logger.write_logs([event], self.log_file_path)
            logger.info(f"API call logged: {method} {endpoint} - {status_code} - {latency_ms}ms")
        except Exception as e:
            logger.error(f"Failed to write API log: {e}")
    
    def _estimate_data_size(self, data: Any) -> int:
        """Estimate data size in 'tokens' (characters/4)."""
        if not data:
            return 0
        try:
            return len(str(data)) // 4
        except:
            return 0


class APILoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log all API calls."""
    
    def __init__(self, app, api_logger: APICallLogger):
        super().__init__(app)
        self.api_logger = api_logger
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        start_time = datetime.now(timezone.utc)
        trace_id = str(uuid.uuid4())
        
        # Extract request data
        request_data = {}
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                # Clone request to read body
                body = await request.body()
                if body:
                    import json
                    try:
                        request_data = json.loads(body)
                    except:
                        request_data = {"body": body.decode("utf-8", errors="ignore")[:500]}
            
            # Add query parameters
            if request.query_params:
                request_data.update(dict(request.query_params))
            
        except Exception as e:
            logger.warning(f"Failed to extract request data: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate timing
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Create simple event object for API request
        class SimpleEvent:
            def __init__(self):
                self.traceId = trace_id
                self.type = "generation"
                self.startTime = start_time.isoformat().replace('+00:00', 'Z')
                self.input = {
                    "model": "fastapi-server"
                }
                self.usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
                self.cost = 0.0
        
        event = SimpleEvent()
        
        try:
            self.api_logger.crashlens_logger.write_logs([event], self.api_logger.log_file_path)
        except Exception as e:
            logger.error(f"Failed to log API request: {e}")
        
        return response


class EmailAPILogger:
    """Specialized logger for email-related operations."""
    
    def __init__(self, api_logger: APICallLogger):
        self.api_logger = api_logger
    
    def log_email_classification(
        self,
        email_subject: str,
        email_body: str,
        predicted_category: str,
        confidence: Optional[float] = None,
        model_used: str = "gemini-2.0-flash",
        processing_time_ms: int = 0,
        user_id: Optional[str] = None,
        prompt: Optional[str] = None
    ):
        """Log email classification operations in simplified format."""
        
        trace_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        # Create the prompt if not provided
        if prompt is None:
            prompt = f"Classify this email: Subject: {email_subject} Body: {email_body[:200]}..."
        
        # Estimate tokens based on email content
        input_tokens = len(prompt) // 4
        output_tokens = len(predicted_category) // 4
        
        # Create simple event object with just the required fields
        class SimpleEvent:
            def __init__(self):
                self.traceId = trace_id
                self.type = "generation"
                self.startTime = start_time.isoformat().replace('+00:00', 'Z')
                self.input = {
                    "model": model_used
                }
                self.usage = {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
                self.cost = 0.0
        
        event = SimpleEvent()
        
        try:
            self.api_logger.crashlens_logger.write_logs([event], self.api_logger.log_file_path)
            logger.info(f"Email classification logged: {predicted_category} - {processing_time_ms}ms")
        except Exception as e:
            logger.error(f"Failed to log email classification: {e}")
    
    def log_email_summarization(
        self,
        email_body: str,
        summary_bullets: List[str],
        model_used: str = "gemini-2.0-flash",
        processing_time_ms: int = 0,
        user_id: Optional[str] = None,
        prompt: Optional[str] = None
    ):
        """Log email summarization operations in simplified format."""
        
        trace_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        # Create the prompt if not provided
        if prompt is None:
            prompt = f"Summarize this email into bullet points: {email_body[:200]}..."
        
        input_tokens = len(prompt) // 4
        output_tokens = sum(len(bullet) for bullet in summary_bullets) // 4
        
        # Create simple event object with just the required fields
        class SimpleEvent:
            def __init__(self):
                self.traceId = trace_id
                self.type = "generation"
                self.startTime = start_time.isoformat().replace('+00:00', 'Z')
                self.input = {
                    "model": model_used
                }
                self.usage = {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
                self.cost = 0.0
        
        event = SimpleEvent()
        
        try:
            self.api_logger.crashlens_logger.write_logs([event], self.api_logger.log_file_path)
            logger.info(f"Email summarization logged: {len(summary_bullets)} bullets - {processing_time_ms}ms")
        except Exception as e:
            logger.error(f"Failed to log email summarization: {e}")


# Utility function for abstracting LLM calls with logging
def call_llm(model: str, prompt: str, **kwargs) -> Dict[str, Any]:
    """
    Abstract LLM call function with automatic logging.
    
    If you're abstracting LLM calls into a function like:
    
    def call_llm(model, prompt):
        response = openai.ChatCompletion.create(model=model, messages=[...])
        # return tokens, cost, etc.
    
    Then you should pass the model as a parameter and log it just like above.
    
    Args:
        model: The model name (e.g., "gpt-3.5-turbo", "gemini-2.0-flash")
        prompt: The input prompt
        **kwargs: Additional parameters for the LLM call
        
    Returns:
        Dict containing response, tokens, cost, etc.
    """
    import time
    start_time = datetime.now(timezone.utc)
    trace_id = str(uuid.uuid4())
    
    try:
        # This is a template - replace with actual LLM API call
        # Example for OpenAI:
        # response = openai.ChatCompletion.create(
        #     model=model,
        #     messages=[{"role": "user", "content": prompt}],
        #     **kwargs
        # )
        
        # For now, return a mock response structure
        response = {
            "choices": [{"message": {"content": "Mock LLM response"}}],
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": 10,
                "total_tokens": len(prompt) // 4 + 10
            }
        }
        
        # Extract response data
        content = response["choices"][0]["message"]["content"]
        usage = response.get("usage", {})
        
        # Log the LLM call
        class SimpleEvent:
            def __init__(self):
                self.traceId = trace_id
                self.type = "generation"
                self.startTime = start_time.isoformat().replace('+00:00', 'Z')
                self.input = {
                    "model": model
                }
                self.usage = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
                self.cost = 0.0  # Calculate based on model pricing
        
        event = SimpleEvent()
        api_logger.crashlens_logger.write_logs([event], api_logger.log_file_path)
        
        return {
            "content": content,
            "usage": usage,
            "model": model,
            "trace_id": trace_id
        }
        
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


# Global logger instances
api_logger = APICallLogger()
email_logger = EmailAPILogger(api_logger)
