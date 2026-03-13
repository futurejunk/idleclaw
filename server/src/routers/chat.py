from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from server.src.models.chat import ChatRequest
from server.src.services.node_connection import create_request_queue, remove_request_queue
from server.src.services.ollama_params import build_ollama_params
from server.src.services.router import RequestRouter
from server.src.services.tool_execution import execute_tool_calls
from server.src.services.tool_parser import ContentTagStripper, parse_tool_calls, strip_tool_tags
from server.src.services.tool_registry import tool_registry
from server.src.services.content_filter import ContentFilter
from server.src.config import settings

logger = logging.getLogger(__name__)

content_filter = ContentFilter(settings.inbound_blocklist, settings.outbound_blocklist)

router = APIRouter()

REQUEST_TIMEOUT = 60  # seconds
MAX_TOOL_ROUNDS = 5
MAX_TOTAL_PAYLOAD_CHARS = 100_000


@router.post("/api/chat")
async def chat(request: ChatRequest):
    from server.src.main import registry, request_queues, request_node_map, stats

    # Payload size validation
    total_chars = sum(len(m.content) for m in request.messages)
    if total_chars > MAX_TOTAL_PAYLOAD_CHARS:
        raise HTTPException(status_code=422, detail=f"Total payload too large: {total_chars} chars (max {MAX_TOTAL_PAYLOAD_CHARS})")

    # Content filter: check inbound messages
    messages_raw = [{"role": m.role, "content": m.content} for m in request.messages]
    blocked_pattern = content_filter.check_inbound(messages_raw)
    if blocked_pattern:
        raise HTTPException(status_code=400, detail="Message content not allowed")

    # Find the best node for the requested model
    node = RequestRouter.select_node(registry, request.model)
    if node is None:
        raise HTTPException(status_code=503, detail=f"No nodes available with model {request.model}")

    request_id = str(uuid.uuid4())
    request_start = time.monotonic()
    stats.requests_active += 1
    logger.info("Inference request started", extra={"request_id": request_id, "model": request.model, "node_id": node.node_id})
    queue = create_request_queue(request_queues, request_node_map, request_id, node.node_id)

    capabilities = node.get_model_capabilities(request.model)
    supports_native_tools = capabilities.get("tool_calls", False)

    # Build initial ollama_params with tools
    ollama_params = build_ollama_params(request, node, tool_registry)
    tools_offered = "tools" in ollama_params or (
        not tool_registry.is_empty() and not supports_native_tools
    )
    await node.websocket.send_text(json.dumps({
        "type": "inference_request",
        "request_id": request_id,
        "ollama_params": ollama_params,
    }))
    node.active_requests += 1

    chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    async def event_generator():
        nonlocal ollama_params, request_id, queue
        tool_round = 0
        request_error: str | None = None
        tag_stripper = ContentTagStripper()

        try:
            while True:
                # Accumulate the full response for tool call detection
                accumulated_content = ""
                done_message = None

                # Stream chunks from the node
                while True:
                    try:
                        msg = await asyncio.wait_for(queue.get(), timeout=REQUEST_TIMEOUT)
                    except asyncio.TimeoutError:
                        request_error = "timeout"
                        registry.adjust_reputation(node.node_id, -0.05)
                        error_chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": request.model,
                            "choices": [{"delta": {"content": "\n\n[Error: request timed out]"}, "index": 0}],
                        }
                        yield {"data": json.dumps(error_chunk)}
                        yield {"data": "[DONE]"}
                        return

                    if msg["type"] == "inference_error":
                        request_error = msg.get("error", "unknown")
                        registry.adjust_reputation(node.node_id, -0.05)
                        error_chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": request.model,
                            "choices": [{"delta": {"content": f"\n\n[Error: {msg.get('error', 'unknown')}]"}, "index": 0}],
                        }
                        yield {"data": json.dumps(error_chunk)}
                        yield {"data": "[DONE]"}
                        return

                    if msg["type"] == "inference_chunk":
                        raw_chunk = msg.get("chunk", {})

                        if raw_chunk.get("done"):
                            final_msg = raw_chunk.get("message", {})
                            # Merge with previously captured tool_calls (Ollama sends them before done)
                            if done_message and "tool_calls" in done_message:
                                final_msg["tool_calls"] = done_message["tool_calls"]
                            done_message = final_msg
                            break

                        message = raw_chunk.get("message", {})
                        content = message.get("content", "")
                        thinking = message.get("thinking", "")

                        # Capture tool_calls from streaming chunks (Ollama sends them before the done chunk)
                        chunk_tool_calls = message.get("tool_calls")
                        if chunk_tool_calls:
                            if done_message is None:
                                done_message = {}
                            done_message["tool_calls"] = chunk_tool_calls

                        if thinking:
                            delta = {"content": thinking, "reasoning": True}
                            chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "model": request.model,
                                "choices": [{"delta": delta, "index": 0}],
                            }
                            yield {"data": json.dumps(chunk)}
                        if content:
                            accumulated_content += content
                            display_content = tag_stripper.feed(content)
                            display_content = content_filter.filter_outbound(display_content)
                            if display_content:
                                delta = {"content": display_content}
                                chunk = {
                                    "id": chat_id,
                                    "object": "chat.completion.chunk",
                                    "model": request.model,
                                    "choices": [{"delta": delta, "index": 0}],
                                }
                                yield {"data": json.dumps(chunk)}

                # Stream complete — check for tool calls (only if tools were offered)
                tool_calls = (
                    parse_tool_calls(
                        accumulated_content,
                        done_message,
                        native_only=supports_native_tools,
                    )
                    if tools_offered
                    else []
                )

                if not tool_calls:
                    # Flush any remaining buffered content from tag stripper
                    remaining = tag_stripper.flush()
                    if remaining:
                        flush_chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": request.model,
                            "choices": [{"delta": {"content": remaining}, "index": 0}],
                        }
                        yield {"data": json.dumps(flush_chunk)}
                    yield {"data": "[DONE]"}
                    return

                # Tool calls detected — execute them
                tool_round += 1
                logger.info(
                    "Tool calls detected (round %d): %s",
                    tool_round,
                    [tc["name"] for tc in tool_calls],
                    extra={"request_id": request_id},
                )

                # Emit SSE tool status events (executing)
                for tc in tool_calls:
                    tool_status_chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "model": request.model,
                        "choices": [{"delta": {"tool_call": {"name": tc["name"], "status": "executing"}}, "index": 0}],
                    }
                    yield {"data": json.dumps(tool_status_chunk)}

                # Execute tools
                tool_results = await execute_tool_calls(tool_calls, tool_registry, node_id=node.node_id)

                # Emit SSE tool status events (done)
                for tr in tool_results:
                    tool_done_chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "model": request.model,
                        "choices": [{"delta": {"tool_call": {"name": tr.name, "status": "done"}}, "index": 0}],
                    }
                    yield {"data": json.dumps(tool_done_chunk)}

                # Construct follow-up messages
                if supports_native_tools:
                    # Native follow-up: assistant message with tool_calls + tool role results
                    ollama_params["messages"].append({
                        "role": "assistant",
                        "content": accumulated_content,
                        "tool_calls": done_message.get("tool_calls", []) if done_message else [],
                    })
                    for tc, tr in zip(tool_calls, tool_results):
                        ollama_params["messages"].append({
                            "role": "tool",
                            "content": tr.result,
                        })
                else:
                    # Fallback follow-up: stripped assistant content + user role tool results
                    stripped_content = strip_tool_tags(accumulated_content)
                    if stripped_content:
                        ollama_params["messages"].append({
                            "role": "assistant",
                            "content": stripped_content,
                        })
                    for tc, tr in zip(tool_calls, tool_results):
                        ollama_params["messages"].append({
                            "role": "user",
                            "content": f"[Tool Result for {tc['name']}]:\n{tr.result}",
                        })

                # Enforce max tool rounds — on round limit, rebuild without tools
                if tool_round >= MAX_TOOL_ROUNDS:
                    logger.info(
                        "Max tool rounds reached (%d), forcing text response",
                        MAX_TOOL_ROUNDS,
                        extra={"request_id": request_id},
                    )
                    ollama_params.pop("tools", None)

                # Clean up old request queue and send new inference_request
                remove_request_queue(request_queues, request_node_map, request_id)
                request_id = str(uuid.uuid4())
                queue = create_request_queue(request_queues, request_node_map, request_id, node.node_id)

                await node.websocket.send_text(json.dumps({
                    "type": "inference_request",
                    "request_id": request_id,
                    "ollama_params": ollama_params,
                }))

        finally:
            duration = time.monotonic() - request_start
            stats.requests_total += 1
            stats.requests_active = max(0, stats.requests_active - 1)
            status = "error" if request_error else "success"
            if request_error:
                stats.requests_errors_total += 1
            log_extra = {
                "request_id": request_id,
                "model": request.model,
                "node_id": node.node_id,
                "duration_s": round(duration, 2),
                "status": status,
                "tool_rounds": tool_round,
            }
            if request_error:
                log_extra["error"] = request_error
            logger.info("Inference request completed", extra=log_extra)
            node.active_requests = max(0, node.active_requests - 1)
            remove_request_queue(request_queues, request_node_map, request_id)
            # Tell node to cancel if still running (client may have disconnected)
            try:
                await node.websocket.send_text(json.dumps({
                    "type": "cancel_request",
                    "request_id": request_id,
                }))
            except Exception:
                pass

    return EventSourceResponse(event_generator())
