"""
Chat / Completion
"""
from __future__ import annotations
from typing import Callable, Any, Optional
from .client import Client
from .stream import stream_post
from .vendor import default_ep
from .exceptions import ValidationError

class Chat:
    def __init__(self, api_key: str | Client,
                 *, vendor: str = "laybot", base: str | None = None):
        self.cli: Client = api_key if isinstance(api_key, Client) \
            else Client(api_key, vendor=vendor, base=base)
        self.is_laybot = vendor == "laybot"

    # ---------- 主接口 ----------
    def completions(
        self,
        body: dict,
        on_stream: Optional[Callable[[dict, bool], Any]] = None
    ) -> Optional[dict]:
        # 基础校验
        if "model" not in body or "messages" not in body:
            raise ValidationError("model & messages required")

        # LayBot 需带 capability
        if self.is_laybot:
            body["capability"] = "chat"

        # 端点
        path = body.pop("endpoint", None) \
            or default_ep("laybot" if self.is_laybot else "openai", "chat") \
            or "/v1/chat"

        # 非流式
        if not body.get("stream"):
            return self.cli.post(path, body).json()

        # 流式
        stream_post(self.cli, path, body, on_delta=on_stream)
        return None
