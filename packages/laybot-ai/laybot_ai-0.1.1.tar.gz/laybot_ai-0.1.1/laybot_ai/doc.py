from __future__ import annotations
from .client import Client
from .exceptions import ValidationError
from .vendor import default_ep

class Doc:
    def __init__(self, api_key: str | Client,
                 *, base: str | None = None):
        self.cli = api_key if isinstance(api_key, Client) \
            else Client(api_key, vendor="laybot", base=base)

    def extract(self, url: str, mode="auto", math=False) -> dict:
        body = {"url": url, "mode": mode, "math": math}
        return self.cli.post("/v1/doc", body).json()

    def status(self, job_id: str) -> dict:
        return self.cli.get(f"/v1/doc/{job_id}").json()
