# Open-RPC Client Generator

Generate clients from Open-RPC APIs.

## Supported Languages

- Python
- Rust
- TypeScript

## CLI

To see options.

```shell
orpc --help
```

### Generate a Client

Call `orpc` passing as arguments the language to generate client for, the URL of the API, and the `out` directory to write the generated files to.

If no argument is passed for `out` it will default to `./out/`.

By default it will look for an `openrpc.json` file in the active directory.
If it finds no file it will call the `rpc.discover` method of the given URL.

```shell
orpc rust "http://127.0.0.1:1737" ./out
```
