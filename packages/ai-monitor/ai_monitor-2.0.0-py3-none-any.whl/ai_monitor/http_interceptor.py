#!/usr/bin/env python3
"""
AI Monitor Interceptor - Monitors existing HTTP calls without changing source code
This module automatically intercepts requests to OpenAI/Azure OpenAI endpoints
"""

import requests
import time
import json
from functools import wraps
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Store original requests methods
_original_post = requests.post
_original_get = requests.get
_original_request = requests.request

# Store original httpx methods (if available)
_original_httpx_post = None
_original_httpx_get = None
try:
    import httpx
    _original_httpx_post = httpx.post
    _original_httpx_get = httpx.get
    print("🔍 [Monitor] HTTPX detected - will also monitor httpx calls")
except ImportError:
    httpx = None

def _detect_api_endpoint(url):
    """Detect the type of OpenAI API endpoint from URL"""
    url_lower = url.lower()
    
    if 'chat/completions' in url_lower:
        return 'chat'
    elif 'completions' in url_lower and 'chat' not in url_lower:
        return 'completion'
    elif 'embeddings' in url_lower:
        return 'embedding'
    elif 'images/generations' in url_lower:
        return 'image_generation'
    elif 'audio/transcriptions' in url_lower:
        return 'audio_transcription'
    elif 'audio/translations' in url_lower:
        return 'audio_translation'
    elif 'fine-tuning' in url_lower:
        return 'fine_tuning'
    elif 'moderations' in url_lower:
        return 'moderation'
    else:
        return 'unknown'

def _extract_prompt_by_endpoint(json_data, endpoint_type):
    """Extract prompt/input data based on API endpoint type"""
    if not json_data or not isinstance(json_data, dict):
        return str(json_data)[:200] if json_data else ""
    
    if endpoint_type == 'chat':
        # Chat completions - extract from messages
        messages = json_data.get('messages', [])
        if messages and isinstance(messages, list):
            prompt_parts = []
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    if role == 'user':
                        prompt_parts.append(content)
                    elif role == 'system':
                        prompt_parts.append(f"[System: {content}]")
            return ' '.join(prompt_parts)
    
    elif endpoint_type == 'completion':
        # Text completions - direct prompt
        return json_data.get('prompt', '')
    
    elif endpoint_type == 'embedding':
        # Embeddings - input text/texts
        input_data = json_data.get('input', '')
        if isinstance(input_data, list):
            return ' | '.join(str(item) for item in input_data[:3])  # Show first 3 items
        return str(input_data)
    
    elif endpoint_type == 'image_generation':
        # Image generation - prompt
        return json_data.get('prompt', '')
    
    elif endpoint_type in ['audio_transcription', 'audio_translation']:
        # Audio - file info (can't show actual audio content)
        return f"Audio file processing (model: {json_data.get('model', 'unknown')})"
    
    elif endpoint_type == 'moderation':
        # Moderation - input text
        return json_data.get('input', '')
    
    else:
        # Unknown endpoint - try common fields
        for field in ['prompt', 'input', 'text', 'messages']:
            if field in json_data:
                value = json_data[field]
                if isinstance(value, str):
                    return value
                elif isinstance(value, list) and len(value) > 0:
                    return str(value[0])
        
        return str(json_data)[:200]

