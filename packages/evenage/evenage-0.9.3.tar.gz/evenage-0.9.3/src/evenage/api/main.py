"""
FastAPI server for EvenAge.

Refactored API with:
- New REST endpoints for jobs, agents, traces, metrics
- WebSocket for real-time events (throttled)
- No OTEL/Prometheus (internal observability only)
- Uses new Agent/AgentRunner architecture
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime
import logging
import time
from typing import Any
import json

from evenage import __version__ as pkg_version
from evenage.core import (
    AgentRunner,
    BackendFactory,
    EvenAgeConfig,
    run_agent,
)
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response models
class SubmitJobRequest(BaseModel):
    """Request to submit a new job (legacy)."""
    pipeline_name: str
    inputs: dict[str, Any]


class SubmitPromptRequest(BaseModel):
    """Request to submit a new prompt execution."""
    prompt_name: str
    inputs: dict[str, Any]
    mode: str = "single"  # "single" or "sequential"
    agents: list[str] | None = None  # For sequential mode: ordered list of agents


class CancelPromptResponse(BaseModel):
    ok: bool
    prompt_id: str
    status: str


class ReplayJobRequest(BaseModel):
    """Request to replay a job."""
    reexecute: bool = False


class AgentChatRequest(BaseModel):
    """Request to chat with an agent."""
    message: str
    wait: bool = True
    timeout: int = 30


class AgentInfo(BaseModel):
    """Agent information."""
    name: str
    role: str
    goal: str
    status: str
    tools: list[str]
    last_seen: str | None = None


# Global services
config: EvenAgeConfig
factory: BackendFactory
database: Any
message_bus: Any


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services."""
    global config, factory, database, message_bus

    # Load configuration
    config = EvenAgeConfig()
    factory = BackendFactory(config)

    # Initialize services
    database = factory.create_database_backend()
    message_bus = factory.create_queue_backend()

    # Create database tables
    database.create_tables()

    logger.info("EvenAge API server started")
    logger.info(f"Database: {config.database_url}")
    logger.info(f"Queue: {config.queue_backend}")

    yield

    logger.info("EvenAge API server shutting down")


async def _run_sequential_chain(runner: AgentRunner, agent_names: list[str], inputs: dict, job_id: str) -> dict:
    """
    Run agents sequentially, piping output from one to the next.
    
    Args:
        runner: AgentRunner instance
        agent_names: List of agent names in execution order
        inputs: Initial inputs
        job_id: Job ID to use for all agents in the chain
    
    Returns:
        Final result dict with sequential execution metadata
    """
    current_input = inputs
    last_result = None
    results = []
    
    for agent_name in agent_names:
        try:
            result = await runner.run(current_input, agent_name=agent_name, job_id=job_id)
            
            if result.get("status") == "error":
                return {
                    "status": "error",
                    "error": f"Sequential chain failed at {agent_name}: {result.get('error')}",
                    "agent": agent_name,
                    "results": results
                }
            
            # Extract result for next agent
            last_result = result.get("result", result)
            results.append({
                "agent": agent_name,
                "result": last_result
            })
            
            # Next agent receives previous output
            if isinstance(last_result, dict):
                current_input = last_result
            else:
                current_input = {"input": last_result, "text": str(last_result)}
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Sequential chain failed at {agent_name}: {e}",
                "agent": agent_name,
                "results": results
            }
    
    return {
        "status": "success",
        "result": last_result,
        "mode": "sequential",
        "agents": agent_names,
        "results": results
    }


