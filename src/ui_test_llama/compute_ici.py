#!/usr/bin/env python3
"""
ICI calculator (semantic metric, no penalties) + interactive-action lister
with optional file outputs for metrics and action details.

Usage:
  python ici_actions.py --spec instruction.json --coverage 1.0 --list-actions \
    --out-metrics metrics.json --metrics-format json \
    --out-actions actions.csv --actions-format csv
"""

import json
import re
import argparse
import os
from typing import Any, Dict, List, Tuple

ACTION_TERMS = ["click", "hover", "select", "type", "switch", "choose", "download", "navigate"]

# Original terms (kept for reference)
DYNAMIC_TERMS_OLD = [
    # semantic dynamics: if any of these appear in an element_requirement entry, count it as dynamic
    "real-time", "live", "dynamic", "interactive",
    "chart", "graph", "plot", "visualization", "timeline", "trend",
    "update", "refresh", "distribution", "statistics", "analytics", "monitor"
]
KNOWN_ELEMENTS_OLD = [
    "stock information", "historical data", "financial metrics", "financial summary",
    "ownership distribution", "report customization", "stock performance",
    "company selector", "download button", "summary tab", "background color"
]

# Updated terms for AlphaVision Stock Analyzer
DYNAMIC_TERMS = [
    # semantic dynamics: if any of these appear in an element_requirement entry, count it as dynamic
    "real-time", "live", "dynamic", "interactive", "tracker", "analysis",
    "chart", "graph", "plot", "visualization", "timeline", "trend", "history",
    "update", "refresh", "distribution", "statistics", "analytics", "monitor",
    "search", "results", "information", "data", "ratio", "yield", "cap"
]
# NOTE: KNOWN_ELEMENTS updated for AlphaVision Stock Analyzer elements
# Based on test_response_000002-1_final_filtered_cleaned.json element requirements
KNOWN_ELEMENTS = [
    "portfolio tracker button", "search stocks card", "search results card", 
    "analytics section", "apple inc information card", "overview tab", "overview card",
    "news tab", "ai analysis tab", "timeframe buttons", "profile settings card",
    "welcome card", "navigation tabs card", "market cap card", "volume card",
    "p/e ratio card", "dividend yield card", "price history chart", 
    "generate report card", "customize report card"
]

# ---------- helpers ----------

def ensure_parent_dir(path: str):
    """Create parent directory if not exists (for file outputs)."""
    if not path:
        return
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

