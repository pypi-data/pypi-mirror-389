"""
/_inner & /usage 等运营查询接口（LayBot Only）
"""
from __future__ import annotations
from .client import Client

class Portal:
    def __init__(self, api_key: str | Client, *, base=None):
        self.cli = api_key if isinstance(api_key, Client) \
            else Client(api_key, vendor="laybot", base=base)

    def call(self, method: str, path: str, params=None, whole=False):
        method = method.upper()
        path = path.lstrip("/")
        params = params or {}
        if method == "GET":
            r = self.cli.get(path, **params)
        else:
            r = self.cli.post(path, params)
        data = r.json()
        return data if whole else data.get("data", data)

    # 便捷
    def models(self):
        return self.call("POST", "/v1/models")

    def doc_usage(self, start_date="", end_date=""):
        return self.call("GET", "/v1/usage/doc",
                         {"start_date": start_date, "end_date": end_date})

    def account_usage(self):
        return self.call("GET", "/v1/usage/account")
