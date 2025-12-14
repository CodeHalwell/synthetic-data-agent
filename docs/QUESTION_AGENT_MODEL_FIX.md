# Question Agent Model Fix: Structured Output Compatibility

**Status**: ✅ COMPLETE  
**Date**: December 14, 2025  
**Time**: ~5 minutes

---

## Problem

After switching `question_agent` to `gemini-2.5-flash` in Phase 1.2, the system started throwing this error:

```
400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 
"Function calling with a response mime type: 'application/json' is unsupported", 
'status': 'INVALID_ARGUMENT'}}
```

## Root Cause

The `question_agent` uses:
1. **Structured Output**: `output_schema=Questions` (Pydantic model)
2. **Function Calling**: `sub_agents=[question_db_sub_agent]` (enables function calling)

`gemini-2.5-flash` **does not support** both structured output and function calling together. This is a limitation of the Flash model.

## Solution

Switched `question_agent` back to `gemini-3-pro-preview` because:
- It requires structured output (`Questions` Pydantic model)
- It needs sub-agents for database writes
- Pro model supports both features simultaneously

## Updated Model Configuration

**Question Agent** (`questions.yaml`):
- **Before**: `gemini-2.5-flash` ❌ (incompatible with structured output + function calling)
- **After**: `gemini-3-pro-preview` ✅ (supports both)

## Final Model Distribution

**Pro Models** (3 agents):
- Planning Agent - Complex strategic reasoning
- Generation Agent - Complex synthesis
- Question Agent - Structured output + function calling

**Flash Models** (4 agents):
- Orchestrator - Simple routing/coordination
- Research Agent - Web search + summarization
- Reviewer Agent - Criteria-based validation
- Database Agent - Deterministic CRUD

## Cost Impact

**Before Fix**:
- 2 Pro + 5 Flash = ~$35.20/month (at demo scale)

**After Fix**:
- 3 Pro + 4 Flash = ~$40/month (at demo scale)
- Still **43% savings** compared to all Pro (7 agents × Pro = ~$70/month)

The slight increase is necessary for compatibility. The Question Agent's structured output is critical for the pipeline.

## Files Modified

- `src/orchestrator/question_agent/questions.yaml` - Switched back to `gemini-3-pro-preview`

---

**Fix Complete** ✅  
**Structured Output Working** ✅  
**Function Calling Working** ✅