def collect_text(obj: Any) -> str:
    if isinstance(obj, dict):
        return " ".join(collect_text(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(collect_text(v) for v in obj)
    return str(obj)

def format_table(rows: List[Tuple[str, str]], header=("Metric", "Value")) -> str:
    col1 = max(len(header[0]), max(len(r[0]) for r in rows)) if rows else len(header[0])
    col2 = max(len(header[1]), max(len(str(r[1])) for r in rows)) if rows else len(header[1])
    line = "+" + "-"*(col1+2) + "+" + "-"*(col2+2) + "+"
    out = [line, f"| {header[0].ljust(col1)} | {header[1].ljust(col2)} |", line]
    for k, v in rows:
        out.append(f"| {k.ljust(col1)} | {str(v).ljust(col2)} |")
    out.append(line)
    return "\n".join(out)

def split_into_sentences(text: str) -> List[str]:
    # simple sentence splitter: split on . ! ? or newline; keep words together
    parts = re.split(r'(?<=[\.\!\?])\s+|\n+', (text or "").strip())
    return [p.strip() for p in parts if p.strip()]

def find_actions_in_text(text: str) -> List[Tuple[str, str]]:
    """Return list of (verb, sentence) for each action term hit in text."""
    hits: List[Tuple[str, str]] = []
    if not text:
        return hits
    sentences = split_into_sentences(text)
    for sent in sentences:
        low = sent.lower()
        for verb in ACTION_TERMS:
            # word boundary to avoid matching 'clicking' unless you want it; change to r'\bclick' for stems
            if re.search(rf"\b{verb}\b", low):
                hits.append((verb, sent))
    return hits

def refs_in(text: str) -> List[str]:
    return [n for n in KNOWN_ELEMENTS if n in (text or "").lower()]

def write_json(path: str, data):
    ensure_parent_dir(path)
    with open(path, "a", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_jsonl(datas, out_file, mode='w'):
    """Save data to JSONL file"""
    with open(out_file, mode, encoding='utf-8') as f:
        for data in datas:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

def write_csv_dicts(path: str, rows: List[Dict[str, Any]], field_order: List[str] = None):
    ensure_parent_dir(path)
    if not rows:
        # write header only if field_order is provided; otherwise write empty file
        with open(path, "w", encoding="utf-8") as f:
            if field_order:
                f.write(",".join(field_order) + "\n")
        return
    # Determine columns
    if field_order is None:
        cols = list({k for row in rows for k in row.keys()})
    else:
        cols = field_order
    # Write
    with open(path, "a", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for row in rows:
            vals = []
            for c in cols:
                v = row.get(c, "")
                # Escape CSV basics
                s = str(v).replace('"', '""')
                if any(ch in s for ch in [",", "\n", '"']):
                    s = f'"{s}"'
                vals.append(s)
            f.write(",".join(vals) + "\n")

# ---------- core ----------

def calculate_metrics_and_actions(spec: Dict[str, Any], step_num: int, coverage_final: float = 0.0):
    # counts
    elements = spec.get("element_requirement", []) or []
    n_elements = len(elements)

    tests: List[Dict[str, Any]] = []
    for cat, arr in (spec.get("test_cases") or {}).items():
        for t in arr:
            tt = dict(t)
            tt["_category"] = cat
            tests.append(tt)
    n_tests = len(tests)

    # interactive actions — detail collection by test & field
    interactive_actions_total = 0
    action_details: List[Dict[str, str]] = []
    for t in tests:
        tcid = t.get("id") or "(no-id)"
        # scan objective, expected_results, and each procedure step
        fields = [
            ("objective", t.get("objective", "")),
            ("expected_results", t.get("expected_results", "")),
            ("procedure", " ".join(t.get("procedure", []) if isinstance(t.get("procedure"), list) else [t.get("procedure","")]))
        ]
        for field_name, field_text in fields:
            for verb, sentence in find_actions_in_text(field_text):
                action_details.append({
                    "test_id": tcid,
                    "field": field_name,
                    "verb": verb,
                    "sentence": sentence
                })
                interactive_actions_total += 1

    # dynamics (semantic, generalized keywords above)
    dynamic_components = sum(
        1 for e in elements if any(term in e.lower() for term in DYNAMIC_TERMS)
    )

    # cross ref tests
    cross_refs = 0
    for t in tests:
        txt = " ".join([
            t.get("expected_results","") or "",
            " ".join(t.get("procedure", [])) if isinstance(t.get("procedure"), list) else str(t.get("procedure","") or "")
        ])
        if len(set(refs_in(txt))) >= 2:
            cross_refs += 1

    # scores
    S = min(1.0, 0.5*(n_elements/15.0) + 0.5*(n_tests/20.0))
    I = min(1.0, interactive_actions_total/20.0)
    D = min(1.0, dynamic_components/6.0)
    C = min(1.0, cross_refs/10.0)
    G = min(1.0, max(0.0, coverage_final))

    ici = 100*(0.35*S + 0.25*I + 0.15*D + 0.15*G + 0.10*C)

    metrics = {
        "Step": step_num,
        "Elements": n_elements,
        "Test Cases": n_tests,
        "Interactive actions": interactive_actions_total,
        "Dynamic components": dynamic_components,
        "Cross-referencing tests": cross_refs,
        "Coverage (final)": round(G, 3),
        "Size score": round(S, 3),
        "Interactivity score": round(I, 3),
        "Dynamic score": round(D, 3),
        "Coupling score": round(C, 3),
        "ICI": round(ici, 1)
    }
    return metrics, action_details

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="ICI + interactive action lister (with file outputs).")
    # ap.add_argument("--spec", required=True, help="Path to instruction/spec JSON")
    ap.add_argument("--spec_dir", required=True, help="Path to instruction/spec JSON")
    ap.add_argument("--coverage", type=float, default=0.0, help="Coverage G in [0,1]")
    ap.add_argument("--list-actions", action="store_true", help="List each interactive action with test context")

    # Output options
    ap.add_argument("--out-metrics", help="Path to write metrics (JSON/CSV based on --metrics-format)")
    ap.add_argument("--metrics-format", choices=["json", "csv"], default="json", help="File format for metrics output")

    ap.add_argument("--out-actions", help="Path to write interactive actions (JSON/CSV based on --actions-format)")
    ap.add_argument("--actions-format", choices=["json", "csv"], default="json", help="File format for actions output")

    args = ap.parse_args()
    if args.spec_dir:
        res_list = []
        for s in sorted(os.listdir(args.spec_dir)):
            with open(os.path.join(args.spec_dir, s), "r", encoding="utf-8") as f:
                spec = json.load(f)
            
            step_num = s.split("_")[-1].replace("multistep/","").split(".json")[0]

            metrics, action_details = calculate_metrics_and_actions(spec, step_num, coverage_final=args.coverage)

            # Print metrics table to console
            ordered = [
                ("Step Num", metrics["Step"]),
                ("Elements", metrics["Elements"]),
                ("Test Cases", metrics["Test Cases"]),
                ("Interactive actions", metrics["Interactive actions"]),
                ("Dynamic components", metrics["Dynamic components"]),
                ("Cross-referencing tests", metrics["Cross-referencing tests"]),
                ("Coverage (final)", metrics["Coverage (final)"]),
                ("Size score", metrics["Size score"]),
                ("Interactivity score", metrics["Interactivity score"]),
                ("Dynamic score", metrics["Dynamic score"]),
                ("Coupling score", metrics["Coupling score"]),
            ]
            print(format_table(ordered, header=("Metric", "Value")))
            print(f"\nICI = {metrics['ICI']}")

            if args.list_actions:
                if not action_details:
                    print("\nNo interactive actions found.")
                else:
                    print("\nInteractive Action Details:")
                    col_test = max(10, max(len(x["test_id"]) for x in action_details))
                    col_field = max(12, max(len(x["field"]) for x in action_details))
                    col_verb = max(8, max(len(x["verb"]) for x in action_details))
                    line = "+" + "-"*(col_test+2) + "+" + "-"*(col_field+2) + "+" + "-"*(col_verb+2) + "+" + "-"*(60) + "+"
                    print(line)
                    print("| {:{}} | {:{}} | {:{}} | {:<60} |".format("Test ID", col_test, "Field", col_field, "Verb", col_verb, "Sentence"))
                    print(line)
                    for x in action_details:
                        sent = x["sentence"]
                        display = (sent[:57] + "...") if len(sent) > 60 else sent
                        print("| {:{}} | {:{}} | {:{}} | {:<60} |".format(
                            x["test_id"], col_test, x["field"], col_field, x["verb"], col_verb, display))
                    print(line)
            res_list.append(metrics)
    # ---- File outputs ----
    if args.out_metrics:
        if args.metrics_format == "json":
            write_jsonl(res_list, args.out_metrics)
        else:
            # CSV needs a list of dicts; wrap metrics
            write_csv_dicts(args.out_metrics, res_list, field_order=[
                "Elements","Test Cases","Interactive actions","Dynamic components",
                "Cross-referencing tests","Coverage (final)","Size score",
                "Interactivity score","Dynamic score","Coupling score","ICI"
            ])
        print(f"\nSaved metrics to: {args.out_metrics}")

    # if args.out_actions:
    #     if args.actions_format == "json":
    #         write_json(args.out_actions, action_details)
    #     else:
    #         # flatten action_details to CSV
    #         write_csv_dicts(args.out_actions, action_details, field_order=[
    #             "test_id","field","verb","sentence"
    #         ])
    #     print(f"Saved interactive actions to: {args.out_actions}")

if __name__ == "__main__":
    main()
