# mcp-info

CLI tool to list tools and schemas from MCP servers configured in an `mcp.json` file.

## Usage

The tool can be run directly with `uvx` (recommended) without installation:

```bash
uvx mcp-info path/to/mcp.json
```

Options:
- `--output PATH` - Write output to a file (default: stdout)
- `--show-output-schema` - Include output schemas in results
- `-t, --tool-names TOOL1 TOOL2 ...` - Filter to specific tool names

Output is JSON format, grouped by server name.

## Installation

Alternatively, the tool can be installed via pip:

```bash
pip install mcp-info
```

