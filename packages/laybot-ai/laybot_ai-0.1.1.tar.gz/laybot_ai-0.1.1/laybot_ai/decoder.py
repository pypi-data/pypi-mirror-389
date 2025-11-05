"""
把 text/event-stream 拆帧
"""
import json
from typing import Iterator
import requests

def sse_iter(resp: requests.Response) -> Iterator[str]:
    buff = ""
    for chunk in resp.iter_content(chunk_size=2048, decode_unicode=True):
        buff += chunk
        while "\n" in buff:
            line, buff = buff.split("\n", 1)
            line = line.rstrip("\r")
            if not line.startswith("data:"):
                continue
            yield line[5:].strip()
