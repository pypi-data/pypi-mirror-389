"""
流式 POST 工具：阻塞式同步
"""
from __future__ import annotations
import json
from typing import Callable, Any
from .client import Client
from .decoder import sse_iter

def stream_post(cli: Client, path: str, body: dict,
                on_delta: Callable[[dict, bool], Any] | None = None):
    resp = cli.post(path, body, stream=True)
    for data in sse_iter(resp):
        if data == "[DONE]":
            if on_delta:
                on_delta({}, True)
            break
        try:
            payload = json.loads(data)
            if on_delta:
                on_delta(payload, False)
        except Exception:
            # 忽略非 JSON 帧
            continue
