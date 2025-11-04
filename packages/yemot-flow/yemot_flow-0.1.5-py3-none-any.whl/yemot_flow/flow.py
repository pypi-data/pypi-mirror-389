# ================================================================
# File: yemot_router/flow.py
# ================================================================
"""Flow – ניהול שיחות ומיפוי שלוחות."""
from __future__ import annotations

import logging
from typing import Callable, Dict

from .call import Call
from .utils import now_ms

_LOG = logging.getLogger("yemot_flow")
Handler = Callable[[Call], None]


class Flow:
    """מנהל שיחות בזיכרון לפי `ApiCallId`."""

    def __init__(self, *, timeout: int | float = 30_000, print_log: bool = False):
        self.active_calls: Dict[str, Call] = {}
        self.routes: Dict[str, Handler] = {}
        self.timeout_ms = int(timeout)
        if print_log:
            logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # ---------------- Registration ----------------
    def add_route(self, extension: str, handler: Handler):
        self.routes[extension.strip("/")] = handler
        _LOG.debug("Route registered: %s -> %s", extension, handler)

    def get(self, extension: str):
        def decorator(handler: Handler):
            self.add_route(extension, handler)
            return handler
        return decorator

    # ---------------- Entry‑point -----------------
    def handle_request(self, params: dict) -> str:
        call_id = params.get("ApiCallId")
        if not call_id:
            _LOG.error("Missing ApiCallId – cannot continue")
            return "noop"

        self._cleanup_expired()
        call = self.active_calls.get(call_id)
        if call is None:
            call = Call(params, flow=self)
            self.active_calls[call_id] = call
        else:
            call.update_params(params)

        if params.get("hangup") == "yes":
            self.active_calls.pop(call_id, None)
            return "noop"

        ext = params.get("ApiExtension", "").strip("/")
        handler = self.routes.get(ext)
        if handler is None:
            return "id_list_message=t-שלוחה לא קיימת"

        try:
            handler(call)
            return call.render_response()
        except Exception:
            _LOG.exception("Unhandled error in handler")
            return "id_list_message=t-תקלה זמנית"

    def _cleanup_expired(self):
        now = now_ms()
        for cid, c in list(self.active_calls.items()):
            if now - c.last_activity_ms > self.timeout_ms:
                self.active_calls.pop(cid, None)

