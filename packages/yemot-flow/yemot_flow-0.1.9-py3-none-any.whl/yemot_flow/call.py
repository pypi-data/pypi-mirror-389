# ================================================================
# File: yemot_router/call.py
# ================================================================
"""Call – אובייקט שיחה בודדת עם תמיכה ב-async כמו yemot-router2."""
from __future__ import annotations

import asyncio
from typing import List, Tuple, Optional, Any

from .actions import build_go_to_folder, build_id_list_message, build_read
from .utils import now_ms

Message = Tuple[str, str]


class CallInterrupted(Exception):
    """נזרק כשהשיחה צריכה להיפסק לקבלת קלט מהמשתמש"""
    def __init__(self, response: str):
        self.response = response
        super().__init__()


class Call:
    def __init__(self, params: dict, *, flow: "Flow"):
        from .flow import Flow  # local to avoid circular
        self.params = params.copy()
        self.flow = flow
        self.call_id = params.get("ApiCallId")
        self.response_parts: List[str] = []
        self.last_activity_ms = now_ms()
        self._waiting_for_input = False
        self._expected_param = None
        self._handler_state = "fresh"  # fresh, waiting_input, completed

    def update_params(self, new_params: dict):
        self.params.update(new_params)
        self.last_activity_ms = now_ms()

    # -------- API --------
    def play_message(self, messages: List[Message], **opts):
        """השמעת הודעות - מחזיר מיד אחרי השמעה"""
        response = build_id_list_message(messages, **opts)
        raise CallInterrupted(response)

    async def read(self, messages: List[Message], *, mode: str = "tap", **opts) -> Optional[str]:
        """קבלת קלט מהמשתמש - מחזיר את התוצאה"""
        
        # אם יש כבר קלט מהקריאה הקודמת
        val_name = opts.get("val_name", "Digits")
        existing_value = self.params.get(val_name)
        
        if existing_value is not None and self._handler_state == "waiting_input":
            self._handler_state = "completed"
            return existing_value
        
        # אין קלט - צריך לבקש מהמשתמש
        self._handler_state = "waiting_input"
        self._expected_param = val_name
        
        response = build_read(messages, mode=mode, **opts)
        raise CallInterrupted(response)

    def goto(self, folder: str):
        """מעבר לשלוחה אחרת"""
        response = build_go_to_folder(folder)
        raise CallInterrupted(response)

    def hangup(self):
        """ניתוק השיחה"""
        self.goto("hangup")

    def render_response(self) -> str:
        """עיבוד התגובה הסופית - לא אמור להיקרא עוד"""
        if not self.response_parts:
            return "noop"
        resp = "\n".join(self.response_parts)
        self.response_parts.clear()
        return resp

