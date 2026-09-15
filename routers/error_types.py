#!/usr/bin/env python3
"""
Bosly Gov v4 - Typed Error Model + Standard Error Envelope
Python 3.12+
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any


@dataclass
class BoslyError(Exception):
    code: str
    message: str
    hint: str
    retryable: bool
    request_id: str | None = None
    status: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def to_envelope(self) -> dict[str, Any]:
        return {
            "ok": False,
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "retryable": self.retryable,
            "request_id": self.request_id,
        }


class ValidationError(BoslyError):
    def __init__(self, message: str, hint: str = "Check request fields and try again.", request_id: str | None = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            hint=hint,
            retryable=False,
            request_id=request_id,
            status=HTTPStatus.BAD_REQUEST,
        )


class LLMTimeoutError(BoslyError):
    def __init__(self, message: str = "The language model timed out.", hint: str = "Retry in a moment or shorten your request.", request_id: str | None = None):
        super().__init__(
            code="LLM_TIMEOUT",
            message=message,
            hint=hint,
            retryable=True,
            request_id=request_id,
            status=HTTPStatus.GATEWAY_TIMEOUT,
        )


class ContextLoadError(BoslyError):
    def __init__(self, message: str = "Failed to load context.", hint: str = "Try again, or provide the exact file path to narrow context.", request_id: str | None = None):
        super().__init__(
            code="CONTEXT_LOAD_ERROR",
            message=message,
            hint=hint,
            retryable=True,
            request_id=request_id,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class MemoryStoreError(BoslyError):
    def __init__(self, message: str = "Memory subsystem failed.", hint: str = "Continuing without memory. You can retry later.", request_id: str | None = None):
        super().__init__(
            code="MEMORY_STORE_ERROR",
            message=message,
            hint=hint,
            retryable=True,
            request_id=request_id,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class FileAccessError(BoslyError):
    def __init__(self, message: str = "File access failed.", hint: str = "Verify the file path and permissions; continuing without file context.", request_id: str | None = None):
        super().__init__(
            code="FILE_ACCESS_ERROR",
            message=message,
            hint=hint,
            retryable=True,
            request_id=request_id,
            status=HTTPStatus.BAD_REQUEST,
        )


class UnknownError(BoslyError):
    def __init__(self, message: str = "Unexpected server error.", hint: str = "Retry your request. If it persists, check server logs.", request_id: str | None = None):
        super().__init__(
            code="UNKNOWN_ERROR",
            message=message,
            hint=hint,
            retryable=True,
            request_id=request_id,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


def error_envelope(
    code: str,
    message: str,
    hint: str,
    retryable: bool,
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "code": code,
        "message": message,
        "hint": hint,
        "retryable": bool(retryable),
        "request_id": request_id,
    }


def normalize_exception(exc: Exception, request_id: str | None = None) -> BoslyError:
    if isinstance(exc, BoslyError):
        if not exc.request_id:
            exc.request_id = request_id
        return exc

    msg = str(exc) or exc.__class__.__name__
    low = msg.lower()

    if "timeout" in low:
        return LLMTimeoutError(message=msg, request_id=request_id)

    if "json" in low or "required" in low or "invalid" in low:
        return ValidationError(message=msg, request_id=request_id)

    if "memory" in low:
        return MemoryStoreError(message=msg, request_id=request_id)

    if "file" in low or "path" in low:
        return FileAccessError(message=msg, request_id=request_id)

    return UnknownError(message=msg, request_id=request_id)
