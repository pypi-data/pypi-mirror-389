# ISO MCP Server

A lightweight MCP server exposing tools for validating **ISO 45001 & 9001** Management Review spreadsheets
(e.g., `MoM.xlsx`) and generating auto-patched workbooks + reports.

## Quick start (with `uv`)
```bash
uv venv
uv pip install -e .
uv run iso-mcp
```
The server will print a WebSocket URL (or run as stdio). In AutoGen Studio 0.7.5, add it as an MCP tool:
- **Protocol:** WebSocket
- **URL:** `ws://localhost:8765/ws` (default in this sample)
- Or run stdio mode (see code comment in `server.py`) and select "Stdio" in Studio.

## Tools implemented
- xlsx_open
- xlsx_inspect
- iso_rules.get_checklist
- iso_rules.validate_clause
- evidence.extract_from_sheet
- evidence.make_requests
- xlsx_patch
- report.write_markdown
- report.export_docx
- files.save_to_workspace (no-op passthrough in this sample, since Studio saves files itself)

## Files
- `rules/iso_rules.json` — a minimal seed ruleset. Extend/replace with your authority text.
- `workspace/` — output artifacts land here by default.