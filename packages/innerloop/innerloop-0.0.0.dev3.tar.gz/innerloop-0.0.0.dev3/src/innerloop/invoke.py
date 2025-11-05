from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import AsyncIterator
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ValidationError

from .config import InvokeConfig
from .events import ErrorEvent, OpenCodeEvent, TimeInfo
from .events import parse_event as _parse_event
from .helper import unix_ms
from .mcp import LocalMcpServer, McpServer, RemoteMcpServer
from .output import assemble_output
from .permissions import Permission
from .providers import ProviderConfig
from .request import Request
from .response import Response
from .structured import _extract_and_parse_json, build_structured_prompt
from .usage import compute_usage

P = TypeVar("P", bound=BaseModel)


def write_config_file(cfg: InvokeConfig) -> str:
    """Write config JSON to a secure temp file and return its path."""
    data = cfg.to_json().encode("utf-8")
    fd, path = tempfile.mkstemp(prefix="opencode-config-", suffix=".json")
    try:
        try:
            os.fchmod(fd, 0o600)
        except Exception:
            try:
                os.chmod(path, 0o600)
            except Exception:
                pass
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        return path
    except Exception:
        try:
            os.close(fd)
        except Exception:
            pass
        raise


def build_env_with_config_path(
    config_path: str, base: dict[str, str] | None = None
) -> dict[str, str]:
    """Return env dict with OPENCODE_CONFIG_PATH pointing to the temp file."""
    env = dict(base or os.environ)
    env["OPENCODE_CONFIG_PATH"] = config_path
    # Also provide inline content for CLIs that prefer OPENCODE_CONFIG_CONTENT.
    # Harmless if ignored; keeps compatibility across versions.
    # The caller may still override this later if needed.
    # Enable MCP features in CLI builds that gate the functionality.
    env.setdefault("OPENCODE_EXPERIMENTAL_MCP", "1")
    return env


def build_opencode_cmd(
    prompt: str, model: str, session_id: str | None = None
) -> list[str]:
    cmd = ["opencode", "run", "--format", "json", "--model", model]
    if session_id:
        cmd += ["--session", session_id]
    cmd.append(prompt)
    return cmd


async def run_opencode_jsonl(
    prompt: str,
    *,
    model: str,
    permission: Permission,
    providers: dict[str, ProviderConfig] | None = None,
    mcp_servers: list[McpServer] | dict[str, McpServer] | None = None,
    session_id: str | None = None,
    cwd: str | None = None,
    timeout: float | None = None,
    chunk_size: int = 8192,
) -> AsyncIterator[dict[str, Any]]:
    """
    Pure functional runner: build config -> write file -> run -> JSONL stream.
    Yields parsed JSON objects from the CLI, one per line.
    Minimal guardrails here; callers can layer policies as needed.
    """
    typed_mcp = cast(
        dict[str, LocalMcpServer | RemoteMcpServer] | None, mcp_servers
    )
    # Note: Request.providers (plural, user-facing) maps to InvokeConfig.provider
    # (singular) because the CLI schema uses a single top-level "provider" object.
    # Keep naming as-is to avoid API churn.
    cfg = InvokeConfig(
        permission=permission, provider=providers, mcp=typed_mcp
    )
    config_path = write_config_file(cfg)
    env = build_env_with_config_path(config_path)
    # Provide content alongside path to satisfy CLIs that read only CONTENT.
    env["OPENCODE_CONFIG_CONTENT"] = cfg.to_json()
    cmd = build_opencode_cmd(prompt, model, session_id=session_id)

    # Delegate to the generic process streamer for robust handling
    from .proc import stream_jsonl_process as _stream

    try:
        async for obj in _stream(
            cmd,
            env=env,
            cwd=cwd,
            timeout=timeout,
            chunk_size=chunk_size,
        ):
            yield obj
    finally:
        # Best‑effort cleanup of the temp config file in all code paths
        try:
            os.unlink(config_path)
        except Exception:
            pass


