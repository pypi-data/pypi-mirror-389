from __future__ import annotations
from .client import Client
from .vendor import default_ep
from .exceptions import ValidationError

class Embed:
    def __init__(self, api_key: str | Client,
                 *, vendor="laybot", base=None):
        self.cli = api_key if isinstance(api_key, Client) \
            else Client(api_key, vendor=vendor, base=base)
        self.is_laybot = vendor == "laybot"

    def embeddings(self, body: dict) -> dict:
        if "model" not in body:
            raise ValidationError("model required")
        if self.is_laybot:
            body["capability"] = "embed"
        path = body.pop("endpoint", None) \
            or "/v1/embeddings"
        return self.cli.post(path, body).json()
