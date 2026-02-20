# HELM Runbook

## Deploying New Tool Executors

1. **Add Intent Scope**
   - Update `orchestration/intent.py` with your new canonical Intent name.
   - Describe required entities that must be parsed (e.g., `"purchase"` needs `"target_amount"`).

2. **Implement an Executor**
   - Create `backend/<domain>/executor.py`. Must implement `async def execute(entities, ...)` returning structured JSON.
   - Fail gracefully. Do not raise uncaught 500 exceptions if a dependent service drops.
   
3. **Map the Route**
   - In `orchestration/router.py`, instantiate your Executor and map it to the Intent namespace.

4. **Verify Composition Format**
   - Modify `orchestration/response.py` handling to provide clean, unified UI summaries based on `tool_data`.

5. **Local Testing**
   - Submit a direct payload to `http://localhost:8080/history/generate` matching your tool schema.
   - Monitor `backend/debug_history.log` for execution latencies.
