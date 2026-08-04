"""Generate the 'after' eval harness straight from the live server, so the probe agents see
exactly the text a real MCP client is handed."""
import json
import os
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(OUT, "..", "..", "api"))
import _core  # noqa: E402

lines = [
    "# explore_unizg MCP server — instructions the client sees (TUNED / v2)",
    "",
    "## Server instructions",
    "",
    _core.INSTRUCTIONS,
    "## Tools available",
    "",
]
for t in _core.TOOLS:
    props = ", ".join(sorted(t["inputSchema"].get("properties", {}))) or "(none)"
    lines.append(f"- `{t['name']}` — {t['description']}")
    lines.append(f"  Args: {props}.")
    if t["name"] == "unizg_mobility_rules":
        lines.append("  NOTE FOR THIS SIMULATION: this tool makes no network call. To 'call' it, "
                     "Read the file mobility_rules_payload.md in this same directory — that is "
                     "verbatim what the tool returns.")
lines.append("")

with open(os.path.join(OUT, "server_after.md"), "w") as fh:
    fh.write("\n".join(lines))

payload = _core.call_tool("unizg_mobility_rules", {})
with open(os.path.join(OUT, "mobility_rules_payload.md"), "w") as fh:
    fh.write("# Verbatim result of calling unizg_mobility_rules\n\n```json\n")
    fh.write(json.dumps(payload, ensure_ascii=False, indent=2))
    fh.write("\n```\n")

print("wrote server_after.md and mobility_rules_payload.md")
print("instructions chars:", len(_core.INSTRUCTIONS), "| tools:", len(_core.TOOLS))
