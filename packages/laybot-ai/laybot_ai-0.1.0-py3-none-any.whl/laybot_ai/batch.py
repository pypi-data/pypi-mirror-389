from __future__ import annotations
from .client import Client

class Batch:
    def __init__(self, api_key: str | Client, *, base=None):
        self.cli = api_key if isinstance(api_key, Client) \
            else Client(api_key, vendor="laybot", base=base)

    def upload_jsonl(self, path: str) -> dict:
        files = {"file": open(path, "rb")}
        return self.cli.post("v1/files", {"purpose": "batch"}).json()

    def create(self, input_file_id: str, target="/v1/chat/completions",
               window="24h", metadata=None):
        body = {
            "input_file_id": input_file_id,
            "target_endpoint": target,
            "completion_window": window,
            "metadata": metadata or {},
            "capability": "batch",
        }
        return self.cli.post("/v1/batch", body).json()

    def retrieve(self, batch_id: str):
        return self.cli.get(f"/v1/batch/{batch_id}").json()

    def list(self, limit=20):
        return self.cli.get("/v1/batch", limit=limit).json()

    def cancel(self, batch_id: str):
        return self.cli.post(f"/v1/batch/{batch_id}/cancel", {}).json()