def _extract_response_by_endpoint(resp_json, endpoint_type):
    """Extract response data based on API endpoint type"""
    response_text = ""
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    
    # Debug: Print the actual response structure
    logger.info(f"🔍 [Debug] Response JSON keys: {list(resp_json.keys()) if resp_json else 'None'}")
    
    # Extract token usage (common across most endpoints)
    usage = resp_json.get('usage', {})
    logger.info(f"🔍 [FIXED] Full usage object from Azure: {usage}")
    
    if usage:
        # FIXED: More robust token extraction with explicit logging
        # Azure OpenAI typically uses: prompt_tokens, completion_tokens, total_tokens
        input_tokens = usage.get('prompt_tokens', 0)
        output_tokens = usage.get('completion_tokens', 0) 
        total_tokens = usage.get('total_tokens', 0)
        
        # Fallback to alternative field names if main ones are not present
        if input_tokens == 0:
            input_tokens = usage.get('input_tokens', 0) or usage.get('promptTokens', 0)
        if output_tokens == 0:
            output_tokens = (usage.get('output_tokens', 0) or 
                           usage.get('completionTokens', 0) or 
                           usage.get('generated_tokens', 0))
        if total_tokens == 0:
            total_tokens = usage.get('totalTokens', 0) or (input_tokens + output_tokens)
        
        logger.info(f"✅ [FIXED] Azure tokens extracted - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
        
        # Validate and potentially correct the tokens
        is_valid, corrected_total = validate_azure_tokens(input_tokens, output_tokens, total_tokens, "Azure")
        if is_valid:
            total_tokens = corrected_total  # Use corrected total if needed
            logger.info(f"🎯 [FIXED] Using validated Azure tokens: {input_tokens} + {output_tokens} = {total_tokens}")
        else:
            logger.info(f"⚠️ [FIXED] Azure tokens invalid - will fall back to estimation")
        
        # FIXED: Alert if we got tokens from Azure - prioritize these!
        if input_tokens > 0:
            logger.info(f"✅ [FIXED] Azure provided {input_tokens} input tokens - USING EXACTLY THESE!")
        else:
            logger.info(f"⚠️ [FIXED] Azure provided 0 input tokens - WILL CALCULATE FALLBACK!")
    else:
        logger.info("⚠️ [FIXED] No usage data found in response!")
    
    if endpoint_type in ['chat', 'completion']:
        # Chat and text completions
        choices = resp_json.get('choices', [])
        if choices and len(choices) > 0:
            choice = choices[0]
            if 'message' in choice:
                response_text = choice['message'].get('content', '')
            elif 'text' in choice:
                response_text = choice.get('text', '')
    
    elif endpoint_type == 'embedding':
        # Embeddings - show metadata about embeddings created
        data = resp_json.get('data', [])
        response_text = f"Generated {len(data)} embeddings"
        # Embeddings don't have output tokens, only input tokens
        output_tokens = 0
        total_tokens = input_tokens
    
    elif endpoint_type == 'image_generation':
        # Image generation - show image count and URLs
        data = resp_json.get('data', [])
        if data:
            response_text = f"Generated {len(data)} images"
            # Add image info if available
            if len(data) > 0 and 'url' in data[0]:
                response_text += f" (first: {data[0]['url'][:50]}...)"
        # Images don't typically have token usage
        input_tokens = len(resp_json.get('prompt', '').split()) if 'prompt' in resp_json else 0
        output_tokens = 0
        total_tokens = input_tokens
    
    elif endpoint_type in ['audio_transcription', 'audio_translation']:
        # Audio processing - show transcribed/translated text
        response_text = resp_json.get('text', 'Audio processed')
        # Audio endpoints may not have token usage
        if not usage:
            input_tokens = 1  # Represents audio file
            output_tokens = len(response_text.split()) if response_text else 0
            total_tokens = input_tokens + output_tokens
    
    elif endpoint_type == 'moderation':
        # Moderation - show results
        results = resp_json.get('results', [])
        if results and len(results) > 0:
            result = results[0]
            flagged = result.get('flagged', False)
            categories = result.get('categories', {})
            flagged_cats = [cat for cat, flag in categories.items() if flag]
            response_text = f"Moderation: {'Flagged' if flagged else 'Clean'}"
            if flagged_cats:
                response_text += f" ({', '.join(flagged_cats)})"
        # Moderation doesn't have token usage
        if not usage:
            input_tokens = len(str(resp_json.get('input', '')).split())
            output_tokens = 0
            total_tokens = input_tokens
    
    else:
        # Unknown endpoint - try to extract any text content
        response_text = str(resp_json)[:200]
        if not usage:
            # Estimate tokens if no usage provided
            input_tokens = 0
            output_tokens = len(response_text.split()) if response_text else 0
            total_tokens = output_tokens
    
    return response_text, (input_tokens, output_tokens, total_tokens)

def _extract_model_from_request(json_data, url, endpoint_type):
    """Extract model name from request data or URL"""
    model = "unknown"
    
    # First try to get model from JSON (standard OpenAI)
    if json_data and isinstance(json_data, dict):
        model = json_data.get('model', 'unknown')
    elif json_data and isinstance(json_data, str):
        try:
            parsed = json.loads(json_data)
            model = parsed.get('model', 'unknown')
        except:
            pass
    
    # If model is still unknown, extract from Azure OpenAI URL path
    if model == "unknown" and 'deployments/' in url:
        try:
            # Extract model from URL like: /deployments/gpt-4o/chat/completions
            url_parts = url.split('/deployments/')
            if len(url_parts) > 1:
                deployment_part = url_parts[1].split('/')[0]  # Get gpt-4o
                model = deployment_part
                logger.info(f"🔍 [Monitor] Extracted model from Azure URL: {model}")
        except Exception as e:
            logger.info(f"⚠️ [Monitor] Could not extract model from URL: {e}")
    
    # If still unknown, infer from endpoint type
    if model == "unknown":
        endpoint_model_defaults = {
            'chat': 'gpt-chat-model',
            'completion': 'gpt-completion-model',
            'embedding': 'text-embedding-model',
            'image_generation': 'dall-e-model',
            'audio_transcription': 'whisper-model',
            'audio_translation': 'whisper-model',
            'moderation': 'text-moderation-model'
        }
        model = endpoint_model_defaults.get(endpoint_type, f"{endpoint_type}-model")
    
    return model

def _estimate_input_tokens(json_data, endpoint_type):
    """Estimate input tokens from request data when response doesn't provide them"""
    if not json_data or not isinstance(json_data, dict):
        return 0
    
    try:
        # Use tiktoken for most accurate estimation
        prompt_text = ""
        
        if endpoint_type == 'chat':
            # Chat completions - extract from messages
            messages = json_data.get('messages', [])
            prompt_parts = []
            for msg in messages:
                if isinstance(msg, dict):
                    content = msg.get('content', '')
                    prompt_parts.append(str(content))
            prompt_text = ' '.join(prompt_parts)
        
        elif endpoint_type == 'completion':
            prompt_text = str(json_data.get('prompt', ''))
        
        elif endpoint_type == 'embedding':
            input_data = json_data.get('input', '')
            if isinstance(input_data, list):
                prompt_text = ' '.join(str(item) for item in input_data)
            else:
                prompt_text = str(input_data)
        
        elif endpoint_type == 'image_generation':
            prompt_text = str(json_data.get('prompt', ''))
        
        else:
            prompt_text = str(json_data)[:1000]  # Limit for safety
        
        # Try tiktoken for accurate estimation
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(prompt_text))
        except:
            # Fallback: improved character-based estimation
            # GPT models average about 4.2 characters per token
            return max(1, len(prompt_text) // 4)
            
    except Exception as e:
        logger.info(f"⚠️ [FIXED] Error estimating input tokens: {e}")
        return 0

def validate_azure_tokens(input_tokens, output_tokens, total_tokens, source="Azure"):
    """Validate that token values are consistent and reasonable"""
    if input_tokens > 0 and output_tokens >= 0:
        expected_total = input_tokens + output_tokens
        if total_tokens == expected_total or total_tokens == 0:
            logger.info(f"✅ [VALIDATE] {source} tokens are valid: {input_tokens}+{output_tokens}={expected_total}")
            return True, expected_total
        else:
            logger.info(f"⚠️ [VALIDATE] {source} total_tokens mismatch: {total_tokens} vs expected {expected_total}")
            return True, expected_total  # Still trust input+output, recalculate total
    return False, 0

def extract_openai_data(url, json_data, headers, response):
    """Extract OpenAI call data from HTTP request/response"""
    try:
        # Expanded check for all OpenAI/Azure OpenAI API calls
        openai_indicators = [
            'openai.azure.com', 'api.openai.com',
            '/chat/completions', '/completions', '/embeddings', 
            '/images/generations', '/audio/transcriptions', '/audio/translations',
            '/fine-tuning/', '/files/', '/models/', '/moderations'
        ]
        
        if not any(indicator in url.lower() for indicator in openai_indicators):
            return None
        
        logger.info(f"🔍 [Monitor] Intercepted OpenAI API call to: {url}")
        
        # Determine API endpoint type from URL
        endpoint_type = _detect_api_endpoint(url)
        logger.info(f"🔍 [Monitor] Detected endpoint type: {endpoint_type}")
        
        # Extract model from request (Azure OpenAI uses URL path, not JSON)
        model = "unknown"
        
        # Enhanced model detection for all endpoint types
        model = _extract_model_from_request(json_data, url, endpoint_type)
        
        # Debug: Print request data structure
        logger.info(f"🔍 [Debug] Request JSON data type: {type(json_data)}")
        if json_data and isinstance(json_data, dict):
            logger.info(f"🔍 [Debug] Request JSON keys: {list(json_data.keys())}")
        
        # Extract prompt/messages from request based on endpoint type
        prompt = _extract_prompt_by_endpoint(json_data, endpoint_type)
        
        # Extract response data based on endpoint type
        response_text = ""
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        
        try:
            if response and hasattr(response, 'json') and response.status_code == 200:
                logger.info(f"🔍 [Debug] Successful response (200), parsing JSON...")
                resp_json = response.json()
                logger.info(f"🔍 [Debug] Response JSON structure: {list(resp_json.keys()) if resp_json else 'None'}")
                response_text, tokens = _extract_response_by_endpoint(resp_json, endpoint_type)
                input_tokens, output_tokens, total_tokens = tokens
            elif response:
                logger.info(f"⚠️ [Debug] Non-200 response or no JSON method. Status: {response.status_code}, Response: {type(response)}")
                
                # If input tokens are still 0, estimate from request
                if input_tokens == 0 and json_data:
                    estimated_input = _estimate_input_tokens(json_data, endpoint_type)
                    if estimated_input > 0:
                        input_tokens = estimated_input
                        total_tokens = input_tokens + output_tokens
                        logger.info(f"🔢 [Debug] Estimated input tokens: {input_tokens}")
            else:
                logger.info(f"⚠️ [Debug] No response or no JSON method. Response: {response}")
                
        except Exception as e:
            logger.info(f"❌ [Debug] Error extracting response data: {e}")
            logger.debug(f"Error extracting response data: {e}")
        
        # FIXED: Only estimate input tokens if Azure didn't provide them (input_tokens == 0)
        if input_tokens == 0 and json_data:
            estimated_input = _estimate_input_tokens(json_data, endpoint_type)
            if estimated_input > 0:
                input_tokens = estimated_input
                total_tokens = input_tokens + output_tokens
                logger.info(f"🔢 [FIXED] Estimated input tokens (no Azure data): {input_tokens}")
        elif input_tokens > 0:
            # Azure provided tokens - use them exactly as-is
            logger.info(f"✅ [FIXED] Using Azure-provided input tokens: {input_tokens}")
            total_tokens = input_tokens + output_tokens
        
        # FIXED: Final fallback only if no tokens from Azure and no previous estimation worked
        if input_tokens == 0 and prompt and len(prompt) > 0:
            # Use tiktoken for most accurate estimation when Azure doesn't provide tokens
            try:
                import tiktoken
                encoding = tiktoken.get_encoding("cl100k_base")  # Most common encoding
                input_tokens = len(encoding.encode(prompt))
                logger.info(f"🔢 [FIXED] Tiktoken estimation: {input_tokens}")
            except:
                # Fallback to character-based estimation
                input_tokens = max(1, len(prompt) // 4)
                logger.info(f"� [FIXED] Character-based estimation: {input_tokens}")
            
            total_tokens = input_tokens + output_tokens

        return {
            'model': model,
            'prompt': prompt,
            'response': response_text,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens
        }
        
    except Exception as e:
        logger.error(f"Error extracting OpenAI data: {e}")
        return None

def _extract_flask_request_context():
    """Extract metadata from Flask request context if available"""
    metadata = {}
    try:
        from flask import has_request_context, request
        if has_request_context():
            # Extract portfolio/platform from request JSON if available
            if request.is_json and request.json:
                json_data = request.json
                if 'portfolio_name' in json_data:
                    metadata['portfolio'] = json_data['portfolio_name']
                if 'platform_name' in json_data:
                    metadata['platform'] = json_data['platform_name']
                if 'user_id' in json_data:
                    metadata['user_id'] = json_data['user_id']
            
            # Extract from headers
            if 'X-User-ID' in request.headers:
                metadata['user_id'] = request.headers.get('X-User-ID')
            if 'X-Portfolio' in request.headers:
                metadata['portfolio'] = request.headers.get('X-Portfolio')
            
            # Store endpoint path as report_type
            if request.endpoint:
                metadata['report_type'] = request.endpoint.replace('_', '-')
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Could not extract Flask request context: {e}")
    
    return metadata

def monitored_post(*args, **kwargs):
    """Monitored version of requests.post"""
    url = args[0] if args else kwargs.get('url', '')
    json_data = kwargs.get('json')
    headers = kwargs.get('headers', {})
    
    # CRITICAL DEBUG: Log ALL requests to see what we're intercepting
    if 'openai' in url.lower() or 'azure' in url.lower():
        logger.info(f"🚨 [CRITICAL DEBUG] Intercepted POST: {url}")
        logger.info(f"🚨 [CRITICAL DEBUG] Request data keys: {list(json_data.keys()) if json_data else 'None'}")
    
    # Start timing
    start_time = time.time()
    
    # Make the original request
    response = _original_post(*args, **kwargs)
    
    # End timing
    end_time = time.time()
    latency = end_time - start_time
    
    # Try to extract OpenAI data and monitor it
    try:
        openai_data = extract_openai_data(url, json_data, headers, response)
        
        if openai_data:
            # Import here to avoid circular imports
            from ai_monitor import get_monitor
            monitor = get_monitor()
            
            if monitor:
                logger.info(f"📊 [Monitor] Recording LLM call:")
                logger.info(f"   Model: {openai_data['model']}")
                logger.info(f"   Tokens: {openai_data['input_tokens']}→{openai_data['output_tokens']}")
                logger.info(f"   Latency: {latency:.2f}s")
                
                # Enhance with quality analysis
                try:
                    from .quality_analyzer import enhance_llm_call_with_quality_analysis
                    
                    # Prepare call data for quality analysis
                    call_data = {
                        'prompt': openai_data['prompt'],
                        'response': openai_data['response'],
                        'model': openai_data['model'],
                        'input_tokens': openai_data['input_tokens'],
                        'output_tokens': openai_data['output_tokens'],
                        'latency': latency,
                        'metadata': {
                            'intercepted': True,
                            'url': url,
                            'method': 'POST'
                        }
                    }
                    
                    # Perform quality analysis
                    enhanced_data = enhance_llm_call_with_quality_analysis(call_data)
                    
                    # Print quality metrics
                    logger.info(f"🎯 [Quality] Score: {enhanced_data['quality_score']:.2f}")
                    logger.info(f"🚨 [Quality] Hallucination Risk: {enhanced_data['hallucination_risk']}")
                    if enhanced_data['drift_detected']:
                        logger.info(f"⚠️ [Quality] Drift detected!")
                    if enhanced_data['quality_issues']:
                        logger.info(f"❌ [Quality] Issues: {', '.join(enhanced_data['quality_issues'])}")
                    
                    # Update metadata with quality info
                    openai_data['quality_analysis'] = enhanced_data['quality_analysis']
                    
                except Exception as quality_error:
                    logger.info(f"⚠️ [Quality] Analysis failed: {quality_error}")
                
                # FIXED: Only apply estimation if Azure didn't provide input tokens
                if openai_data['input_tokens'] == 0 and openai_data['prompt']:
                    # Use tiktoken for accurate estimation when no Azure tokens
                    try:
                        import tiktoken
                        encoding = tiktoken.get_encoding("cl100k_base")
                        estimated_tokens = len(encoding.encode(openai_data['prompt']))
                        logger.info(f"🔢 [FIXED] Tiktoken estimation: {estimated_tokens} tokens")
                    except:
                        estimated_tokens = len(openai_data['prompt']) // 4
                        logger.info(f"🔢 [FIXED] Fallback estimation: {estimated_tokens} tokens")
                    
                    openai_data['input_tokens'] = estimated_tokens
                    openai_data['total_tokens'] = estimated_tokens + openai_data['output_tokens']
                elif openai_data['input_tokens'] > 0:
                    logger.info(f"✅ [FIXED] Using Azure-provided tokens: {openai_data['input_tokens']} input, {openai_data['output_tokens']} output")

                # Record the call
                flask_context = _extract_flask_request_context()
                call_id = monitor.record_llm_call(
                    model=openai_data['model'],
                    prompt=openai_data['prompt'],
                    response=openai_data['response'],
                    input_tokens=openai_data['input_tokens'],
                    output_tokens=openai_data['output_tokens'],
                    latency=latency,
                    metadata={
                        'intercepted': True,
                        'url': url,
                        'method': 'POST',
                        'quality_analysis': openai_data.get('quality_analysis', {}),
                        **flask_context  # Add Flask request context (portfolio, user_id, report_type)
                    }
                )
                
                logger.info(f"🎯 [Monitor] LLM call recorded with ID: {call_id}")
                
                # Force immediate export by checking exporters
                if hasattr(monitor, '_exporters'):
                    logger.info(f"🔍 [Monitor] Available exporters: {len(monitor._exporters)}")
                    for i, exporter in enumerate(monitor._exporters):
                        exporter_type = type(exporter).__name__
                        logger.info(f"   Exporter {i}: {exporter_type}")
                
                # Try to trigger immediate metrics export for debugging
                try:
                    monitor._export_metrics()
                    logger.info(f"✅ [Monitor] Forced metrics export completed")
                except Exception as export_error:
                    logger.info(f"⚠️ [Monitor] Metrics export failed: {export_error}")
                    
    except Exception as e:
        logger.error(f"Error monitoring request: {e}")
    
    return response

def monitored_get(*args, **kwargs):
    """Monitored version of requests.get for OpenAI API info endpoints"""
    url = args[0] if args else kwargs.get('url', '')
    headers = kwargs.get('headers', {})
    
    # Check if this is an OpenAI API GET request worth monitoring
    openai_indicators = [
        'openai.azure.com', 'api.openai.com',
        '/models', '/files', '/fine-tuning/jobs'
    ]
    
    if any(indicator in url.lower() for indicator in openai_indicators):
        logger.info(f"🔍 [Monitor] Intercepted OpenAI GET request to: {url}")
        
        # Start timing
        start_time = time.time()
        
        # Make the original request
        response = _original_get(*args, **kwargs)
        
        # End timing
        end_time = time.time()
        latency = end_time - start_time
        
        # Log the API info request
        from ai_monitor import get_monitor
        monitor = get_monitor()
        
        if monitor:
            logger.info(f"📊 [Monitor] OpenAI API info request - Latency: {latency:.2f}s")
            # Record as a metric but not as an LLM call
            monitor.record_metric("openai.api_info_requests", 1)
            monitor.record_metric("openai.api_info_latency", latency)
        
        return response
    else:
        # Not an OpenAI request, use original method
        return _original_get(*args, **kwargs)

def monitored_httpx_post(*args, **kwargs):
    """Monitored version of httpx.post"""
    url = args[0] if args else kwargs.get('url', '')
    
    # CRITICAL DEBUG: Always log Azure/OpenAI requests 
    if 'openai' in str(url).lower() or 'azure' in str(url).lower():
        logger.info(f"� [HTTPX CRITICAL] ================== INTERCEPTED AZURE REQUEST ==================")
        logger.info(f"🚨 [HTTPX CRITICAL] URL: {url}")
        logger.info(f"🚨 [HTTPX CRITICAL] This should extract Azure tokens!")
    else:
        logger.info(f"🔍 [HTTPX Monitor] Non-Azure request: {url}")
    
    if httpx is None:
        logger.info(f"❌ [HTTPX Monitor] HTTPX is None!")
        return None
        
    json_data = kwargs.get('json')
    headers = kwargs.get('headers', {})
    
    if 'azure' in str(url).lower():
        logger.info(f"� [HTTPX CRITICAL] JSON data keys: {list(json_data.keys()) if json_data else 'None'}")
        logger.info(f"� [HTTPX CRITICAL] Headers keys: {list(headers.keys()) if headers else 'None'}")
    
    # Start timing
    start_time = time.time()
    logger.info(f"🔍 [HTTPX Monitor] Calling original httpx.post...")
    
    # Make the original request
    response = _original_httpx_post(*args, **kwargs)
    
    # End timing
    end_time = time.time()
    latency = end_time - start_time
    
    logger.info(f"📊 [HTTPX Monitor] Response: {response.status_code} in {latency*1000:.2f}ms")
    
    # Try to extract OpenAI data and monitor it
    try:
        openai_data = extract_openai_data(url, json_data, headers, response)
        
        if openai_data:
            logger.info(f"📊 [HTTPX Monitor] Recording LLM call:")
            logger.info(f"   Model: {openai_data['model']}")
            logger.info(f"   Tokens: {openai_data['input_tokens']}→{openai_data['output_tokens']}")
            logger.info(f"   Latency: {latency:.2f}s")
            
            # Import here to avoid circular imports
            from ai_monitor import get_monitor
            monitor = get_monitor()
            
            if monitor:
                # FINAL SAFETY CHECK: Guarantee input tokens are calculated
                if openai_data['input_tokens'] == 0 and openai_data.get('prompt'):
                    prompt = openai_data['prompt']
                    # Triple estimation method for maximum accuracy
                    char_estimate = len(prompt) // 4
                    word_estimate = int(len(prompt.split()) * 1.3)
                    tiktoken_estimate = len(prompt) // 3.5
                    
                    estimated_tokens = max(int(char_estimate), int(word_estimate), int(tiktoken_estimate), 1)
                    openai_data['input_tokens'] = estimated_tokens
                    openai_data['total_tokens'] = estimated_tokens + openai_data.get('output_tokens', 0)
                    logger.info(f"� [FINAL SAFETY] Calculated input tokens: {estimated_tokens} (char={char_estimate}, word={word_estimate})")

                # Record the call
                call_id = monitor.record_llm_call(
                    model=openai_data['model'],
                    prompt=openai_data['prompt'],
                    response=openai_data['response'],
                    input_tokens=openai_data['input_tokens'],
                    output_tokens=openai_data['output_tokens'],
                    latency=latency,
                    metadata={
                        'intercepted': True,
                        'url': url,
                        'method': 'POST',
                        'http_client': 'httpx'
                    }
                )
                
    except Exception as e:
        logger.info(f"❌ [HTTPX Monitor] Error monitoring HTTPX request: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info(f"🔍 [HTTPX Monitor] ================== END HTTPX INTERCEPT ==================")
    return response

def monitored_httpx_client_post(self, url, *args, **kwargs):
    """Monitored version of httpx.Client.post"""
    logger.info(f"🔍 [HTTPX Client Monitor] ================== INTERCEPTED CLIENT POST ==================")
    logger.info(f"🔍 [HTTPX Client Monitor] URL: {url}")
    logger.info(f"🔍 [HTTPX Client Monitor] Args: {args}")
    logger.info(f"🔍 [HTTPX Client Monitor] Kwargs keys: {list(kwargs.keys()) if kwargs else 'None'}")
    
    # Start timing
    start_time = time.time()
    
    # Call original method
    original_post = httpx.Client._original_post
    response = original_post(self, url, *args, **kwargs)
    
    # End timing
    end_time = time.time()
    latency = end_time - start_time
    
    logger.info(f"📊 [HTTPX Client Monitor] Response: {response.status_code} in {latency*1000:.2f}ms")
    logger.info(f"🔍 [HTTPX Client Monitor] ================== END CLIENT INTERCEPT ==================")
    
    # Process the same way as regular httpx.post
    try:
        json_data = kwargs.get('json')
        headers = kwargs.get('headers', {})
        
        logger.info(f"🔍 [HTTPX Client Monitor] Checking if OpenAI call...")
        logger.info(f"🔍 [HTTPX Client Monitor] JSON data: {json_data is not None}")
        logger.info(f"🔍 [HTTPX Client Monitor] Headers: {headers is not None}")
        
        openai_data = extract_openai_data(url, json_data, headers, response)
        
        if openai_data:
            logger.info(f"🎯 [HTTPX Client Monitor] Detected OpenAI API call!")
            logger.info(f"🔍 [HTTPX Client Monitor] Raw OpenAI data: {openai_data}")
            
            if openai_data:
                logger.info(f"📊 [HTTPX Client Monitor] Recording LLM call:")
                logger.info(f"   Model: {openai_data['model']}")
                logger.info(f"   Tokens: {openai_data['input_tokens']}→{openai_data['output_tokens']}")
                logger.info(f"   Prompt length: {len(openai_data.get('prompt', ''))}")
                
                # Import here to avoid circular imports
                from ai_monitor import get_monitor
                monitor = get_monitor()
                
                if monitor:
                    # FINAL SAFETY CHECK: Ensure input tokens are NEVER zero
                    logger.info(f"🔢 [HTTPX Client Debug] Before final check - Input tokens: {openai_data['input_tokens']}, Prompt length: {len(openai_data.get('prompt', ''))}")
                    
                    if openai_data['input_tokens'] == 0 and openai_data.get('prompt'):
                        prompt = openai_data['prompt']
                        # Use multiple methods and take the maximum for best accuracy
                        char_estimate = len(prompt) // 4  # Conservative: ~4 chars per token
                        word_estimate = int(len(prompt.split()) * 1.3)  # More accurate: ~1.3 tokens per word
                        tiktoken_estimate = len(prompt) // 3.5  # Based on tiktoken averages
                        
                        estimated_tokens = max(int(char_estimate), int(word_estimate), int(tiktoken_estimate), 1)
                        openai_data['input_tokens'] = estimated_tokens
                        openai_data['total_tokens'] = estimated_tokens + openai_data.get('output_tokens', 0)
                        
                        logger.info(f"� [FINAL FIX] Calculated input tokens: {estimated_tokens}")
                        logger.info(f"🔧 [FINAL FIX] Methods: char={char_estimate}, word={word_estimate}, tiktoken={tiktoken_estimate}")
                    
                    logger.info(f"✅ [FINAL CHECK] Final tokens: {openai_data['input_tokens']}→{openai_data.get('output_tokens', 0)} (total: {openai_data.get('total_tokens', 0)})")
                    
                    # Record the call
                    call_id = monitor.record_llm_call(
                        model=openai_data['model'],
                        prompt=openai_data['prompt'],
                        response=openai_data['response'],
                        input_tokens=openai_data['input_tokens'],
                        output_tokens=openai_data['output_tokens'],
                        latency=0,  # We don't have timing here
                        metadata={
                            'intercepted': True,
                            'url': url,
                            'method': 'POST',
                            'http_client': 'httpx_client'
                        }
                    )
                    
    except Exception as e:
        logger.info(f"❌ [HTTPX Client Monitor] Error monitoring request: {e}")
        import traceback
        traceback.print_exc()
    
    return response

def monitored_httpx_client_request(self, method, url, *args, **kwargs):
    """Monitored version of httpx.Client.request (catches all HTTP methods)"""
    logger.info(f"🔍 [HTTPX Client Request] ================== INTERCEPTED {method.upper()} ==================")
    logger.info(f"🔍 [HTTPX Client Request] Method: {method}")
    logger.info(f"🔍 [HTTPX Client Request] URL: {url}")
    logger.info(f"🔍 [HTTPX Client Request] Args: {args}")
    logger.info(f"🔍 [HTTPX Client Request] Kwargs keys: {list(kwargs.keys()) if kwargs else 'None'}")
    
    # Start timing
    start_time = time.time()
    
    # Call original method
    original_request = httpx.Client._original_request
    response = original_request(self, method, url, *args, **kwargs)
    
    # End timing
    end_time = time.time()
    latency = end_time - start_time
    
    logger.info(f"📊 [HTTPX Client Request] Response: {response.status_code} in {latency*1000:.2f}ms")
    logger.info(f"🔍 [HTTPX Client Request] ================== END REQUEST INTERCEPT ==================")
    
    # Only process POST requests to OpenAI
    if method.upper() == 'POST':
        try:
            json_data = kwargs.get('json')
            headers = kwargs.get('headers', {})
            
            logger.info(f"🔍 [HTTPX Client Request] POST detected - checking if OpenAI...")
            
            openai_data = extract_openai_data(url, json_data, headers, response)
            
            if openai_data:
                logger.info(f"🎯 [HTTPX Client Request] Detected OpenAI API call!")
                logger.info(f"🔍 [HTTPX Client Request] Raw OpenAI data: {openai_data}")
                
                # Import here to avoid circular imports
                from ai_monitor import get_monitor
                monitor = get_monitor()
                
                if monitor:
                    # FINAL SAFETY CHECK: Guarantee input tokens are calculated
                    if openai_data['input_tokens'] == 0 and openai_data.get('prompt'):
                        prompt = openai_data['prompt']
                        # Triple estimation method for maximum accuracy
                        char_estimate = len(prompt) // 4
                        word_estimate = int(len(prompt.split()) * 1.3)
                        tiktoken_estimate = len(prompt) // 3.5
                        
                        estimated_tokens = max(int(char_estimate), int(word_estimate), int(tiktoken_estimate), 1)
                        openai_data['input_tokens'] = estimated_tokens
                        openai_data['total_tokens'] = estimated_tokens + openai_data.get('output_tokens', 0)
                        logger.info(f"🔧 [CLIENT REQUEST FIX] Calculated input tokens: {estimated_tokens}")
                    
                    # Record the call
                    call_id = monitor.record_llm_call(
                        model=openai_data['model'],
                        prompt=openai_data['prompt'],
                        response=openai_data['response'],
                        input_tokens=openai_data['input_tokens'],
                        output_tokens=openai_data['output_tokens'],
                        latency=latency,
                        metadata={
                            'intercepted': True,
                            'url': str(url),
                            'method': method.upper(),
                            'http_client': 'httpx_client_request'
                        }
                    )
                    logger.info(f"🔧 [CLIENT REQUEST] Successfully recorded call: {call_id}")
                        
        except Exception as e:
            logger.info(f"❌ [HTTPX Client Request] Error monitoring request: {e}")
            import traceback
            traceback.print_exc()
    
    return response

def monitored_request(*args, **kwargs):
    """Monitored version of requests.request"""
    method = args[0] if args else kwargs.get('method', '')
    url = args[1] if len(args) > 1 else kwargs.get('url', '')
    
    # Monitor both POST and GET requests to OpenAI endpoints
    if method.upper() == 'POST':
        return monitored_post(url, **{k: v for k, v in kwargs.items() if k != 'method'})
    elif method.upper() == 'GET':
        return monitored_get(url, **{k: v for k, v in kwargs.items() if k != 'method'})
    else:
        return _original_request(*args, **kwargs)

def enable_http_monitoring():
    """Enable HTTP request monitoring by monkey-patching requests and httpx"""
    print("🔧 [HTTP Monitor] Enabling HTTP request monitoring...")
    
    # Monkey patch requests module
    requests.post = monitored_post
    requests.get = monitored_get
    requests.request = monitored_request
    
    # Monkey patch httpx module if available
    if httpx is not None:
        httpx.post = monitored_httpx_post
        
        # Also patch httpx.Client.post method
        if hasattr(httpx, 'Client') and hasattr(httpx.Client, 'post'):
            if not hasattr(httpx.Client, '_original_post'):
                httpx.Client._original_post = httpx.Client.post
            httpx.Client.post = monitored_httpx_client_post
            print("✅ [HTTP Monitor] HTTPX Client monitoring enabled!")
            
            # PRODUCTION DEBUG: Let's also patch other httpx.Client methods
            if hasattr(httpx.Client, 'request') and not hasattr(httpx.Client, '_original_request'):
                httpx.Client._original_request = httpx.Client.request
                httpx.Client.request = monitored_httpx_client_request
                print("✅ [HTTP Monitor] HTTPX Client.request monitoring enabled!")
        
        print("✅ [HTTP Monitor] HTTPX monitoring enabled!")
        
        # PRODUCTION DEBUG: Show what we've patched
        logger.info(f"🔍 [DEBUG] httpx.post patched: {httpx.post.__name__ if hasattr(httpx.post, '__name__') else 'unknown'}")
        logger.info(f"🔍 [DEBUG] httpx.Client.post patched: {httpx.Client.post.__name__ if hasattr(httpx.Client.post, '__name__') else 'unknown'}")
        if hasattr(httpx.Client, 'request'):
            logger.info(f"🔍 [DEBUG] httpx.Client.request patched: {httpx.Client.request.__name__ if hasattr(httpx.Client.request, '__name__') else 'unknown'}")
    
    print("✅ [HTTP Monitor] HTTP monitoring enabled!")
    print("📊 [HTTP Monitor] All OpenAI API calls (requests & httpx) will be monitored")
    print("🎯 [HTTP Monitor] Supports: chat, completions, embeddings, images, audio, moderation")
    print("🔍 [HTTP Monitor] Also monitors: model listings, file operations, fine-tuning")
    
    # PRODUCTION DEBUG: Add a fallback monitor for all HTTP activity
    try:
        import sys
        
        # Create a simple module-level interceptor
        class HTTPInterceptor:
            def __init__(self):
                self.call_count = 0
            
            def log_http_call(self, method, url, *args, **kwargs):
                self.call_count += 1
                if 'openai' in str(url).lower():
                    logger.info(f"🚨 [FALLBACK] HTTP {method} to OpenAI detected: {url}")
                    logger.info(f"🚨 [FALLBACK] Call #{self.call_count}")
                    if kwargs.get('json'):
                        json_data = kwargs['json']
                        if 'messages' in json_data:
                            prompt_size = sum(len(str(msg.get('content', ''))) for msg in json_data.get('messages', []))
                            logger.info(f"🚨 [FALLBACK] Estimated prompt size: {prompt_size} chars")
        
        # Store interceptor globally
        _http_interceptor = HTTPInterceptor()
        
        # Try to intercept at import level
        if 'openai' in sys.modules:
            print("🔍 [DEBUG] OpenAI module already imported - adding runtime hooks")
        
        print("🔍 [DEBUG] HTTP monitoring setup complete with fallback detection")
        
    except Exception as e:
        logger.info(f"⚠️ [DEBUG] Warning during setup: {e}")

def disable_http_monitoring():
    """Disable HTTP request monitoring"""
    print("🔧 [HTTP Monitor] Disabling HTTP request monitoring...")
    
    # Restore original requests methods
    requests.post = _original_post
    requests.get = _original_get
    requests.request = _original_request
    
    # Restore original httpx methods if available
    if httpx is not None and hasattr(httpx, '_original_post'):
        httpx.post = httpx._original_post
        delattr(httpx, '_original_post')
    
    # Restore httpx.Client.post if patched
    if httpx is not None and hasattr(httpx.Client, '_original_post'):
        httpx.Client.post = httpx.Client._original_post
        delattr(httpx.Client, '_original_post')
    
    print("✅ [HTTP Monitor] HTTP monitoring disabled")

# Auto-enable monitoring when imported
if __name__ != "__main__":
    # Auto-enable will be handled by one_line_setup
    pass
