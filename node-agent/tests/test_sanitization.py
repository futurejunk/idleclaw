"""Tests for node-agent input validation and output sanitization."""

from __future__ import annotations

import json
import sys
import os

import pytest

# Add src to path so we can import ollama_bridge
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ollama_bridge import validate_params, VALID_ROLES
from connection import ALLOWED_CHUNK_FIELDS, ALLOWED_MESSAGE_FIELDS, MAX_CHUNK_BYTES


MODELS = ["llama3.2:3b"]


class TestValidateParamsRoles:
    def test_user_role_accepted(self):
        params = {"model": "llama3.2:3b", "messages": [{"role": "user", "content": "hi"}]}
        result = validate_params(params, MODELS)
        assert result["messages"][0]["role"] == "user"

    def test_system_role_accepted(self):
        params = {"model": "llama3.2:3b", "messages": [{"role": "system", "content": "you are helpful"}]}
        result = validate_params(params, MODELS)
        assert result["messages"][0]["role"] == "system"

    def test_assistant_role_accepted(self):
        params = {"model": "llama3.2:3b", "messages": [{"role": "assistant", "content": "hello"}]}
        result = validate_params(params, MODELS)
        assert result["messages"][0]["role"] == "assistant"

    def test_tool_role_accepted(self):
        params = {"model": "llama3.2:3b", "messages": [{"role": "tool", "content": "result"}]}
        result = validate_params(params, MODELS)
        assert result["messages"][0]["role"] == "tool"

    def test_invalid_role_rejected(self):
        params = {"model": "llama3.2:3b", "messages": [{"role": "admin", "content": "hi"}]}
        with pytest.raises(ValueError, match="Invalid message role"):
            validate_params(params, MODELS)

    def test_empty_role_rejected(self):
        params = {"model": "llama3.2:3b", "messages": [{"role": "", "content": "hi"}]}
        with pytest.raises(ValueError, match="Invalid message role"):
            validate_params(params, MODELS)


class TestValidateParamsLimits:
    def test_content_too_long(self):
        params = {"model": "llama3.2:3b", "messages": [{"role": "user", "content": "x" * 11_000}]}
        with pytest.raises(ValueError, match="Message content too long"):
            validate_params(params, MODELS)

    def test_too_many_messages(self):
        msgs = [{"role": "user", "content": "hi"} for _ in range(51)]
        params = {"model": "llama3.2:3b", "messages": msgs}
        with pytest.raises(ValueError, match="Too many messages"):
            validate_params(params, MODELS)

    def test_unknown_params_stripped(self):
        params = {"model": "llama3.2:3b", "messages": [{"role": "user", "content": "hi"}], "evil": True}
        result = validate_params(params, MODELS)
        assert "evil" not in result


class TestOutputSanitizationConstants:
    def test_allowed_chunk_fields(self):
        assert "message" in ALLOWED_CHUNK_FIELDS
        assert "done" in ALLOWED_CHUNK_FIELDS

    def test_allowed_message_fields(self):
        assert "role" in ALLOWED_MESSAGE_FIELDS
        assert "content" in ALLOWED_MESSAGE_FIELDS
        assert "thinking" in ALLOWED_MESSAGE_FIELDS
        assert "tool_calls" in ALLOWED_MESSAGE_FIELDS

    def test_max_chunk_size(self):
        assert MAX_CHUNK_BYTES == 100_000

    def test_sanitize_message_fields(self):
        """Simulate the sanitization logic from connection.py."""
        raw_message = {
            "role": "assistant",
            "content": "hello",
            "evil_field": "should be stripped",
            "thinking": "",
        }
        sanitized = {k: v for k, v in raw_message.items() if k in ALLOWED_MESSAGE_FIELDS}
        assert "evil_field" not in sanitized
        assert "role" in sanitized
        assert "content" in sanitized
