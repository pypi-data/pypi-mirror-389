"""
同步 HTTP 客户端：requests + Retry
"""
from __future__ import annotations
import json, logging
from typing import Any, Dict, Callable, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .vendor import default_base, patch_hdr
from .exceptions import HttpError, CreditError, RateLimitError, LayBotError

LOG = logging.getLogger("laybot.client")

class Client:
    _DEF_TMO = {"connect": 10, "idle": 180}

    def __init__(self, api_key: str, *,
                 vendor: str = "laybot",
                 base: str | None = None,
                 timeout: Dict[str, int] | None = None,
                 on_req: Callable | None = None,
                 on_resp: Callable | None = None):
        self.base = (base or default_base(vendor)).rstrip("/") + "/"
        self.headers = {
            "Content-Type": "application/json",
            **patch_hdr(vendor, api_key)
        }
        self.tmo = {**self._DEF_TMO, **(timeout or {})}
        self.on_req, self.on_resp = on_req, on_resp

        retry = Retry(total=3, backoff_factor=.2,
                      status_forcelist=[429, 500, 502, 503, 504])
        self.session = requests.Session()
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    # ---------------- 基础 ----------------
    def _req(self, m: str, path: str, **opt):
        url = self.base + path.lstrip("/")
        if self.on_req:
            self.on_req(m, url, opt)
        try:
            r: requests.Response = self.session.request(
                m, url, headers=self.headers,
                timeout=(self.tmo["connect"], None), **opt
            )
            if self.on_resp:
                self.on_resp(r)
            if r.status_code == 402:
                raise CreditError("credit exhausted")
            if r.status_code == 429:
                raise RateLimitError("rate limited")
            if r.status_code >= 400:
                raise HttpError(f"HTTP {r.status_code}: {r.text}")
            return r
        except requests.RequestException as exc:
            raise LayBotError(str(exc)) from exc

    # ---------------- 公共 ----------------
    def post(self, path: str, body: Dict[str, Any], stream=False):
        return self._req("POST", path, json=body, stream=stream)

    def get(self, path: str, **params):
        return self._req("GET", path, params=params)

    def delete(self, path: str):
        return self._req("DELETE", path)
