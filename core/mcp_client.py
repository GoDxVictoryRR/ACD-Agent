"""
core/mcp_client.py — Live MCP routing layer for agent loop and deterministic fallback.

Features:
- Calls tools via mcp_server.server.server (in-process MCPServer from official Python MCP SDK).
- Controlled by USE_MCP environment variable (default: True).
- Direct fallback to core.tools if USE_MCP is False or if MCP execution fails.
- Returns (ToolResult, via: "mcp" | "direct").
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from typing import Any

from core import tools
from core.config import USE_MCP
from core.tools import ToolResult

logger = logging.getLogger(__name__)

_server = None
_mcp_init_failed = False


def _get_server():
    global _server, _mcp_init_failed
    if _server is None and not _mcp_init_failed:
        try:
            from mcp_server.server import server

            _server = server
        except Exception as exc:
            logger.warning("Failed to initialize MCPServer in-process: %s; falling back to direct", exc)
            _mcp_init_failed = True
    return _server


def invoke_tool(
    tool_name: str,
    params: dict[str, Any],
    **kwargs,
) -> tuple[ToolResult, str]:
    """
    Invoke a tool via MCP server or direct fallback.
    Returns (result, "mcp") or (result, "direct").
    """
    if not USE_MCP:
        tool_func = getattr(tools, tool_name)
        merged_params = {**params, **kwargs}
        res = tool_func(**merged_params)
        return res, "direct"

    server_inst = _get_server()
    if server_inst is not None:
        try:

            async def _call():
                return await server_inst.call_tool(tool_name, params)

            # Check if there is an active running event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    call_result = pool.submit(asyncio.run, _call()).result(timeout=15)
            else:
                call_result = asyncio.run(_call())

            if call_result and call_result.content:
                text = call_result.content[0].text
                data_dict = json.loads(text)
                return ToolResult.model_validate(data_dict), "mcp"
        except Exception as mcp_exc:
            logger.warning("MCP call_tool('%s') failed: %s; falling back to direct execution", tool_name, mcp_exc)

    # Fallback to direct execution
    tool_func = getattr(tools, tool_name)
    merged_params = {**params, **kwargs}
    res = tool_func(**merged_params)
    return res, "direct"
