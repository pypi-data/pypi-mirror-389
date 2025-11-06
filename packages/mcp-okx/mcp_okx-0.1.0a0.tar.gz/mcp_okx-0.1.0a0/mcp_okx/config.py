import os

def getenv(key: str, default: str = None, empty: bool = False):
    val = os.environ.get(key, default)
    if empty and not val:
        return default
    return val

OKX_BASE_URL = getenv("OKX_BASE_URL", "https://www.okx.com", True)
OKX_API_KEY = getenv("OKX_API_KEY")
OKX_API_SECRET = getenv("OKX_API_SECRET")
OKX_PASSPHRASE = getenv("OKX_PASSPHRASE")
OKX_TRADE_FLAG = getenv("OKX_TRADE_FLAG", "1")
