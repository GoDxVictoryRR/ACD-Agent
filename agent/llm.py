"""
agent/llm.py — NVIDIA OpenAI-compatible API client wrapper.

Features:
- Points to https://integrate.api.nvidia.com/v1.
- Invariant 11: Max 8 calls per investigation, retry on 429/5xx with exponential backoff (max 3).
- Daily call rate cap tracking.
- Response cache under cache/ to conserve rate limits.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from core.config import (
    DAILY_LLM_CAP,
    LLM_RETRY_BASE_DELAY,
    LLM_RETRY_MAX,
    MAX_LLM_CALLS_PER_RUN,
    NO_LLM,
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_MODEL,
)

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

# Module-level daily counter
_daily_calls = 0
_daily_counter_date = ""


def _get_cache_path(model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> Path:
    payload = json.dumps({"model": model, "messages": messages, "tools": tools}, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.json"


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enable_cache: bool = True,
    ):
        self.api_key = api_key if api_key is not None else NVIDIA_API_KEY
        self.model = model if model is not None else NVIDIA_MODEL
        self.base_url = NVIDIA_BASE_URL
        self.enable_cache = enable_cache
        self.run_call_count = 0

        self.client: OpenAI | None = None
        if self.api_key and not NO_LLM and self.api_key != "nvapi-...":
            try:
                self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            except Exception as exc:
                logger.warning("Failed to initialize OpenAI client for NVIDIA: %s", exc)

    def is_available(self) -> bool:
        return bool(self.client is not None and not NO_LLM)

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> Any:
        global _daily_calls, _daily_counter_date

        if not self.is_available():
            raise RuntimeError("NVIDIA LLM client is not configured or disabled (NO_LLM=1).")

        # Invariant 11: Call counter check
        if self.run_call_count >= MAX_LLM_CALLS_PER_RUN:
            raise RuntimeError(f"Run LLM call cap ({MAX_LLM_CALLS_PER_RUN}) exceeded.")

        # Daily rate cap check
        today = time.strftime("%Y-%m-%d")
        if _daily_counter_date != today:
            _daily_counter_date = today
            _daily_calls = 0
        if _daily_calls >= DAILY_LLM_CAP:
            raise RuntimeError(f"Daily LLM call cap ({DAILY_LLM_CAP}) reached.")

        # Check cache if enabled
        cache_path = _get_cache_path(self.model, messages, tools)
        if self.enable_cache and cache_path.exists():
            try:
                with open(cache_path, encoding="utf-8") as f:
                    cached_data = json.load(f)
                logger.info("Loaded LLM response from cache (%s)", cache_path.name)
                return cached_data
            except Exception:
                pass

        # Exponential backoff retry loop
        last_exc: Exception | None = None
        delay = LLM_RETRY_BASE_DELAY

        for attempt in range(1, LLM_RETRY_MAX + 1):
            try:
                self.run_call_count += 1
                _daily_calls += 1

                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                }
                if tools:
                    kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice

                assert self.client is not None
                response = self.client.chat.completions.create(**kwargs)

                # Convert to dict for caching
                resp_dict = response.model_dump()

                if self.enable_cache:
                    CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    try:
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(resp_dict, f, indent=2)
                    except Exception as ce:
                        logger.debug("Failed to write LLM cache: %s", ce)

                return resp_dict
            except Exception as exc:
                last_exc = exc
                err_str = str(exc).lower()
                is_retryable = "429" in err_str or "rate" in err_str or "500" in err_str or "503" in err_str
                if is_retryable and attempt < LLM_RETRY_MAX:
                    logger.warning("LLM call attempt %d failed (%s). Retrying in %.1fs...", attempt, exc, delay)
                    time.sleep(delay)
                    delay *= 2
                else:
                    break

        raise RuntimeError(f"LLM call failed after {LLM_RETRY_MAX} attempts: {last_exc}")
