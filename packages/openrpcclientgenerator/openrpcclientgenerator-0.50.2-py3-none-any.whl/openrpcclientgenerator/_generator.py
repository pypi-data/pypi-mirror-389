"""Client generator top-level."""

from pathlib import Path

from openrpc import OpenRPC

from openrpcclientgenerator import _python, _rust, _typescript
from openrpcclientgenerator._common import Language


def generate(openrpc: OpenRPC, language: Language, url: str, out: Path) -> str:
    """Generate an RPC client."""
    transport = "WS" if url.startswith("ws") else "HTTP"
    match language:
        case Language.PYTHON:
            lang = _python
        case Language.TYPESCRIPT:
            lang = _typescript
        case Language.RUST:
            lang = _rust
    return lang.generate_client(openrpc, url, transport, out)
