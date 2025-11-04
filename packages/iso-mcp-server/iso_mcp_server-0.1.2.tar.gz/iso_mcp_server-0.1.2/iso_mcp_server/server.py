
from __future__ import annotations
import os
import json
from typing import Any, Dict, List

# MCP server
from mcp.server.fastmcp import FastMCP

from iso_mcp_server.tooling import (
    register_workbook, openpyxl_sheet_names, sheet_to_model, apply_patches, ensure_workspace, WORKBOOKS,
)
from iso_mcp_server.rules_loader import load_rules, collect_rules
from iso_mcp_server.reporting import write_markdown, export_docx

RULES_PATH = os.environ.get("ISO_RULES_PATH", os.path.join(os.path.dirname(__file__), "..", "rules", "iso_rules.json"))
OUT_DIR = os.environ.get("ISO_OUT_DIR", os.path.join(os.path.dirname(__file__), "..", "workspace"))

mcp = FastMCP("iso-mcp")

# -------------------- TOOLS --------------------

@mcp.tool("xlsx_open")
def xlsx_open(path: str) -> Dict[str, Any]:
    wk_id = register_workbook(path)
    sheets = openpyxl_sheet_names(WORKBOOKS[wk_id])
    model_hint = {"hasEvidenceColumn": False, "hasDecisionsColumn": False}
    try:
        # quick sniff on 'Management Review'
        model = sheet_to_model(WORKBOOKS[wk_id], "Management Review")
        model_hint = model.get("hints", model_hint)
    except Exception:
        pass
    return {"workbook_id": wk_id, "sheets": sheets, "normalized_model_hint": model_hint}

@mcp.tool("xlsx_inspect")
def xlsx_inspect(workbook_id: str, sheet: str) -> Dict[str, Any]:
    path = WORKBOOKS[workbook_id]
    model = sheet_to_model(path, sheet)
    return {"sheet_model": model}

@mcp.tool("iso_rules_get_checklist")
def get_checklist(standards: List[str], section: str) -> Dict[str, Any]:
    rules = load_rules(RULES_PATH)
    lst = collect_rules(rules, standards, section)
    return {"rules": lst}

@mcp.tool("iso_rules_validate_clause")
def validate_clause(rule_id: str, row: Dict[str, Any]) -> Dict[str, Any]:
    # naive: find rule by id and validate Decision/Evidence presence
    rules = load_rules(RULES_PATH)
    # flatten rules
    all_rules = []
    for std, sections in rules.items():
        for sec, items in sections.items():
            all_rules.extend(items)
    rule = next((r for r in all_rules if r.get("id")==rule_id), None)
    if not rule:
        return {"conforms": False, "gaps": [f"Unknown rule {rule_id}"], "recommended_fixes": []}
    from iso_mcp_server.tooling import classify_gaps
    conforms, gaps, recs, severity = classify_gaps(row, rule)
    return {"conforms": conforms, "gaps": gaps, "recommended_fixes": recs, "severity": severity, "rule_id": rule_id}

@mcp.tool("evidence_extract_from_sheet")
def evidence_extract_from_sheet(workbook_id: str, sheet: str, row_idx: int) -> Dict[str, Any]:
    # simple heuristic scan: look for 'Actions' and 'Risks' sheets with matching row index offsets
    path = WORKBOOKS[workbook_id]
    candidates = []
    try:
        import pandas as pd
        xls = pd.ExcelFile(path, engine="openpyxl")
        for s in xls.sheet_names:
            if s.lower() in ("actions","risks"):
                df = pd.read_excel(xls, s).fillna("")
                # naive: look for keywords in row range around row_idx
                for i, row in df.iterrows():
                    row_text = " ".join(str(v) for v in row.values).lower()
                    if any(k in row_text for k in ["capa", "incident", "rca", "risk register", "rr-"]):
                        candidates.append(f"{s}!A{i+2} '{row_text[:40]}...'")
    except Exception:
        pass
    return {"candidate_evidence": candidates[:5]}

@mcp.tool("evidence_make_requests")
def evidence_make_requests(gaps: List[str]) -> Dict[str, Any]:
    reqs = []
    for g in gaps:
        g_low = g.lower()
        if "decision" in g_low:
            reqs.append("Record the management decision, responsible owner, and target completion date.")
        elif "evidence" in g_low:
            reqs.append("Attach Incident Log / NCR register / CAPA IDs or QMS change records relevant to this item.")
        else:
            reqs.append(f"Provide supporting evidence for: {g}")
    return {"requests": list(dict.fromkeys(reqs))}

@mcp.tool("xlsx_patch")
def xlsx_patch(workbook_id: str, sheet: str, patches: List[Dict[str, Any]]) -> Dict[str, Any]:
    path = WORKBOOKS[workbook_id]
    ensure_workspace(os.path.join(os.path.dirname(__file__), "..", "workspace"))
    out_path = apply_patches(path, sheet, patches)
    return {"patched": True, "new_file": os.path.basename(out_path)}

@mcp.tool("report_write_markdown")
def report_write_markdown(title: str, sections: List[Dict[str, str]]) -> Dict[str, Any]:
    ensure_workspace(OUT_DIR)
    md_path = write_markdown(title, sections, OUT_DIR)
    return {"md_path": os.path.basename(md_path)}

@mcp.tool("report_export_docx")
def report_export_docx(md_path: str, docx_path: str = "iso_validation_report.docx") -> Dict[str, Any]:
    ensure_workspace(OUT_DIR)
    full_md = os.path.join(OUT_DIR, md_path) if not os.path.isabs(md_path) else md_path
    docx_out = export_docx(full_md, OUT_DIR)
    return {"docx_path": os.path.basename(docx_out)}

@mcp.tool("files_save_to_workspace")
def files_save_to_workspace(path: str) -> Dict[str, Any]:
    # No-op in this sample; Studio typically handles saving.
    return {"saved": True, "workspace_path": f"workspace://{path}"}

def main():
    """
    Compatibility launcher:
    - Prefer FastMCP.run_websocket(host, port, path) if present
    - Else prefer FastMCP.run() (many builds auto-pick stdio)
    - Else fall back to stdio transport explicitly
    """
    # 1) Try native websocket (your original behavior)
    if hasattr(mcp, "run_websocket"):
        return mcp.run_websocket(host="0.0.0.0", port=8765, path="/ws")

    # 2) Generic runner (some FastMCP versions expose just .run())
    if hasattr(mcp, "run"):
        return mcp.run()

    # 3) Last resort: stdio transport (always available via mcp.server.stdio)
    import asyncio
    try:
        from mcp.server.stdio import stdio_server
    except Exception:
        # Some dists nest it differently; try alternate import
        from mcp.transport.stdio import stdio_server  # fallback if your package uses this path
    asyncio.run(stdio_server(mcp))


if __name__ == "__main__":
    main()
