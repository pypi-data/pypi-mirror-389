# laybot_ai/vendor.py
"""
Vendor 表 —— 与 PHP SDK 完全同构
-----------------------------------------
字段说明
base : 厂商基地址
ep   : capability => endpoint 路径   ← 与 PHP SDK 一致
hdr  : 生成认证 Header 的回调         ← 与 PHP SDK 一致
"""
DEFAULT = "laybot"

_VENDOR_TABLE: dict[str, dict] = {
    # LayBot 网关
    "laybot": {
        "base": "https://api.laybot.cn",
        "ep": {                       # capability -> path
            "chat":  "/v1/chat",
            "embed": "/v1/chat",
            "doc":   "/v1/doc",
        },
        "hdr": lambda k: {"X-API-Key": k},
    },

    # OpenAI 官方
    "openai": {
        "base": "https://api.openai.com",
        "ep": {
            "chat":  "/v1/chat/completions",
            "embed": "/v1/embeddings",
        },
        "hdr": lambda k: {"Authorization": f"Bearer {k}"},
    },

    # DeepSeek
    "deepseek": {
        "base": "https://api.deepseek.com",
        "ep": {
            "chat":  "/v1/chat/completions",
            "embed": "/v1/embeddings",
        },
        "hdr": lambda k: {"Authorization": f"Bearer {k}"},
    },

    # Groq
    "grok": {
        "base": "https://api.groq.com",
        "ep": {
            "chat":  "/openai/v1/chat/completions",
            "embed": "/openai/v1/embeddings",
        },
        "hdr": lambda k: {"Authorization": f"Bearer {k}"},
    },

    # Azure-OpenAI（需业务侧把 {RESOURCE}/{DEPLOY} 替换成实际值）
    "azure-openai": {
        "base": "https://{RESOURCE}.openai.azure.com",
        "ep": {
            "chat":  "/openai/deployments/{DEPLOY}/chat/completions?api-version=2024-05-01-preview",
            "embed": "/openai/deployments/{DEPLOY}/embeddings?api-version=2024-05-01-preview",
        },
        "hdr": lambda k: {"api-key": k},
    },
    # ……如有更多厂商同样追加……
}

# ---------------- 公共辅助函数 ----------------
def info(vendor: str) -> dict:
    return _VENDOR_TABLE.get(vendor, _VENDOR_TABLE[DEFAULT])

def default_base(vendor: str) -> str:
    return info(vendor)["base"]

def default_ep(vendor: str, cap: str) -> str | None:
    return info(vendor)["ep"].get(cap)

def patch_hdr(vendor: str, api_key: str) -> dict:
    hdr_fn = info(vendor)["hdr"]
    return hdr_fn(api_key) if hdr_fn else {}