async def async_invoke(
    request: Request,
    *,
    resume: str | None = None,
) -> Response[Any]:
    """Run a single CLI invocation and return a typed Response.

    - resume: optional session id to continue
    Structured parsing and retries live in `async_invoke_structured`/`Loop.run`
    and are not applied here.
    """
    # Always stream and assemble raw text here; structured parsing and retries
    # are handled by async_invoke_structured.
    effective_session = resume or request.session
    if effective_session == "":
        effective_session = None
    prompt = request.prompt

    # Stream events
    events: list[OpenCodeEvent] = []
    response_session: str | None = effective_session

    wall_start = unix_ms()
    async for raw in run_opencode_jsonl(
        prompt,
        model=request.model,
        permission=request.permission,
        providers=request.providers,
        mcp_servers=cast(
            dict[str, McpServer] | list[McpServer] | None, request.mcp
        ),
        session_id=effective_session,
        cwd=request.workdir,
        timeout=request.timeout,
    ):
        ev = _parse_event(raw)
        ev.seq = len(events) + 1
        events.append(ev)
        if response_session is None:
            try:
                response_session = ev.sessionID or None
            except Exception:
                pass
    wall_end = unix_ms()

    # Build output
    text = assemble_output(events, reset_on_tool=True, fallback_to_tool=True)
    out: Any = text

    resp: Response[Any] = Response(
        session_id=response_session or "",
        input=request.prompt,
        output=out,
        events=events,
        time=TimeInfo(start=wall_start, end=wall_end),
    )

    # Populate usage once based on events
    resp.usage = compute_usage(events)
    return resp


def invoke(
    request: Request,
    *,
    resume: str | None = None,
) -> Response[Any]:
    """Synchronous wrapper around async_invoke."""
    return asyncio.run(async_invoke(request, resume=resume))


__all__ = [
    # helpers
    "InvokeConfig",
    "write_config_file",
    "build_env_with_config_path",
    "build_opencode_cmd",
    "run_opencode_jsonl",
    "Request",
    "async_invoke",
    "invoke",
]


async def async_invoke_structured(
    request: Request,
    *,
    max_retries: int = 2,
) -> Response[Any]:
    """Structured invoke with local validation retries.

    Builds a structured prompt, performs attempts until validation succeeds
    or retry budget exhausts. Aggregates events; returns a single Response.
    """
    # Build structured prompt
    if request.response_format is None:
        # If no format provided, delegate to async_invoke
        return await async_invoke(request)

    base_prompt = build_structured_prompt(
        request.prompt, request.response_format
    )
    current_prompt = base_prompt
    attempts_used = 0

    total_events: list[OpenCodeEvent] = []
    final_session: str | None = request.session
    final_output_text = ""
    final_output: Any | None = None

    wall_start = unix_ms()
    while True:
        attempts_used += 1
        # One attempt without schema parsing to detect validation errors locally
        req = Request(
            model=request.model,
            prompt=current_prompt,
            permission=request.permission,
            providers=request.providers,
            mcp=request.mcp,
            response_format=None,
            session=final_session,
            workdir=request.workdir,
            timeout=request.timeout,
        )
        resp = await async_invoke(req)
        total_events.extend(resp.events)
        final_session = resp.session_id
        final_output_text = str(resp.output)

        try:
            parsed = _extract_and_parse_json(
                final_output_text, request.response_format
            )
            final_output = parsed
            break
        except (ValidationError, ValueError) as ve:
            err_ev = ErrorEvent(
                timestamp=unix_ms(),
                sessionID=final_session or "",
                type="error",
                message=str(ve),
                code=None,
                severity="error",
            )
            total_events.append(err_ev)
            if attempts_used > max_retries:
                raise RuntimeError(
                    f"Structured output validation failed after {attempts_used} attempts: {ve}"
                ) from ve
            # corrective prompt
            current_prompt = (
                f"{base_prompt}\n\n"
                "Your previous JSON failed validation.\n"
                f"Error: {str(ve)}\n"
                "Please return ONLY a corrected JSON object that satisfies the schema."
            )

    wall_end = unix_ms()
    assert final_output is not None
    out_resp: Response[Any] = Response(
        session_id=final_session or "",
        input=request.prompt,
        output=final_output,
        events=total_events,
        time=TimeInfo(start=wall_start, end=wall_end),
    )
    out_resp.attempts = attempts_used
    out_resp.usage = compute_usage(total_events)
    return out_resp
