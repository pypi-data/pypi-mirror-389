"""Generate Rust client."""

from pathlib import Path
import re
from typing import Any

import caseswitcher
from jinja2 import Environment, FileSystemLoader
from openrpc import Components, Info, Method, OpenRPC, Schema, SchemaType
from openrpcclientgenerator import _common as common

root = Path(__file__).parent
templates = root.joinpath("templates")
env = Environment(  # noqa: S701
    loader=FileSystemLoader(templates), lstrip_blocks=True, trim_blocks=True
)

lib_str = """
pub mod client;
pub mod model;
"""

keywords = ["type", "move"]


def generate_client(rpc: OpenRPC, url: str, transport: str, out: Path) -> str:
    # Create client directory and src directory.
    out.mkdir(exist_ok=True)
    rs_out = out.joinpath("rust")
    rs_out.mkdir(exist_ok=True)
    client_name = caseswitcher.to_kebab(f"{rpc.info.title}-{transport.lower()}-client")
    client_dir = rs_out.joinpath(client_name)
    client_dir.mkdir(exist_ok=True)
    src_dir = client_dir.joinpath("src")
    src_dir.mkdir(exist_ok=True)
    # Create Rust files.
    schemas = (rpc.components.schemas if rpc.components is not None else {}) or {}
    client = _get_client(
        rpc.info.title, rpc.methods, rpc.components, schemas, url, transport
    )
    common.touch_and_write(src_dir.joinpath("client.rs"), client)
    models = _get_models(rpc.components, schemas)
    common.touch_and_write(src_dir.joinpath("model.rs"), models)
    common.touch_and_write(src_dir.joinpath("lib.rs"), lib_str)
    # Create setup and README files.
    common.touch_and_write(
        client_dir.joinpath("Cargo.toml"),
        _get_setup(rpc.info, transport, client_name.replace("-", "_")),
    )
    common.touch_and_write(
        client_dir.joinpath("README.md"), _get_readme(rpc.info.title, transport)
    )
    return client_name


def _get_client(  # noqa: PLR0913
    title: str,
    methods: list[Method],
    components: Components | None,
    schemas: dict[str, SchemaType],
    url: str,
    transport: str,
) -> str:
    group = common.get_rpc_group(caseswitcher.to_pascal(title), methods)
    template = env.get_template("rust/client.j2")
    context = {
        "components": components,
        "cs": caseswitcher,
        "group": group,
        "rs_type": rs_type,
        "rust_name": _rust_name,
        "schemas": schemas,
        "transport": transport,
        "url": url,
    }
    return template.render(context)


def _get_models(components: Components | None, schemas: dict[str, SchemaType]) -> str:
    context = {
        "components": components,
        "cs": caseswitcher,
        "get_enum_option_name": common.get_enum_option_name,
        "get_enum_type": get_enum_type,
        "get_enum_value": common.get_enum_value,
        "rs_type": rs_type,
        "schemas": schemas,
    }
    template = env.get_template("rust/models.j2")
    return template.render(context)


def _get_readme(rpc_title: str, transport: str) -> str:
    template = env.get_template("rust/readme.j2")
    context = {
        "project_title": caseswitcher.to_title(rpc_title),
        "package_name": caseswitcher.to_snake(rpc_title) + "_client",
        "client_name": caseswitcher.to_pascal(rpc_title),
        "transport": transport,
    }
    return template.render(context) + "\n"


def _get_setup(info: Info, transport: str, client_name: str) -> str:
    context = {
        "project_name": caseswitcher.to_kebab(info.title) + "-client",
        "project_dir": client_name,
        "project_title": caseswitcher.to_title(info.title),
        "info": info,
        "transport": transport,
    }
    return env.get_template("rust/cargo_toml.j2").render(context) + "\n"


def rs_type(  # noqa: PLR0911
    components: Components | None, schema: SchemaType | None, *, is_param: bool = False
) -> str:
    """Get Python type from JSON Schema type."""
    if schema is None or isinstance(schema, bool):
        return "String"
    if schema.type:
        return _get_schema_from_type(components, schema, is_param=is_param)
    if schema_list := schema.all_of or schema.any_of or schema.one_of:
        # If is optional.
        if len(schema_list) == 2 and any(  # noqa: PLR2004
            isinstance(it, Schema) and it.type == "null" for it in schema_list
        ):
            not_null_schema = next(
                iter(
                    s for s in schema_list if isinstance(s, Schema) and s.type != "null"
                )
            )
            return f"Option<{rs_type(components, not_null_schema)}>"
        return " | ".join(rs_type(components, it) for it in schema_list)
    if schema.ref:
        if components is not None:
            resolved = components.resolve_reference(schema.ref)
            if (
                resolved is not None
                and not isinstance(resolved, bool)
                and resolved.enum
            ):
                return _get_type_from_value(next(iter(resolved.enum)))
        return re.sub(r"#/.*/(.*)", r"\1", schema.ref)
    return "String"


def _get_schema_from_type(  # noqa: PLR0911
    components: Components | None, schema: Schema, *, is_param: bool = False
) -> str:
    if schema.type == "array":
        return _get_array_type(components, schema)
    if schema.type == "object":
        return _get_object_type(components, schema)
    if isinstance(schema.type, list):
        return " | ".join(it if it != "integer" else "i32" for it in schema.type)
    if schema.type == "boolean":
        return "bool"
    if schema.type == "number":
        return "f32"
    if schema.type == "string":
        return "&str" if is_param else "String"
    if schema.type == "null":
        return "Option<()>"
    if schema.type == "integer":
        return "i32"
    return "&str" if is_param else "String"


def _get_array_type(components: Components | None, schema: Schema) -> str:
    if "prefix_items" in schema.model_fields_set:
        prefix_items = schema.prefix_items or []
        types = ", ".join(
            rs_type(components, prefix_item) for prefix_item in prefix_items
        )
        return f"({types})" if len(prefix_items) > 1 else types
    if schema.unique_items:
        return f"Vec<{rs_type(components, schema.items)}>"
    array_type = rs_type(components, schema.items)
    if "|" in array_type:
        return f"Vec<{rs_type(components, schema.items)}>"
    return f"Vec<{rs_type(components, schema.items)}>"


def _get_object_type(components: Components | None, schema: Schema) -> str:
    v_type = rs_type(components, schema.additional_properties)
    if v_type != "any":
        return f"HashMap<String, {v_type}>"
    return "HashMap<String, String>"


def get_enum_type(value: Any) -> str:
    """Get the rust type for an enum option."""
    if isinstance(value, str):
        return "&str"
    if isinstance(value, int):
        return "i32"
    return "f32"


def _get_type_from_value(value: float | str | bool | None) -> str:  # noqa: FBT001
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "i32"
    if isinstance(value, float):
        return "f32"
    return "String"


def _rust_name(name: str) -> str:
    return name if name not in keywords else f"{name}_"
