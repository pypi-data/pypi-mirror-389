from __future__ import annotations
from pathlib import Path
from .client import Client
from .exceptions import ValidationError

class File:
    def __init__(self, api_key: str | Client, *, vendor="laybot", base=None):
        self.cli = api_key if isinstance(api_key, Client) \
            else Client(api_key, vendor=vendor, base=base)

    def upload(self, path: str, purpose="batch") -> dict:
        fp = Path(path)
        if not fp.is_file():
            raise ValidationError(f"{path} not found")
        with fp.open("rb") as f:
            r = self.cli.session.post(
                self.cli.base + "v1/files",
                headers=self.cli.headers,
                files={"file": (fp.name, f, "application/octet-stream")},
                data={"purpose": purpose},
                timeout=self.cli.tmo["connect"],
            )
        if r.status_code >= 400:
            raise HttpError(r.text)
        return r.json()

    def download(self, file_id: str) -> str:
        return self.cli.get(f"v1/files/{file_id}/content").text

    def delete(self, file_id: str) -> dict:
        return self.cli.delete(f"v1/files/{file_id}").json()
