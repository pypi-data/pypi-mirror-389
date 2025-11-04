"""
Decorators for AI monitoring - plug and play solution.
"""
import time
import functools
from typing import Callable, Any, Optional, Dict
import inspect

def monitor_llm_call(model: Optional[str] = None, 
                     track_tokens: bool = True,
                     track_cost: bool = True,
                     metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to monitor LLM calls automatically.
    
    Usage:
        @monitor_llm_call(model="gpt-4")
        def call_openai(prompt):
            # Your LLM call code
            return response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # CRITICAL FIX: Force enable monitoring on each call to ensure cross-machine compatibility
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔧 [DECORATOR INIT] monitor_llm_call decorator active for function: {func.__name__}")
            
            # Force HTTP monitoring setup if not already done
            try:
                from .http_interceptor import enable_http_monitoring
                enable_http_monitoring()
                logger.info(f"✅ [DECORATOR] HTTP monitoring force-enabled")
            except Exception as e:
                logger.warning(f"⚠️ [DECORATOR] Could not enable HTTP monitoring: {e}")
            from . import get_monitor
            
            monitor = get_monitor()
            start_time = time.time()
            
            # Extract prompt from arguments
            prompt = _extract_prompt(args, kwargs, func)
            detected_model = model or _detect_model(args, kwargs) or "unknown"
            
            # Try to capture request path for distinguishing requests
            request_path = "unknown"
            try:
                # Try Flask first
                from flask import request
                if hasattr(request, 'path'):
                    request_path = request.path
                    logger.info(f"📍 [DECORATOR] Captured Flask request path: {request_path}")
            except ImportError:
                try:
                    # Try FastAPI/Starlette
                    from starlette.requests import Request
                    from starlette.context import _request_context
                    if _request_context.exists():
                        current_request = _request_context.get()
                        if isinstance(current_request, Request):
                            request_path = current_request.url.path
                            logger.info(f"📍 [DECORATOR] Captured FastAPI request path: {request_path}")
                except ImportError:
                    try:
                        # Try Django
                        from django.http import HttpRequest
                        from django.utils.deprecation import MiddlewareMixin
                        import threading
                        # Django stores request in thread local
                        current_request = getattr(threading.current_thread(), 'django_request', None)
                        if current_request and isinstance(current_request, HttpRequest):
                            request_path = current_request.path
                            logger.info(f"📍 [DECORATOR] Captured Django request path: {request_path}")
                    except ImportError:
                        try:
                            # Try Bottle
                            import bottle
                            if hasattr(bottle, 'request') and hasattr(bottle.request, 'path'):
                                request_path = bottle.request.path
                                logger.info(f"📍 [DECORATOR] Captured Bottle request path: {request_path}")
                        except ImportError:
                            try:
                                # Try CherryPy
                                import cherrypy
                                if hasattr(cherrypy, 'request') and hasattr(cherrypy.request, 'path'):
                                    request_path = cherrypy.request.path
                                    logger.info(f"📍 [DECORATOR] Captured CherryPy request path: {request_path}")
                            except ImportError:
                                try:
                                    # Try Tornado (basic support)
                                    import tornado.httputil
                                    # Tornado doesn't have a global request object, skip for now
                                    pass
                                except ImportError:
                                    logger.debug("No supported web framework detected for request path capture")
                except Exception as e:
                    logger.debug(f"Could not capture request path from FastAPI: {e}")
            except Exception as e:
                logger.debug(f"Could not capture request path: {e}")
            
            # Merge request path into metadata
            call_metadata = metadata.copy() if metadata else {}
            call_metadata['request_path'] = request_path
            
            # Capture temperature and max_tokens from kwargs
            call_metadata['temperature'] = kwargs.get('temperature', 0.7)
            call_metadata['max_tokens'] = kwargs.get('max_tokens', 0)
            
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                
                # Extract response data (now includes enhanced metadata)
                response_text, input_tokens, output_tokens, cost, enhanced_metadata = _extract_response_data(
                    result, track_tokens, track_cost
                )
                
                # Merge enhanced metadata (cached_tokens, reasoning_tokens, audio_tokens)
                call_metadata.update(enhanced_metadata)
                
                # CRITICAL: Calculate cost if not already provided
                if track_cost and cost == 0.0 and (input_tokens > 0 or output_tokens > 0):
                    try:
                        from .cost_optimizer import CostOptimizer
                        cost = CostOptimizer.calculate_cost(
                            model=detected_model,
                            prompt_tokens=input_tokens,
                            completion_tokens=output_tokens
                        )
                        logger.info(f"💰 [COST CALC] model={detected_model}, input={input_tokens}, output={output_tokens}, cost=${cost:.4f}")
                    except Exception as e:
                        logger.debug(f"Could not calculate cost: {e}")
                        cost = 0.0
                
                # Record the call
                call_id = monitor.record_llm_call(
                    model=detected_model,
                    prompt=prompt,
                    response=response_text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency=latency,
                    cost=cost,
                    metadata=call_metadata
                )
                
                # Add monitoring metadata to result if possible
                if hasattr(result, '__dict__'):
                    result.__dict__['_monitor_call_id'] = call_id
                
                return result
                
            except Exception as e:
                latency = time.time() - start_time
                monitor.record_metric(f"llm.{detected_model}.errors", 1)
                monitor.record_metric(f"llm.{detected_model}.error_latency", latency)
                raise
                
        return wrapper
    return decorator

def monitor_agent(name: Optional[str] = None, 
                  track_tools: bool = True,
                  track_decisions: bool = True):
    """
    Decorator to monitor AI agent sessions.
    
    Usage:
        @monitor_agent(name="my_agent")
        def run_agent_task():
            # Your agent code
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from . import get_monitor
            
            monitor = get_monitor()
            agent_name = name or func.__name__
            session_id = f"{agent_name}_{int(time.time())}"
            
            start_time = time.time()
            monitor.record_metric(f"agent.{agent_name}.sessions_started", 1)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                monitor.record_metric(f"agent.{agent_name}.session_duration", duration)
                monitor.record_metric(f"agent.{agent_name}.sessions_completed", 1)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                monitor.record_metric(f"agent.{agent_name}.sessions_failed", 1)
                monitor.record_metric(f"agent.{agent_name}.error_duration", duration)
                raise
                
        return wrapper
    return decorator

def monitor_tool_use(tool_name: Optional[str] = None):
    """
    Decorator to monitor AI tool usage.
    
    Usage:
        @monitor_tool_use(tool_name="web_search")
        def search_web(query):
            # Your tool code
            return results
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from . import get_monitor
            
            monitor = get_monitor()
            name = tool_name or func.__name__
            
            start_time = time.time()
            monitor.record_metric(f"tool.{name}.calls", 1)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                monitor.record_metric(f"tool.{name}.success_duration", duration)
                monitor.record_metric(f"tool.{name}.success_calls", 1)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                monitor.record_metric(f"tool.{name}.error_duration", duration)
                monitor.record_metric(f"tool.{name}.error_calls", 1)
                raise
                
        return wrapper
    return decorator

def _extract_prompt(args, kwargs, func):
    """Extract prompt from function arguments."""
    # Try common prompt parameter names
    prompt_keys = ['prompt', 'message', 'messages', 'input', 'text', 'query']
    
    # Check kwargs first
    for key in prompt_keys:
        if key in kwargs:
            value = kwargs[key]
            if isinstance(value, str):
                return value
            elif isinstance(value, list) and len(value) > 0:
                # Handle messages format
                return str(value)
    
    # Check positional arguments
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    
    for i, arg in enumerate(args):
        if i < len(param_names):
            param_name = param_names[i]
            if param_name in prompt_keys:
                return str(arg)
    
    # Fallback to first string argument
    for arg in args:
        if isinstance(arg, str) and len(arg) > 0:
            return arg
    
    return "unknown"

def _detect_model(args, kwargs):
    """Detect model from function arguments."""
    model_keys = ['model', 'engine', 'model_name', 'model_id']
    
    for key in model_keys:
        if key in kwargs:
            return str(kwargs[key])
    
    # Check if it's an OpenAI-style call
    if 'messages' in kwargs or 'prompt' in kwargs:
        return "openai-api"
    
    return None

def _extract_response_data(result, track_tokens=True, track_cost=True):
    """Extract response data from function result."""
    response_text = ""
    input_tokens = 0
    output_tokens = 0
    cost = 0.0
    
    # NEW: Additional metadata for enhanced metrics
    cached_tokens = 0
    reasoning_tokens = 0
    audio_tokens = 0
    
    if isinstance(result, str):
        response_text = result
        if track_tokens:
            # Rough token estimation
            output_tokens = len(result.split()) * 1.3  # Rough approximation
    
    elif isinstance(result, dict):
        # Handle OpenAI-style response dict
        if 'choices' in result:
            choice = result['choices'][0]
            if 'message' in choice:
                response_text = choice['message'].get('content', '')
            elif 'text' in choice:
                response_text = choice['text']
        
        # Extract usage information - ENHANCED for Azure OpenAI
        if 'usage' in result and track_tokens:
            usage = result['usage']
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            
            # CRITICAL DEBUG: Log what we extracted from dict response
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🚨 [DECORATOR DICT] Extracted from dict response:")
            logger.info(f"   Input tokens: {input_tokens} (from usage.prompt_tokens)")
            logger.info(f"   Output tokens: {output_tokens} (from usage.completion_tokens)")
            logger.info(f"   Full usage: {usage}")
            
        # Extract cost if available
        if track_cost and 'cost' in result:
            cost = result['cost']
    
    elif hasattr(result, 'choices') and hasattr(result, 'usage'):
        # Handle OpenAI v1.x response objects (ChatCompletion, Completion, etc.)
        # Extract response text from choices
        if hasattr(result, 'choices') and len(result.choices) > 0:
            choice = result.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                response_text = choice.message.content or ""
            elif hasattr(choice, 'text'):
                response_text = choice.text or ""
        
        # Extract usage information - ENHANCED for Azure OpenAI with cache details
        if hasattr(result, 'usage') and track_tokens:
            usage = result.usage
            # Azure OpenAI uses prompt_tokens/completion_tokens, not input_tokens/output_tokens
            try:
                input_tokens = int(getattr(usage, 'prompt_tokens', 0) or 0)
                output_tokens = int(getattr(usage, 'completion_tokens', 0) or 0)
                
                # NEW: Extract prompt_tokens_details for cached tokens
                if hasattr(usage, 'prompt_tokens_details'):
                    prompt_details = usage.prompt_tokens_details
                    cached_tokens = int(getattr(prompt_details, 'cached_tokens', 0) or 0)
                
                # NEW: Extract completion_tokens_details for reasoning/audio tokens
                if hasattr(usage, 'completion_tokens_details'):
                    completion_details = usage.completion_tokens_details
                    reasoning_tokens = int(getattr(completion_details, 'reasoning_tokens', 0) or 0)
                    audio_tokens = int(getattr(completion_details, 'audio_tokens', 0) or 0)
                    
            except (TypeError, ValueError):
                # Fallback if attributes aren't numbers
                input_tokens = 0
                output_tokens = 0
            
            # CRITICAL DEBUG: Log what we extracted
            import logging
            logger = logging.getLogger(__name__)
            if input_tokens > 0 or output_tokens > 0:
                logger.info(f"🚨 [DECORATOR FIX] Extracted from OpenAI response:")
                logger.info(f"   Input tokens: {input_tokens} (from usage.prompt_tokens)")
                logger.info(f"   Output tokens: {output_tokens} (from usage.completion_tokens)")
                if cached_tokens > 0:
                    logger.info(f"   💰 Cached tokens: {cached_tokens} (saved ~${cached_tokens * 0.03 / 1000 * 0.5:.4f})")
                if reasoning_tokens > 0:
                    logger.info(f"   🧠 Reasoning tokens: {reasoning_tokens}")
                logger.info(f"   Usage object: {usage}")
            else:
                logger.info(f"⚠️ [DECORATOR FIX] No valid tokens found in usage object: {usage}")
    
    elif hasattr(result, 'content'):
        # Handle other response objects with content attribute
        response_text = str(result.content)
        
        if hasattr(result, 'usage') and track_tokens:
            usage = result.usage
            # Fallback for other response formats
            input_tokens = (getattr(usage, 'prompt_tokens', 0) or 
                           getattr(usage, 'input_tokens', 0) or 0)
            output_tokens = (getattr(usage, 'completion_tokens', 0) or 
                            getattr(usage, 'output_tokens', 0) or 0)
    
    else:
        response_text = str(result)
    
    # Ensure we have token counts
    if track_tokens and output_tokens == 0 and response_text:
        output_tokens = max(1, len(response_text.split()) * 1.3)
    
    # Return enhanced data with additional metadata
    enhanced_metadata = {
        'cached_tokens': cached_tokens,
        'reasoning_tokens': reasoning_tokens,
        'audio_tokens': audio_tokens
    }
    
    return response_text, int(input_tokens), int(output_tokens), float(cost), enhanced_metadata