# Create FastAPI app
app = FastAPI(
    title="EvenAge API",
    description="API for EvenAge distributed agent framework",
    version=pkg_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://dashboard:5173",
        "*",  # Configure appropriately for production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "EvenAge API",
        "version": pkg_version,
        "status": "running",
        "dashboard": "http://localhost:5173",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check message bus
        bus_healthy = await message_bus.health_check()

        # Check database
        db_healthy = True
        try:
            database.get_metrics()
        except Exception:
            db_healthy = False

        if not (bus_healthy and db_healthy):
            raise HTTPException(
                status_code=503,
                detail=f"Services unhealthy: bus={bus_healthy}, db={db_healthy}"
            )

        return {
            "status": "healthy",
            "queue": bus_healthy,
            "database": db_healthy,
            "version": pkg_version,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/jobs")
async def submit_job(request: SubmitJobRequest):
    """
    Submit a new job for execution.

    Creates job, executes agent, stores results and traces.

    Args:
        request: Job submission request

    Returns:
        Job result with job_id, status, result/error
    """
    try:
        result = await run_agent(
            agent_name=request.pipeline_name,
            inputs=request.inputs,
            env_config=config
        )

        return {
            "job_id": result["job_id"],
            "status": result["status"],
            "result": result.get("result"),
            "error": result.get("error"),
            "duration_ms": result.get("duration_ms"),
            "agent": result.get("agent")
        }

    except Exception as e:
        logger.error(f"Error submitting job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """
    Get job status and result.

    Args:
        job_id: Job identifier

    Returns:
        Job information
    """
    try:
        result = database.get_result(job_id)

        if not result:
            raise HTTPException(status_code=404, detail="Job not found")

        # Aggregate token usage
        usage = {}
        try:
            usage = database.get_token_usage(job_id)
        except Exception:
            usage = {}

        return {
            "job_id": job_id,
            "status": result.get("status"),
            "pipeline_name": result.get("pipeline_name"),
            "inputs": result.get("inputs"),
            "outputs": result.get("outputs"),
            "error": result.get("error"),
            "created_at": result.get("created_at"),
            "completed_at": result.get("completed_at"),
            "token_usage": usage,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch job")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
async def list_jobs(limit: int = 50, offset: int = 0):
    """
    List recent jobs.

    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip

    Returns:
        List of jobs
    """
    try:
        # DatabaseService currently supports only limit; offset not implemented
        jobs = database.list_jobs(limit=limit)

        return {
            "jobs": [
                {
                    "job_id": job.get("job_id"),
                    "status": job.get("status"),
                    "pipeline_name": job.get("pipeline_name"),
                    "created_at": job.get("created_at"),
                    "completed_at": job.get("completed_at")
                }
                for job in jobs
            ],
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.exception("Failed to list jobs")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/replay")
async def replay_job(job_id: str, request: ReplayJobRequest):
    """
    Replay a previous job.

    Args:
        job_id: Job identifier
        request: Replay configuration

    Returns:
        Job result (stored or re-executed)
    """
    try:
        runner = AgentRunner(env_config=config)
        result = runner.replay(job_id, reexecute=request.reexecute)

        return result

    except Exception as e:
        logger.exception("Failed to replay job")
        raise HTTPException(status_code=500, detail=str(e))


# --- New Prompt Endpoints (preferred terminology) ---

@app.post("/api/prompts")
async def submit_prompt(request: SubmitPromptRequest):
    """
    Submit a new prompt execution (non-blocking).

    - Creates a prompt record immediately
    - Kicks off background agent execution using the same prompt_id as job_id
    - Returns promptly with status 'running' and the prompt_id
    - Supports sequential mode: runs multiple agents in order, piping output
    """
    try:
        # Create prompt record first and mark as running
        prompt_id = database.create_prompt(None, request.prompt_name, request.inputs)
        database.update_prompt_status(prompt_id, "running")

        async def _run_in_background(pid: str):
            try:
                runner = AgentRunner(env_config=config)
                
                # Sequential mode: run multiple agents in order
                if request.mode == "sequential" and request.agents and len(request.agents) > 1:
                    result = await _run_sequential_chain(runner, request.agents, request.inputs, pid)
                else:
                    # Single agent mode (default)
                    # For single-mode prompt executions initiated from the API UI,
                    # disable delegation for non-coordinator agents to prevent unwanted
                    # cross-agent delegation (e.g., researcher delegating to coordinator).
                    # However, allow delegation if the user is directly prompting the
                    # coordinator, since delegation is the coordinator's primary function.
                    inputs_for_run = dict(request.inputs or {})
                    
                    # Only disable delegation if NOT prompting the coordinator
                    if request.prompt_name != "coordinator":
                        inputs_for_run["_allow_delegation"] = False

                    result = await runner.run(
                        inputs=inputs_for_run,
                        agent_name=request.prompt_name,
                        job_id=pid,
                    )

                # Map status to prompt status
                status = result.get("status", "failed")
                outputs = result.get("result") or {}
                error = result.get("error")

                # Prefer explicit outputs; if only error present, store that
                if error and not outputs:
                    outputs = {"error": error}

                # Normalize success to 'completed'
                prompt_status = "completed" if status == "success" else status
                database.save_prompt_result(pid, outputs, status=prompt_status)
            except Exception as e:
                logger.exception("Background prompt run failed")
                database.save_prompt_result(pid, {"error": str(e)}, status="failed")

        # Fire-and-forget background task
        asyncio.create_task(_run_in_background(prompt_id))

        return {
            "prompt_id": prompt_id,
            "status": "running",
            "agent": request.prompt_name,
            "mode": request.mode,
            "agents": request.agents if request.mode == "sequential" else [request.prompt_name]
        }

    except Exception as e:
        logger.error(f"Error submitting prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    """
    Get prompt execution status and result.

    Args:
        prompt_id: Prompt execution identifier

    Returns:
        Prompt information
    """
    try:
        result = database.get_prompt_result(prompt_id)

        if not result:
            raise HTTPException(status_code=404, detail="Prompt execution not found")

        # Aggregate token usage for this prompt/job
        usage = {}
        try:
            usage = database.get_token_usage(prompt_id)
        except Exception:
            usage = {}

        return {
            "prompt_id": prompt_id,
            "status": result.get("status"),
            "prompt_name": result.get("prompt_name"),
            "inputs": result.get("inputs"),
            "outputs": result.get("outputs"),
            "error": result.get("error"),
            "created_at": result.get("created_at"),
            "completed_at": result.get("completed_at"),
            "token_usage": usage,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch prompt")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompts")
async def list_prompts(limit: int = 50):
    """
    List recent prompt executions.

    Args:
        limit: Maximum number of prompts to return

    Returns:
        List of prompt executions
    """
    try:
        prompts = database.list_prompts(limit=limit)

        return {
            "prompts": [
                {
                    "prompt_id": prompt.get("prompt_id"),
                    "status": prompt.get("status"),
                    "prompt_name": prompt.get("prompt_name"),
                    "created_at": prompt.get("created_at"),
                    "completed_at": prompt.get("completed_at")
                }
                for prompt in prompts
            ],
            "limit": limit
        }

    except Exception as e:
        logger.exception("Failed to list prompts")
        raise HTTPException(status_code=500, detail=str(e))


# --- Legacy Job Endpoints (backward compatibility) ---

@app.get("/api/agents")
async def list_agents():
    """
    List registered agents.

    Returns:
        List of agents with metadata
    """
    try:
        # Query database for agent metadata (registered by workers)
        agents_list = database.list_agents()

        return {
            "agents": [
                AgentInfo(
                    name=agent["agent_name"],
                    role=agent["metadata"].get("role", "unknown"),
                    goal=agent["metadata"].get("goal", ""),
                    status=agent["metadata"].get("status", "unknown"),
                    tools=agent["metadata"].get("tools", []),
                    last_seen=agent.get("last_seen")
                ).dict()
                for agent in agents_list
            ]
        }

    except Exception as e:
        logger.exception("Failed to list agents")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/{agent_name}/chat")
async def chat_with_agent(agent_name: str, request: AgentChatRequest):
    """
    Send a message to an agent.

    Args:
        agent_name: Agent name
        request: Chat request with message

    Returns:
        Agent response or task_id
    """
    try:
        # Publish task
        task_id = await message_bus.publish_task(
            agent_name,
            {"message": request.message}
        )

        if request.wait:
            # Wait for response
            # Message bus expects positional timeout in seconds (timeout_sec)
            response = await message_bus.wait_for_response(
                task_id,
                request.timeout
            )

            if response:
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "response": response
                }
            return {
                "task_id": task_id,
                "status": "timeout",
                "message": "Agent did not respond in time"
            }
        # Return task_id immediately
        return {
            "task_id": task_id,
            "status": "submitted"
        }

    except Exception as e:
        logger.exception("Failed to chat with agent")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/responses/{task_id}/resolved")
async def get_resolved_response(task_id: str):
    """
    Resolve and return a task response. If the response was offloaded to storage,
    this endpoint fetches the full payload from MinIO/S3 and returns it.

    Args:
        task_id: Task identifier as returned by delegation/chat APIs

    Returns:
        JSON object containing either the inline response or the resolved payload
        when the response was offloaded. Shape:
        {
          "task_id": str,
          "offloaded": bool,
          "pointer": {"bucket": str, "key": str, "size_bytes": int} | None,
          "data": Any  # full response payload
        }
    """
    try:
        # Try to read existing response without blocking
        response: dict | None = None

        # MemoryBus fast-path
        if hasattr(message_bus, "_responses"):
            try:
                response = getattr(message_bus, "_responses", {}).get(task_id)
            except Exception:
                response = None

        # RedisBus path: read key directly to avoid pub/sub
        if response is None and hasattr(message_bus, "_get_client"):
            try:
                client = await message_bus._get_client()  # type: ignore[attr-defined]
                raw = await client.get(f"evenage:response:{task_id}")
                if raw:
                    response = json.loads(raw)
            except Exception:
                response = None

        # Fallback minimal wait
        if response is None:
            with suppress(Exception):
                response = await message_bus.wait_for_response(task_id, 1)

        if not response:
            raise HTTPException(status_code=404, detail="Response not found or expired")

        # If it's a pointer to offloaded content, fetch and return full data
        if isinstance(response, dict) and response.get("offloaded") and response.get("bucket") and response.get("key"):
            bucket = response.get("bucket")
            key = response.get("key")

            storage = factory.create_storage_backend()
            try:
                blob = await storage.get_object(bucket, key)
                try:
                    data = json.loads(blob.decode("utf-8"))
                except Exception:
                    # Return raw text if not valid JSON
                    data = blob.decode("utf-8", errors="replace")
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Failed to fetch offloaded artifact: {e}")

            return {
                "task_id": task_id,
                "offloaded": True,
                "pointer": {
                    "bucket": bucket,
                    "key": key,
                    "size_bytes": response.get("size_bytes")
                },
                "data": data
            }

        # Inline payload already present
        return {
            "task_id": task_id,
            "offloaded": False,
            "pointer": None,
            "data": response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to resolve response")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/traces")
async def list_traces(
    job_id: str | None = None,
    agent_name: str | None = None,
    limit: int = 100,
):
    """List trace events with optional filters and include payload."""
    try:
        if job_id:
            traces = database.get_job_traces(job_id)
        else:
            traces = database.list_traces(agent=agent_name, limit=limit)

        return {"traces": traces}

    except Exception as e:
        logger.exception("Failed to list traces")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/traces/grouped")
async def get_grouped_traces(limit: int = 50):
    """
    Get traces grouped by job_id.
    
    Returns traces organized by job_id, showing complete multi-agent runs together.
    Each group contains all traces (coordinator, researcher, etc.) for that job.
    """
    try:
        # Get recent traces with job_id
        all_traces = database.list_traces(limit=limit * 10)  # Get more to ensure we have enough jobs
        
        # Group traces by job_id
        grouped: dict[str, list] = {}
        for trace in all_traces:
            job_id = trace.get('job_id')
            if job_id:
                if job_id not in grouped:
                    grouped[job_id] = []
                grouped[job_id].append(trace)
        
        # Convert to list format with metadata
        result = []
        for job_id, traces in list(grouped.items())[:limit]:
            # Sort traces by timestamp
            traces.sort(key=lambda t: t.get('timestamp', ''))
            
            # Extract metadata
            agents = list(set(t.get('agent_name') for t in traces if t.get('agent_name')))
            start_time = traces[0].get('timestamp') if traces else None
            end_time = traces[-1].get('timestamp') if traces else None
            
            result.append({
                'job_id': job_id,
                'trace_count': len(traces),
                'agents': agents,
                'start_time': start_time,
                'end_time': end_time,
                'traces': traces
            })
        
        # Sort by most recent first
        result.sort(key=lambda g: g.get('start_time', ''), reverse=True)
        
        return {'grouped_traces': result}
        
    except Exception as e:
        logger.exception("Failed to get grouped traces")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get a single trace by id with full payload."""
    try:
        trace = database.get_trace(trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        return trace
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get trace")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
async def get_metrics():
    """
    Get system metrics.

    Returns:
        Aggregated metrics from traces and jobs
    """
    try:
        metrics = database.get_metrics()

        return {
            "total_jobs": metrics.get("total_jobs", 0),
            "avg_latency_ms": metrics.get("avg_latency_ms", 0),
            "active_agents_count": metrics.get("active_agents_count", 0),
            "cache_hits": metrics.get("cache_hits", 0),
            "tool_calls": metrics.get("tool_calls", 0),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.exception("Failed to get metrics")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for real-time events (throttled)
class EventThrottler:
    """Throttle WebSocket events to avoid overwhelming clients."""

    def __init__(self, max_per_second: int = 10):
        self.max_per_second = max_per_second
        self.last_sent = 0.0
        self.buffer: list[dict] = []

    def add(self, event: dict) -> dict | None:
        """Add event, return it if should be sent immediately."""
        now = time.time()
        elapsed = now - self.last_sent

        if elapsed >= (1.0 / self.max_per_second):
            self.last_sent = now
            return event
        # Buffer for batching
        self.buffer.append(event)
        if len(self.buffer) >= 5:  # Batch size
            batch = self.buffer[:]
            self.buffer.clear()
            self.last_sent = now
            return {"type": "batch", "events": batch}

        return None


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time events.

    Streams job submissions, completions, trace events with throttling.
    """
    await websocket.accept()
    throttler = EventThrottler(max_per_second=10)

    try:
        while True:
            # Poll for recent traces (last 5 seconds)
            traces = database.list_traces(limit=20)
            recent: list[dict] = []
            now = datetime.utcnow()
            for t in traces:
                ts = t.get("timestamp")
                if not ts:
                    continue
                try:
                    # Support ISO strings
                    ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                    if (now - ts_dt).total_seconds() < 5:
                        recent.append(t)
                except Exception:
                    continue

            for trace in recent:
                event = {
                    "type": "trace",
                    "data": {
                        "job_id": trace.get("job_id"),
                        "agent_name": trace.get("agent_name"),
                        "event_type": trace.get("event_type"),
                        "timestamp": trace.get("timestamp")
                    }
                }

                to_send = throttler.add(event)
                if to_send:
                    await websocket.send_json(to_send)

            # Sleep before next poll
            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@app.websocket("/ws/prompts/{prompt_id}")
async def websocket_prompt_traces(websocket: WebSocket, prompt_id: str):
    """
    WebSocket endpoint for live trace streaming for a specific prompt execution.
    
    Clients connect when starting a prompt and receive real-time traces
    as they are generated during execution.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for prompt {prompt_id}")
    
    # Track last seen trace timestamp to avoid duplicates (use timestamp-based filtering to
    # avoid races where autoincrement id ordering differs from timestamps). Fall back to
    # last_trace_id when timestamps are missing.
    last_seen_ts: datetime | None = None
    last_trace_id = 0
    # Track open delegation windows to annotate child traces with parent_trace_id
    # Shape: { parent_trace_id: { 'agent': str|None, 'start': datetime, 'end': datetime|None } }
    open_delegations: dict[int, dict[str, Any]] = {}

    def _parse_ts(ts: str | None) -> datetime | None:
        if not ts:
            return None
        try:
            # Support "Z" timezone by replacing with +00:00 for fromisoformat
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None
    
    try:
        while True:
            # Get traces for this prompt/job
            traces = database.get_job_traces(prompt_id)
            
            # Filter to only new traces using timestamp-based comparison when possible.
            parsed_traces = []
            for t in traces:
                ts = _parse_ts(t.get('timestamp'))
                parsed_traces.append((t, ts))

            if last_seen_ts is None:
                # First time: send all traces
                new_traces = [t for t, _ in parsed_traces]
            else:
                # Send traces whose timestamp is greater than last_seen_ts
                new_traces = [t for t, ts in parsed_traces if ts is not None and ts > last_seen_ts]

            # Fallback: if no timestamps available or no new traces found, use id-based filtering
            if not new_traces:
                new_traces = [t for t in traces if t.get('id', 0) > last_trace_id]

            if new_traces:
                # Update last seen timestamp and id conservatively
                max_ts = None
                for t in new_traces:
                    ts = _parse_ts(t.get('timestamp'))
                    if ts and (max_ts is None or ts > max_ts):
                        max_ts = ts
                if max_ts:
                    last_seen_ts = max_ts
                last_trace_id = max(last_trace_id, max(t.get('id', 0) for t in new_traces))
                
                # Send new traces
                for trace in new_traces:
                    # Heuristically detect delegation start/end to annotate children
                    try:
                        event_type = trace.get('event_type')
                        payload = trace.get('payload') or {}
                        tool_name = (payload.get('tool') or '').lower()

                        # Delegation start (detect both system tool-based delegation and custom delegation events)
                        if (event_type == 'tool_call' and tool_name in {
                            'delegate_parallel', 'system_delegate_parallel',
                            'delegate_task', 'system_delegate_task'
                        }) or event_type == 'delegation':
                            parent_id = trace.get('id')
                            params = payload.get('params') or {}
                            # For custom delegation traces the payload may use different keys
                            delegated_agent = (
                                params.get('agent')
                                or params.get('agent_name')
                                or payload.get('target_agent')
                                or payload.get('delegated_agent')
                                or payload.get('agent')
                            )
                            open_delegations[int(parent_id)] = {
                                'agent': delegated_agent,
                                'start': _parse_ts(trace.get('timestamp')),
                                'end': None,
                            }

                        # Delegation end (close the most recent open window if any)
                        if event_type == 'tool_result' and tool_name in {
                            'delegate_parallel', 'system_delegate_parallel',
                            'delegate_task', 'system_delegate_task'
                        }:
                            end_ts = _parse_ts(trace.get('timestamp'))
                            # Close all open windows that have no end yet (handles overlapping conservatively)
                            for k, v in list(open_delegations.items()):
                                if v.get('end') is None:
                                    v['end'] = end_ts
                                    open_delegations[k] = v

                        # Annotate child traces that belong to an open delegation window
                        if event_type not in {'tool_call', 'tool_result'}:
                            t_ts = _parse_ts(trace.get('timestamp'))
                            agent_name = trace.get('agent_name')
                            parent_to_use: int | None = None
                            for pid, window in open_delegations.items():
                                if window.get('agent') and agent_name == window['agent']:
                                    start_ok = (window.get('start') is None) or (t_ts and window['start'] and t_ts >= window['start'])
                                    end_ok = (window.get('end') is None) or (t_ts and window['end'] and t_ts <= window['end'])
                                    if start_ok and end_ok:
                                        parent_to_use = pid
                                        break
                            if parent_to_use is not None:
                                # Attach parent_trace_id for the UI to nest this event
                                trace = {**trace, 'parent_trace_id': parent_to_use}
                    except Exception:
                        # Best-effort enrichment; never break the stream
                        pass

                    await websocket.send_json({
                        "type": "trace",
                        "data": trace
                    })
            
            # Check if prompt is complete
            prompt_result = database.get_prompt_result(prompt_id)
            if prompt_result and prompt_result.get('status') in ['completed', 'failed', 'error', 'canceled']:
                # Send completion event
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "status": prompt_result.get('status'),
                        "outputs": prompt_result.get('outputs'),
                        "error": prompt_result.get('error')
                    }
                })
                logger.info(f"Prompt {prompt_id} completed, closing WebSocket")
                break
            
            # Poll interval
            await asyncio.sleep(0.3)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for prompt {prompt_id}")
    except Exception as e:
        logger.error(f"WebSocket error for prompt {prompt_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"error": str(e)}
            })
        except:
            pass


    @app.post("/api/prompts/{prompt_id}/cancel", response_model=CancelPromptResponse)
    async def cancel_prompt(prompt_id: str):
        """Request cancellation of a running prompt. This sets a cancel flag and updates status."""
        try:
            # Signal cancel to runtime via message bus
            with suppress(Exception):
                # message_bus may not implement cancel in all backends; best-effort
                await message_bus.cancel_job(prompt_id)

            # Update prompt status to canceled
            database.update_prompt_status(prompt_id, "canceled")
            # Trace cancel request
            try:
                database.append_trace(prompt_id, "api", "task_cancel_requested", {"by": "user"})
            except Exception:
                pass

            return CancelPromptResponse(ok=True, prompt_id=prompt_id, status="canceled")
        except Exception as e:
            logger.exception("Failed to cancel prompt")
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
