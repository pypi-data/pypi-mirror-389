from __future__ import annotations
from .client import Client
from .exceptions import ValidationError

class FineTune:
    def __init__(self, api_key: str | Client, *, base=None):
        self.cli = api_key if isinstance(api_key, Client) \
            else Client(api_key, vendor="laybot", base=base)

    def create(self, body: dict) -> dict:
        if "model" not in body:
            raise ValidationError("model required")
        body["capability"] = "tune"
        body["endpoint"] = "/v1/fine_tuning/jobs"
        return self.cli.post("/v1/chat", body).json()   # 复用 chat 路径

    def retrieve(self, job_id: str):
        return self.cli.get(f"/v1/fine_tuning/jobs/{job_id}").json()

    def cancel(self, job_id: str):
        return self.cli.post(f"/v1/fine_tuning/jobs/{job_id}/cancel", {}).json()
