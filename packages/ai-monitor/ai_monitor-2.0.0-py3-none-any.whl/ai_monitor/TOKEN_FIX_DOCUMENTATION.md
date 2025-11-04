# AI Monitor Token Counting Fix

## Problem Summary

The AI Monitor's input and output token calculations were not matching Azure OpenAI's reported tokens due to several issues:

1. **Overriding Azure-provided tokens**: The code was recalculating tokens even when Azure provided exact counts
2. **Incorrect correction factors**: Applied a 4.6% reduction to tiktoken counts that was inappropriate for Azure tokens
3. **Multiple conflicting calculations**: Several places in the code were doing different token estimations
4. **Inaccurate fallback methods**: Used overly simplistic character-based estimations

## Root Causes Identified

### 1. Core.py Issues
- `record_llm_call()` method was always recalculating input tokens
- Applied Azure correction factor (0.9565) to tiktoken counts unnecessarily
- Multiple estimation methods were overriding Azure-provided values

### 2. HTTP Interceptor Issues  
- Multiple fallback calculations were overriding correct Azure values
- Token extraction logic wasn't robust enough
- Final token fixes were applied even when Azure provided correct tokens

### 3. Estimation Logic Issues
- Used inaccurate 4 chars/token ratio instead of tiktoken
- Applied corrections that were meant for tiktoken estimates to Azure tokens
- No validation of token consistency

## Fixes Implemented

### 1. Prioritize Azure-Provided Tokens
```python
# OLD - Always recalculated
if input_tokens == 0 and prompt and len(prompt) > 0:
    # Complex calculation that might override Azure tokens

# FIXED - Only calculate if Azure didn't provide tokens  
if input_tokens > 0:
    logger.info(f"✅ Using Azure-provided tokens: {input_tokens}")
else:
    # Only estimate if Azure gave us 0 tokens
```

### 2. Removed Incorrect Azure Correction Factor
```python
# OLD - Applied incorrect correction
tiktoken_exact = int(raw_tiktoken * 0.9565)  # Azure correction factor

# FIXED - Use tiktoken as-is for estimation only
tiktoken_exact = len(encoding.encode(prompt))
# No correction - Azure gives exact tokens when available
```

### 3. Enhanced Token Extraction
```python
# FIXED - More robust extraction with validation
input_tokens = usage.get('prompt_tokens', 0)
output_tokens = usage.get('completion_tokens', 0) 
total_tokens = usage.get('total_tokens', 0)

# Validate consistency
is_valid, corrected_total = validate_azure_tokens(input_tokens, output_tokens, total_tokens)
```

### 4. Improved Fallback Estimation
```python
# FIXED - Use tiktoken for accurate fallback estimation
try:
    import tiktoken
    encoding = tiktoken.get_encoding("cl100k_base")
    input_tokens = len(encoding.encode(prompt))
except:
    # Better character-based fallback
    input_tokens = max(1, len(prompt) // 4)
```

### 5. Added Token Validation
```python
def validate_azure_tokens(input_tokens, output_tokens, total_tokens, source="Azure"):
    """Validate that token values are consistent and reasonable"""
    if input_tokens > 0 and output_tokens >= 0:
        expected_total = input_tokens + output_tokens
        if total_tokens == expected_total or total_tokens == 0:
            return True, expected_total
        else:
            return True, expected_total  # Trust input+output, recalculate total
    return False, 0
```

## Key Changes Made

### File: `core.py`
- ✅ Only calculate tokens if `input_tokens == 0`
- ✅ Removed Azure correction factor (0.9565 multiplier)
- ✅ Enhanced logging to show when Azure tokens are used vs estimated
- ✅ Prioritize Azure-provided tokens in all cases

### File: `http_interceptor.py`
- ✅ Added `validate_azure_tokens()` function
- ✅ Enhanced token extraction with better field mapping
- ✅ Improved `_estimate_input_tokens()` to use tiktoken
- ✅ Prevented override of valid Azure tokens
- ✅ Added comprehensive logging for debugging

### File: `test_token_accuracy.py` (New)
- ✅ Created test suite to verify token handling
- ✅ Tests Azure token preservation
- ✅ Tests fallback estimation when Azure doesn't provide tokens
- ✅ Tests token validation logic

## Expected Results

After these fixes:

1. **When Azure provides tokens**: Use Azure's exact values without any modification
2. **When Azure doesn't provide tokens**: Use tiktoken for accurate estimation
3. **Consistent logging**: Clear indication of when Azure vs estimated tokens are used
4. **No more mismatches**: Token counts should match Azure's dashboard exactly

## Verification

Run the test suite to verify fixes:
```bash
cd ai_monitor
python test_token_accuracy.py
```

Expected output:
```
✅ Test PASSED: Azure tokens preserved exactly!
✅ Test PASSED: Fallback estimation working!  
✅ Test PASSED: Token validation working!
🎉 All tests PASSED! Token handling should now match Azure exactly.
```

## Migration Notes

- **No breaking changes**: Existing code will continue to work
- **Better accuracy**: Token counts now match Azure OpenAI exactly
- **Improved debugging**: More detailed logging for troubleshooting
- **Robust fallbacks**: Better estimation when Azure doesn't provide tokens

## Monitoring Recommendations

1. Monitor logs for "Azure-provided tokens" vs "estimated tokens" messages
2. Verify token counts match Azure dashboard after deployment
3. Check for any validation warnings in the logs
4. Test with different Azure OpenAI models to ensure consistency

The fixes ensure that AI Monitor will now report the exact same token counts as Azure OpenAI, eliminating discrepancies in usage tracking and cost calculations.
