
import json
from typing import Dict, Any, List

def load_rules(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def collect_rules(all_rules: Dict[str, Any], standards: List[str], section: str) -> List[Dict[str, Any]]:
    out = []
    for std in standards:
        if std in all_rules and section in all_rules[std]:
            out.extend(all_rules[std][section])
    return out
