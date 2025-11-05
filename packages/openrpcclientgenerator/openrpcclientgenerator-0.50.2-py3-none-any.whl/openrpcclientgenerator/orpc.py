"""CLI main entry point."""

import json
from pathlib import Path

import httpx
from jsonrpcobjects.objects import ResultResponse
from openrpc import OpenRPC, RPCServer
from openrpcclientgenerator import generate, Language
from rpc_cli import cli

rpc = RPCServer(title="OpenRPC Client Generator")


@rpc.method()
def python(api_url: str, out: Path | None = None) -> str:
    """Generate a Python client."""
    openrpc = _get_openrpc(api_url)
    out = out or Path.cwd().joinpath("out")
    out.mkdir(exist_ok=True)
    name = generate(openrpc, Language.PYTHON, api_url, out)
    return f"{out.as_posix()}/python/{name}"


@rpc.method()
def rust(api_url: str, out: Path | None = None) -> str:
    """Generate a Rust client."""
    openrpc = _get_openrpc(api_url)
    out = out or Path.cwd().joinpath("out")
    out.mkdir(exist_ok=True)
    name = generate(openrpc, Language.RUST, api_url, out)
    return f"{out.as_posix()}/rust/{name}"


@rpc.method()
def typescript(api_url: str, out: Path | None = None) -> str:
    """Generate a TypeScript client."""
    openrpc = _get_openrpc(api_url)
    out = out or Path.cwd().joinpath("out")
    out.mkdir(exist_ok=True)
    name = generate(openrpc, Language.TYPESCRIPT, api_url, out)
    return f"{out.as_posix()}/typescript/{name}"


def _get_openrpc(api_url: str) -> OpenRPC:
    if Path.cwd().joinpath("openrpc.json").exists():
        return OpenRPC(**json.loads(Path.cwd().joinpath("openrpc.json").read_text()))
    resp = httpx.post(
        api_url, json={"id": 1, "method": "rpc.discover", "jsonrpc": "2.0"}
    )
    result = ResultResponse(**resp.json())
    return OpenRPC(**result.result)


def main() -> None:
    """Run client generator CLI."""
    _ = cli(rpc, exclude_discover=True).run()


if __name__ == "__main__":
    main()
