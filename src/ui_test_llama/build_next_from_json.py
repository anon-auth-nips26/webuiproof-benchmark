#!/usr/bin/env python3
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path
import os

# ---------------- helpers ----------------
def run(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=cwd)

def ensure_clean_dir(path: Path):
    if path.exists(): shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

def read_json(path: Path) -> dict:
   # Read JSON file (each line is a separate JSON object)
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Error parsing line: {e}")
                    continue
    return data
    
def write(p: Path, s: str, binary=False):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(s) if binary else p.write_text(s, encoding="utf-8")
    print("wrote", p)


def cleanup_folders(base_path, full_folder=False):
    """
    Clean up folders by keeping only 'out/' directories and removing all other files.
    If no 'out/' directory exists, delete all files in the folder.
    
    Args:
        base_path (str): Path to the base directory containing subfolders
    """

    print(f"\nProcessing: {base_path}")
        
    # Get all items in the subdirectory
    items = list(base_path.iterdir())
    out_dir = base_path / 'out'
    
    stats = {
        'total_itmes': len(items),
        'folders_with_out': 0,
        'folders_without_out': 0,
        'files_deleted': 0,
        'folders_deleted': 0
    }

    if out_dir.exists() and out_dir.is_dir():
        # Keep only the 'out' directory, delete everything else
        stats['folders_with_out'] += 1
        print(f"  ✓ Found 'out/' directory - keeping it, removing {len(items) - 1} other items")
        
        for item in items:
            if item.name != 'out':
                try:
                    if item.is_file():
                        item.unlink()
                        stats['files_deleted'] += 1
                        print(f"    - Deleted file: {item.name}")
                    elif item.is_dir():
                        shutil.rmtree(item)
                        stats['folders_deleted'] += 1
                        print(f"    - Deleted folder: {item.name}/")
                except Exception as e:
                    print(f"    ✗ Error deleting {item.name}: {e}")
    else:
        # No 'out' directory found, delete all files
        stats['folders_without_out'] += 1
        print(f"  ✗ No 'out/' directory found - deleting all {len(items)} items")
        
        for item in items:
            try:
                if item.is_file():
                    item.unlink()
                    stats['files_deleted'] += 1
                    print(f"    - Deleted file: {item.name}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    stats['folders_deleted'] += 1
                    print(f"    - Deleted folder: {item.name}/")
            except Exception as e:
                print(f"    ✗ Error deleting {item.name}: {e}")
    
    if full_folder:
        shutil.rmtree(base_path)
        stats['folders_deleted'] += 1
        print(f"    - Deleted folder: {base_path.name}/")
    return stats

# --------- TSX extraction / sanitizing ----------
def _sanitize_tsx(tsx: str) -> str:
    # drop generator tail blocks
    for mark in ["\n// Zod Schema", "\n/* Zod Schema", "\nexport const Schema"]:
        if mark in tsx:
            tsx = tsx.split(mark, 1)[0]
    # fix Pythonic literals if present
    tsx = re.sub(r"{\s*n+\s+(date:)", r"{ \1", tsx)
    tsx = re.sub(r"\bFalse\b", "false", tsx)
    tsx = re.sub(r"\bTrue\b", "true", tsx)
    tsx = re.sub(r"\bNone\b", "null", tsx)
    return tsx.strip()

def extract_code(payload: dict) -> str:
    candidates = []
    try:
        v = payload["dialog"][0].get("prediction_texts")
        if isinstance(v, str): candidates.append(v)
    except Exception: pass
    v = payload.get("metadata", {}).get("code")
    index = payload.get("metadata", {}).get("prompt_index")
    prompt = payload.get("metadata", {}).get("prompt")
    if isinstance(v, str): candidates.append(v)
    code_raw = payload.get("Schema", {}).get("code") if isinstance(payload.get("Schema"), dict) else None
    if isinstance(code_raw, str):
        try: candidates.append(bytes(code_raw, "utf-8").decode("unicode_escape"))
        except Exception: candidates.append(code_raw)

    for src in candidates:
        if not isinstance(src, str): continue
        clean = _sanitize_tsx(src)
        # Optional: auto-rewrite CandlestickChart
        # if re.search(r"from\s+['\"]recharts['\"]", clean) and "CandlestickChart" in clean:
        #     clean = _rewrite_candlestick_to_area(clean)
        # if "export default function" in clean:
        #     return clean
        if re.search(r"\bexport\s+default\b", clean):
            return clean, index, prompt
    raise ValueError("Could not find a valid TSX page in JSON.")

def _rewrite_candlestick_to_area(tsx: str) -> str:
    """
    - Remove CandlestickChart from recharts import list
    - Ensure AreaChart and Area are imported
    - Replace JSX tags <CandlestickChart .../> and </CandlestickChart> with AreaChart
    """
    # 1) rewrite import {...} from 'recharts'
    #    capture the import spec and rebuild it
    pat = re.compile(r"""import\s*{\s*([^}]+)\s*}\s*from\s*['"]recharts['"];?""")
    def fix_import(m):
        spec = m.group(1)
        names = [x.strip() for x in spec.split(",") if x.strip()]
        names = [n for n in names if n != "CandlestickChart"]
        # ensure AreaChart & Area present
        for need in ["AreaChart", "Area"]:
            if need not in names:
                names.append(need)
        # dedupe while keeping order
        seen = set()
        deduped = []
        for n in names:
            if n not in seen:
                seen.add(n)
                deduped.append(n)
        return f"import {{ {', '.join(deduped)} }} from 'recharts'"

    tsx = pat.sub(fix_import, tsx)

    # 2) replace JSX tags
    #    opening or self-closing: <CandlestickChart ...> / <CandlestickChart ... />
    tsx = re.sub(r"<\s*CandlestickChart(\b[^>]*)>", r"<AreaChart\1>", tsx)
    tsx = re.sub(r"<\s*/\s*CandlestickChart\s*>", r"</AreaChart>", tsx)

    return tsx

# def patch_extra_braces(code: str) -> str:
#     """
#     Fix accidental '}}' after object literals in arrays like:
#       { metric: 'Top 10', value: '30%' }},
#     → { metric: 'Top 10', value: '30%' },
#     """
#     original = code
#     # 1) Common case: "}},"
#     fixed = re.sub(r"\}\},", "},", code)

#     # 2) '}}' before a line comment: make it '}, ' (preserve comment)
#     fixed = re.sub(r"\}\}\s*(?=//)", "}, ", fixed)

#     # 3) '}}' before next object/identifier on same line: add comma after '}'
#     fixed = re.sub(r"\}\}\s*(?=\{)", "}, ", fixed)          # next token is "{"
#     fixed = re.sub(r"\}\}\s*(?=[A-Za-z_])", "}, ", fixed)   # next token is identifier

#     # 4) Collapse accidental triple braces "}}}" → "}}"
#     fixed = re.sub(r"\}\}\}", "}}", fixed)

#     if fixed != original:
#         # Find the line numbers where this happened
#         for i, (o_line, f_line) in enumerate(zip(original.splitlines(), fixed.splitlines()), start=1):
#             if o_line != f_line and "}}" in o_line:
#                 print(f"⚠️  Fixed stray '}}' at line {i}:")
#                 print(f"   before: {o_line.strip()}")
#                 print(f"   after : {f_line.strip()}")

#     return fixed

def formatted_json(init_code, edit_code, output_file, prompt_index=None, prompt=None):

    # If prompt_index is provided, include it in the JSON data
    json_data = {
        "dialog": [{"init_code": init_code}, {"edit_code": edit_code}],
        "metadata": 
        {
            "prompt_index": prompt_index,
            'prompt': prompt
        }
    }
    
    try:
        with open(output_file, 'a', encoding="utf-8") as f:   
            f.write(json.dumps(json_data) + "\n")
        print(f"Successfully saved text to {output_file}")
    except Exception as e:
        print(f"Error writing to file {output_file}: {e}")

def ensure_tsx_component_shell(code: str) -> str:
    """Ensure there's a default-exported component that wraps the JSX."""
    # Check for any export default pattern (function, const, class, etc.)
    if re.search(r"\bexport\s+default\b", code):
        return code
    
    # Check if code starts with imports (indicating it's already a complete component)
    if re.search(r"^\s*import\s+", code, flags=re.M):
        return code
    
    # Try to wrap top-level JSX with a minimal component if missing
    # Only if we see a top-level <div ... right after a return-like gap
    if re.search(r"^\s*<div[\s>]", code, flags=re.M):
        return (
            "import React from 'react';\n\n"
            "export default function IndexPage() {\n"
            "  return (\n" + code + "\n  );\n}\n"
        )
    return code

def patch_unbalanced_return_parens(code: str) -> str:
    """
    If there's a 'return (' without a matching ');' add it at EOF.
    Also fixes the common 'return (' followed by closing '}' (missing ');').
    """
    # Count naive parens around 'return ('
    opens = len(re.findall(r"return\s*\(", code))
    closes = len(re.findall(r"\)\s*;", code))
    if opens > closes:
        # If the last non-space doesn't end with ');', append it
        if not re.search(r"\)\s*;\s*\}\s*$", code) and not re.search(r"\)\s*;\s*$", code):
            code = re.sub(r"\s*$", "\n  );\n}\n", code)
    return code

def patch_unclosed_template_literals(code: str) -> str:
    """
    Rough guard for unbalanced backticks: if odd count, append a closing backtick.
    """
    if code.count("`") % 2 == 1:
        code = code + "`"
    return code

def patch_extra_braces(code: str) -> str:
    """
    Fix stray '}}' after object literals and malformed JSX object syntax.
    Priority: Fix JSX comma-separated attributes first, then other patterns.
    """
    original = code
    changes_made = []
    
    # PRIORITY 1: Fix JSX object attributes with comma-separated syntax (most critical)
    # This must run first before other patterns interfere
    
    # Step 1: Fix any JSX object that ends with single } followed by comma and another attribute
    # Match: {{ ... }, nextAttr= -> {{ ... }} nextAttr=
    pattern1_matches = re.findall(r'(\{\{[^}]*)\}\s*,\s*([a-zA-Z_][a-zA-Z0-9_]*\s*=)', code)
    new_code = re.sub(r'(\{\{[^}]*)\}\s*,\s*([a-zA-Z_][a-zA-Z0-9_]*\s*=)', r'\1}} \2', code)
    if new_code != code:
        changes_made.append(f"Fixed JSX object single brace before comma ({len(pattern1_matches)} matches)")
        code = new_code
    
    # Step 2: Remove commas between JSX attributes (they should be spaces)
    # Match: }} , nextAttr= -> }} nextAttr=
    new_code = re.sub(r'(\}\})\s*,\s*([a-zA-Z_][a-zA-Z0-9_]*\s*=)', r'\1 \2', code)
    if new_code != code:
        changes_made.append("Removed commas between JSX attributes")
        code = new_code
    
    # Step 3: Fix JSX object that ends with single } before />
    # Match: {{ ... }/> -> {{ ... }}/> (handles multi-line)
    new_code = re.sub(r'(\{\{[^}]*)\}\s*/>', r'\1}}/>',  code, flags=re.DOTALL)
    if new_code != code:
        changes_made.append("Fixed JSX object single brace before self-closing")
        code = new_code
    
    # FINAL FIX: Comprehensive pattern for missing closing braces
    # This pattern should catch all JSX attributes that are missing a closing brace
    # Pattern: word={{ anything_except_} }/> -> word={{ anything_except_} }}/>
    new_code = re.sub(r'(\w+\s*=\s*\{\{[^}]*)\}\s*/>', r'\1}}/>',  code, flags=re.DOTALL)
    if new_code != code:
        changes_made.append("FINAL: Fixed JSX attributes missing closing brace")
        code = new_code
    
    # Step 5: Fix JSX attributes with missing closing brace before closing tag
    # Match: attr={{ ... }> -> attr={{ ... }}> (handles multi-line)
    new_code = re.sub(r'(\w+\s*=\s*\{\{[^}]*)\}\s*>', r'\1}}>', code, flags=re.DOTALL)
    if new_code != code:
        changes_made.append("Fixed JSX attribute missing closing brace before closing tag")
        code = new_code
    
    # PRIORITY 2: Other JSX patterns (DISABLED - these were breaking correct JSX)
    # The patterns below were incorrectly converting well-formed JSX to malformed comma-separated format
    
    # SAFE PATTERNS ONLY:
    
    # Fix JSX attribute patterns: key={`item-${index}` }} -> key={`item-${index}`}
    new_code = re.sub(r"(\{`[^`]*`)\s*\}\s*\}", r"\1}", code)
    if new_code != code:
        changes_made.append("Fixed JSX attribute template literal '}}' pattern")
        code = new_code
    
    # Fix template literal at end of JSX expression: {`...`} }} -> {`...`}
    new_code = re.sub(r"(\{`[^`]*`\})\s*\}\}", r"\1", code)
    if new_code != code:
        changes_made.append("Fixed JSX template literal end '}}' pattern")
        code = new_code
    
    # DISABLED - This pattern was breaking correct JSX:
    # # Fix malformed JSX object attributes missing closing braces
    # # Pattern: prop={{ key: value }, otherProp={...} -> prop={{ key: value }} otherProp={...}
    # new_code = re.sub(r"(\{\{\s*[^}]+)\s*\}\s*,\s*([a-zA-Z_][a-zA-Z0-9_]*\s*=)", r"\1 }} \2", code)
    
    # DISABLED - This pattern was breaking correct JSX:
    # # Fix JSX attributes ending with }, instead of }}
    # # Pattern: contentStyle={{ ... }, labelStyle={{ ... } -> contentStyle={{ ... }}, labelStyle={{ ... }}
    # new_code = re.sub(r"(\{\{[^}]*)\}\s*,\s*([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\{\{)", r"\1 }}, \2", code)
    
    # General '}},' -> '},'
    new_code = re.sub(r"\}\},", "},", code)
    if new_code != code:
        changes_made.append("Fixed general '}},")
        code = new_code
    
    # '}} // comment' -> '}, // comment'
    new_code = re.sub(r"\}\}\s*(?=//)", "}, ", code)
    if new_code != code:
        changes_made.append("Fixed '}} // comment'")
        code = new_code
    
    # DISABLED - These patterns were breaking correct JSX:
    # The pattern below was incorrectly converting well-formed multi-line JSX attributes to comma-separated format
    
    # '}}{' -> '}, {'  (This one might be safe)
    new_code = re.sub(r"\}\}\s*(?=\{)", "}, ", code)
    if new_code != code:
        changes_made.append("Fixed '}}{' pattern")
        code = new_code
        
    # DISABLED - This was the main culprit breaking JSX:
    # '}}<ident>' -> '}, ident' 
    # This was converting "}} \nlabelStyle=" to "}, labelStyle=" which breaks JSX
    # new_code = re.sub(r"\}\}\s*(?=[A-Za-z_])", "}, ", code)
    # if new_code != code:
    #     changes_made.append("Fixed '}}ident' pattern")
    #     code = new_code
    
    # '}}' followed by whitespace and ']' -> '}' followed by whitespace and ']'
    new_code = re.sub(r"\}\}\s*(?=\])", "}", code)
    if new_code != code:
        changes_made.append("Fixed '}}]' pattern")
        code = new_code
    
    # '}}' followed by ' />' (JSX self-closing tag)
    new_code = re.sub(r"\}\}\s*(?=\s*/>)", "}", code)
    if new_code != code:
        changes_made.append("Fixed '}} />' pattern")
        code = new_code
    
    # collapse '}}}' -> '}}'
    new_code = re.sub(r"\}\}\}", "}}", code)
    if new_code != code:
        changes_made.append("Fixed '}}}' pattern")
        code = new_code
    
    if changes_made:
        print(f"patch_extra_braces made changes: {', '.join(changes_made)}")
    else:
        print("patch_extra_braces: no changes needed")
    
    return code

def fix_missing_jsx_braces(code: str) -> str:
    """
    Dedicated function to fix missing closing braces in JSX attributes.
    This runs after all other patches to ensure it catches any remaining issues.
    """
    original = code
    
    # Fix JSX attributes missing closing brace: word={{ ... }/> -> word={{ ... }}/>
    code = re.sub(r'(\w+\s*=\s*\{\{[^}]*)\}\s*/>', r'\1}}/>',  code, flags=re.DOTALL)
    
    # Fix function attributes missing closing brace: word={(func) => ...}/> -> word={(func) => ...}/>
    code = re.sub(r'(\w+\s*=\s*\{[^}]*)\}\s*/>', r'\1}/>',  code, flags=re.DOTALL)
    
    if code != original:
        print("fix_missing_jsx_braces: Fixed missing closing braces in JSX attributes")
    
    return code

def fix_typescript_types(code: str) -> str:
    """
    Fix common TypeScript type issues in generated code.
    """
    original = code
    
    # Fix Recharts Pie label function parameter types
    # The parameters cx, cy, midAngle, innerRadius, outerRadius, percent need type annotations
    pattern = r'label=\{\(\{\s*cx,\s*cy,\s*midAngle,\s*innerRadius,\s*outerRadius,\s*percent,?\s*\}\) => \{'
    replacement = r'label={({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {'
    code = re.sub(pattern, replacement, code, flags=re.DOTALL)
    
    if code != original:
        print("fix_typescript_types: Fixed TypeScript type annotations")
    
    return code

def stabilize_jsx_block(code: str):
    before = code
    code = patch_extra_braces(code)
    code = patch_unclosed_template_literals(code)
    code = patch_unbalanced_return_parens(code)
    code = ensure_tsx_component_shell(code)
    # Apply patch_extra_braces again in case other functions introduced new issues
    code = patch_extra_braces(code)
    # Final fix for missing JSX braces
    code = fix_missing_jsx_braces(code)
    # Fix TypeScript type issues
    code = fix_typescript_types(code)
    # if code != before:
    #     index_path.write_text(code, encoding="utf-8")
    return code

def patch_chart_types_general(code: str) -> str:
    """
    General hardening for Recharts data typing:
    - Ensure a permissive 'AnyDatum = Record<string, string | number>' exists.
    - Widen any interface/type ending with 'Data', 'DataPoint', or 'Point' to include AnyDatum.
    - Relax strict target aliases like 'type ChartDataInput = { ... }' to Record<...>.
    Returns code if file modified.
    """
    original = code
    changed = False

    # 1) Ensure AnyDatum exists once
    if "type AnyDatum = Record<string, string | number>" not in code:
        insert_after = re.search(r"(^import[^\n]*\n)+", code, flags=re.M)
        ins = "type AnyDatum = Record<string, string | number>;\n"
        if insert_after:
            code = code[:insert_after.end()] + ins + code[insert_after.end():]
        else:
            code = ins + code
        changed = True

    # 2) Widen interfaces whose names end with Data|DataPoint|Point
    def widen_interface(m):
        head, extends, brace = m.groups()
        extends = extends or ""
        if "AnyDatum" in extends:
            return m.group(0)
        return f"{head}{(extends.rstrip()+', ' if extends else ' extends ')}AnyDatum {brace}"

    code_new = re.sub(
        r"(interface\s+\w*(?:DataPoint|Point|Data)\s*)(extends\s+[^:{]+)?(\{)",
        widen_interface,
        code
    )
    if code_new != code:
        code, changed = code_new, True

    # 3) Convert type aliases (ending with Data|DataPoint|Point) to interfaces that extend AnyDatum
    def alias_to_iface(m):
        name, body = m.group(1), m.group(2)
        return f"interface {name} extends AnyDatum {{{body}}}"

    code_new = re.sub(
        r"type\s+(\w*(?:DataPoint|Point|Data))\s*=\s*\{([\s\S]*?)\}\s*;",
        alias_to_iface,
        code
    )
    if code_new != code:
        code, changed = code_new, True

    # 4) Relax common “target” aliases used in wrappers
    #    e.g., type ChartDataInput = { ... } → Record<string, string | number>
    code_new = re.sub(
        r"(type\s+\w*(?:ChartData|DataInput|Series|Datum)\w*\s*=\s*)\{[\s\S]*?\}",
        r"\1Record<string, string | number>",
        code
    )
    if code_new != code:
        code = code_new
        changed = True

    return code, changed


def patch_pie_label_percent_unknown(code: str) -> str:
    """
    Harden <Pie label={({ name|region, percent }) => ...}> usages:
    - Add explicit param types: { name|region?: string; percent?: number }
    - Coerce percent to number before arithmetic
    - Replace `${(percent * 100).toFixed(0)}%` and `${percent * 100}%` with a safe variant

    Returns: (new_code: str, changed: bool)
    """
    original = code
    changed = False

    if "PieLabelRenderProps" not in code and "from 'recharts'" in code:
        code = re.sub(
            r"(import\s*{[^}]*)(}\s*from\s*['\"]recharts['\"]\s*;)",
            r"\1, PieLabelRenderProps\2",
            code,
            count=1
        )


    # replace destructured label with typed function using payload/name and safe percent
    code = re.sub(
        r'label=\{\(\{\s*(?:name|region)\s*,\s*percent\s*\}\)\s*=>\s*',
        "label={(props: PieLabelRenderProps) => { const payload = (props.payload as any) || {}; const label = (payload.region ?? props.name ?? ''); const pct = Number(props.percent ?? 0); return ",
        code,
    )
    # close the injected function where the original arrow returned a template string
    code = re.sub(
        r'(`[^`]*`)\s*\}',
        r'\1 }}',
        code,
    )
    
    # 1) Add explicit param types for either `name` or `region` + percent
    #    label={({ name, percent }) => ...}  OR  label={({ region, percent }) => ...}
    code_new = re.sub(
        r'label=\{\(\{\s*(name|region)\s*,\s*percent\s*\}\)\s*=>\s*',
        r'label={({ \1, percent }: { \1?: string; percent?: number }) => ',
        code,
    )
    if code_new != code:
        code = code_new
        changed = True

    # 2) Ensure arithmetic uses Number(percent ?? 0)
    #    Replace `(percent ?? 0) * 100` → `Number(percent ?? 0) * 100`
    code_new = re.sub(
        r'\(\s*percent\s*\?\?\s*0\s*\)\s*\*\s*100',
        r'Number(percent ?? 0) * 100',
        code,
    )
    if code_new != code:
        code = code_new
        changed = True

    #    Replace `percent * 100` (but not already within Number(...)) → `Number(percent ?? 0) * 100`
    #    Negative lookbehind avoids double-wrapping if already Number(…).
    code_new = re.sub(
        r'(?<!Number\()\bpercent\s*\*\s*100\b',
        r'Number(percent ?? 0) * 100',
        code,
    )
    if code_new != code:
        code = code_new
        changed = True

    if code != original:
        # index_path.write_text(code, encoding="utf-8")
        changed = True
        return code, changed
    return original, changed

# ---------------- scaffold ----------------
def npm_bootstrap(project: Path, needs_recharts: bool):
    run(["npm", "init", "-y"], cwd=project)
    run(["npm", "install", "react@18.3.1", "react-dom@18.3.1", "next@15.5.4"], cwd=project)
    run(["npm", "install", "@heroicons/react"], cwd=project)
    run(["npm", "install", "lucide-react"], cwd=project)  # Add lucide-react dependency
    # Tailwind v3 stack

    # # OLD
    # run(["npm", "install", "-D", "typescript", "@types/react", "@types/node", 
    #     "tailwindcss", "@tailwindcss/postcss", "postcss"], cwd=project)

    # NEW (adds prettier, autoprefixer)
    run([
        "npm", "install", "-D",
        "typescript", "@types/react", "@types/node", 
        "tailwindcss@3", "postcss", "autoprefixer",  
        "prettier"
    ], cwd=project)

    if needs_recharts:
        run(["npm", "install", "recharts"], cwd=project)

def make_files(project: Path, tsx_code: str):

    init_code = tsx_code
    # next static export
    write(project/"next.config.mjs",
"""/** @type {import('next').NextConfig} */
const nextConfig = { output: 'export' };
export default nextConfig;
""")
    # tsconfig
    write(project/"tsconfig.json",
"""{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",       // or "react-jsx"
    "allowJs": true,
    "skipLibCheck": true,
    "incremental": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
""")
    # next-env
    write(project/"next-env.d.ts",
"""/// <reference types="next" />
/// <reference types="next/image-types/global" />
// NOTE: This file should not be edited
""")
    # tailwind v3 config (classic content scan)
    write(project/"tailwind.config.js",
"""/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{ts,tsx,js,jsx}",
    "./components/**/*.{ts,tsx,js,jsx}",
    "./styles/**/*.css"
  ],
  theme: {
    extend: {
      colors: {
        navy: { 50: "#eef2ff", 500: "#1e3a8a", 600: "#1e40af", 900: "#0b1e3d" }
      }
    }
  },
  plugins: [],
};
""")
    # postcss v3 style
    write(project/"postcss.config.js",
"""module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
""")
    # globals.css at /styles
    write(project/"styles"/"globals.css",
"""@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html, body, #__next { height: 100%; }
  body { @apply font-sans bg-gray-50; }
}
""")
    # _app.tsx importing ../styles/globals.css
    write(project/"pages"/"_app.tsx",
"""import type { AppProps } from 'next/app';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
""")
    # 404
    write(project/"pages"/"404.tsx",
"""export default function Custom404() {
  return (
    <main className="min-h-screen grid place-items-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">404</h1>
        <p className="text-gray-600">Page not found.</p>
      </div>
    </main>
  );
}
""")
    # index.tsx (sanity)
    if not re.search(r"\bexport\s+default\b", tsx_code):
        raise ValueError("Extracted code is missing `export default`.")
    # tsx_code = patch_extra_braces(tsx_code)
    
    # print('patched extra braces')
    # tsx_code, changed = patch_chart_types_general(tsx_code)
    # if changed: print("patched chart types")
    tsx_code, changed = patch_pie_label_percent_unknown(tsx_code)
    if changed: print("patched pie label percent")
    tsx_code = stabilize_jsx_block(tsx_code)
    

    write(project/"pages"/"index.tsx", tsx_code)

    # Run Prettier on the generated file
    try:
        run(["npx", "prettier", "--write", str(project/"pages"/"index.tsx")], cwd=project)
    except Exception as e:
        print("⚠️  Prettier formatting failed:", e)

    # post-build shaping script
    write(project/"scripts"/"after-export.cjs",
r"""/* shape out/ to match required structure */
const fs = require('fs');
const path = require('path');
const OUT = path.join(process.cwd(), 'out');
if (!fs.existsSync(OUT)) process.exit(0);
const shots = path.join(OUT, 'screenshots');
if (!fs.existsSync(shots)) fs.mkdirSync(shots);
if (!fs.existsSync(path.join(OUT, 'modelOutputPage.html'))) {
  fs.writeFileSync(path.join(OUT, 'modelOutputPage.html'),
    `<!doctype html><html><head><meta charset="utf-8"><title>Model Output</title></head><body><h1>Model Output Page</h1><p>Placeholder.</p></body></html>`);
}
if (!fs.existsSync(path.join(OUT, 'instance_logs.txt'))) {
  fs.writeFileSync(path.join(OUT, 'instance_logs.txt'), 'Logs start...\n');
}
console.log('Post-export shaping complete.');
""")

    # package.json scripts
    pkg_path = project/"package.json"
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except Exception:
        pkg = {"name": project.name, "version": "1.0.0"}
    pkg["scripts"] = {
        "dev": "next dev -p 3000",
        "build": "next build",
        # Next15 static export happens during build; run shaping after build
        "postbuild": "node scripts/after-export.cjs",
        "start": "next start",
        "prod": "npm run build",
        # convenient local preview of /out
        "preview": "npx serve out"
    }
    write(pkg_path, json.dumps(pkg, indent=2))

    # tiny favicon placeholder
    write(project/"public"/"favicon.ico",
          bytes.fromhex("0000010001001010000001002000680400001600000028000000100000002000"
                        "0000010020000000000000040000C40E0000C40E00000000000000000000"),
          binary=True)
    
    if init_code != tsx_code:
        edit_tsx_code = tsx_code
    else:
        edit_tsx_code = None
    return edit_tsx_code

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="Path to input JSON")
    ap.add_argument("--project", default="stock-report", help="Project folder name")
    ap.add_argument("--no-build", action="store_true", help="Only scaffold; skip build")
    ap.add_argument('--multi_step', action='store_true', help='Enable multi-step mode')
    ap.add_argument('--build_for_train', action='store_true', help='Enable multi-step mode')
    ap.add_argument('--build_by_sample', action='store_true', help='Build only single sample')
    ap.add_argument('--build_index', type=int, default=0, help='Build only single sample')
    ap.add_argument('--build_from_index', type=int, default=0, help='Build only single sample')
    args = ap.parse_args()

    payload = read_json(Path(args.json))
   
    if args.multi_step:
        print('Length of steps: ', len(payload))
        for i, step in enumerate(payload):

            print(f"----Build Next.js project for step {i+1}----")
            tsx_code = extract_code(step)

            project = Path.cwd()/args.project/f"step_{i+1}"
            out_dir = project / "out"
            if out_dir.exists():
                print(f"[skip] {out_dir} already exists, skipping build pipeline.")
                continue    
            else:
                try:
                    ensure_clean_dir(project)
                    needs_recharts = ("from 'recharts'" in tsx_code) or ('from "recharts"' in tsx_code)
                    npm_bootstrap(project, needs_recharts)
                    make_files(project, tsx_code)
                    if not args.no_build:
                        run(["npm", "run", "build"], cwd=project)  # writes out/ and runs postbuild
                except Exception as e:
                    print(f"Error building step {i+1}: {e}")
                    continue

        print("\nDone. Static files are in:", project/"out")
        print("Local preview:", "npm run preview")
    else:
        print('Number of sample: ', len(payload))
        if args.build_by_sample:
            build_index = args.build_index
            code = payload[build_index-1]
            
            print(f"\n----Build Next.js project for ID {build_index}----\n")
            tsx_code, pro_idx = extract_code(code)

            project = Path.cwd()/args.project/f"{str(pro_idx+1).zfill(6)}-1"
            
            out_dir = project / "out"
            if out_dir.exists():
                print(f"[skip] {out_dir} already exists, skipping build pipeline.")
            else:
                try:
                    ensure_clean_dir(project)
                    needs_recharts = ("from 'recharts'" in tsx_code) or ('from "recharts"' in tsx_code)
                    npm_bootstrap(project, needs_recharts)
                    make_files(project, tsx_code)
                    if not args.no_build:
                        run(["npm", "run", "build"], cwd=project)  # writes out/ and runs postbuild
                        print("\nDone. Static files are in:", project/"out")
                        print("Local preview:", "npm run preview")
                except Exception as e:
                    print(f"Error building project ID {i+1}: {e}")
        else:
            for i, code in enumerate(payload):
                if i < args.build_from_index:
                    continue
                else:
                    print(f"----Build Next.js project for ID {i+1}----")
                    try:
                        tsx_code, pro_idx, prompt = extract_code(code)
                    except Exception as e:
                        continue

                    project = Path.cwd()/args.project/f"{str(pro_idx+1).zfill(6)}-1"
                    
                    out_dir = project / "out"
                    if out_dir.exists():
                        print(f"[skip] {out_dir} already exists, skipping build pipeline.")
                        continue    
                    else:
                        try:
                            ensure_clean_dir(project)
                            needs_recharts = ("from 'recharts'" in tsx_code) or ('from "recharts"' in tsx_code)
                            npm_bootstrap(project, needs_recharts)
                            edit_tsx_code = make_files(project, tsx_code)
                            if not args.no_build:
                                run(["npm", "run", "build"], cwd=project)  # writes out/ and runs postbuild
                                if os.path.exists(project/"out"):
                                    print("\nBuild Success! Static files are in:", project/"out")
                                    
                                    if args.build_for_train:
                                        formatted_json(tsx_code, edit_tsx_code, Path.cwd()/args.project/"build_train_success_v1.json", pro_idx, prompt)
                                        print("\n Save tsx code to : ", Path.cwd()/args.project/"build_train_success.json\n")
                                        cleanup_folders(project)
                                        print("\n Finish cleaning project folders...keep only out/ folder\n")
                                else:
                                    print("\nBuild Failed!\n")
                                    cleanup_folders(project, full_folder=True)
                                    print("\n Finish cleaning project folders\n")

                        except Exception as e:
                            print(f"Error building project ID {i+1}: {e}")
                            cleanup_folders(project, full_folder=True)
                            continue

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed: {e}", file=sys.stderr)
        sys.exit(e.returncode)
    except Exception as ex:
        print(f"\nError: {ex}", file=sys.stderr)
        sys.exit(1)