import argparse
import asyncio
import json
import sys

from fastmcp import Client
from rich.console import Console


def load_config(mcp_json_path: str) -> dict:
    with open(mcp_json_path) as f:
        config = json.load(f)
    return config


async def get_tools(
    cfg: dict,
    *,
    tool_names: list[str] | None = None,
    show_output_schema: bool = False,
) -> tuple[dict, list[str]]:
    console = Console()
    grouped: dict[str, dict] = {}
    failures = []
    for server in cfg["mcpServers"]:
        server_cfg = {"mcpServers": {server: cfg["mcpServers"][server]}}
        try:
            client = Client(server_cfg)
            async with client:
                tools = await client.list_tools()

                console.print(f"Found {len(tools)} tools for {server}")

                for tool in tools:
                    name = getattr(tool, "name", None) or (tool.get("name") if isinstance(tool, dict) else str(tool))
                    if tool_names and name not in tool_names:
                        continue
                    description = getattr(tool, "description", None) or (
                        tool.get("description", "") if isinstance(tool, dict) else ""
                    )
                    input_schema = (
                        getattr(tool, "inputSchema", None) if not isinstance(tool, dict) else tool.get("inputSchema")
                    )
                    output_schema = (
                        getattr(tool, "outputSchema", None) if not isinstance(tool, dict) else tool.get("outputSchema")
                    )

                    group_key = server
                    if group_key not in grouped:
                        grouped[group_key] = {"tools": []}
                    tool_data = {
                        "name": name,
                        "description": description,
                        "input_schema": input_schema,
                    }
                    if show_output_schema:
                        tool_data["output_schema"] = output_schema
                    grouped[group_key]["tools"].append(tool_data)
            console.print(f"[green]✓[/green] Tools for {server} were successfully retrieved")
        except Exception as e:
            failures.append(f"{server}: {e}")

    return grouped, failures


def main():
    parser = argparse.ArgumentParser(description="List MCP tools and schemas from an mcp.json config")
    parser.add_argument("mcp_json_path", help="Path to the mcp.json file")
    parser.add_argument(
        "--output",
        dest="output_path",
        help="Path to output file (defaults to stdout if omitted)",
        default=None,
    )
    parser.add_argument(
        "--show-output-schema",
        action="store_true",
        help="Include output schema in the results",
    )
    parser.add_argument(
        "-t",
        "--tool-names",
        nargs="+",
        default=None,
        help="Filter to only show tools with these names (default: show all tools)",
    )
    args = parser.parse_args()
    cfg = load_config(args.mcp_json_path)

    output, failures = asyncio.run(
        get_tools(cfg, tool_names=args.tool_names, show_output_schema=args.show_output_schema)
    )
    console = Console()

    if args.output_path:
        with open(args.output_path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    else:
        console.print(json.dumps(output, indent=2))
    if failures:
        console.print("[red]✗[/red] Failed to get tools for the following servers:")
        for failure in failures:
            console.print(f"    [red]{failure}[/red]")
        sys.exit(1)
    else:
        console.print("[green]✓[/green] Tools for all servers were successfully retrieved")
