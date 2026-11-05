"""Refresh the README model table from Tokscale's public 30-day profile JSON."""

from datetime import date
import html
import json
import math
from pathlib import Path
import re
import sys


START = "<!-- TOKSCALE_MODELS_START -->"
END = "<!-- TOKSCALE_MODELS_END -->"


def render_models(data):
    if data["user"]["username"].casefold() != "issacl04" or data["period"] != "month":
        raise ValueError("Expected IssacL04's rolling 30-day profile")
    start = date.fromisoformat(data["dateRange"]["start"])
    end = date.fromisoformat(data["dateRange"]["end"])
    if (end - start).days != 29:
        raise ValueError("Expected a 30-day window, including both endpoints")
    models = data["modelUsage"]
    if not isinstance(models, list):
        raise ValueError("Missing model usage list")
    for row in models:
        tokens, cost = row["tokens"], row["cost"]
        if not isinstance(row["model"], str) or not row["model"].strip():
            raise ValueError("Invalid model name")
        if type(tokens) is not int or tokens < 0:
            raise ValueError("Invalid model token count")
        if type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
            raise ValueError("Invalid model cost")

    lines = [
        "### Model usage",
        "",
        f"{start} to {end} · Updated daily.",
        "",
        "| Model | Tokens | Estimated cost |",
        "| :--- | ---: | ---: |",
    ]
    for row in sorted(models, key=lambda row: row["tokens"], reverse=True):
        name = html.escape(row["model"], quote=False)
        name = re.sub(r"([\\`*_{}\[\]()|])", r"\\\1", name)
        name = name.replace("\n", " ").replace("\r", " ")
        lines.append(f"| {name} | {row['tokens']:,} | ${row['cost']:,.2f} |")
    if not models:
        lines.append("| No model usage in this window | 0 | $0.00 |")
    lines += ["", "Costs are Tokscale estimates. Unpriced usage can appear as $0."]
    return "\n".join(lines)


def replace_models(readme, table):
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError("Expected exactly one model table marker pair")
    before, _, rest = readme.partition(START)
    if END not in rest:
        raise ValueError("Model table markers are out of order")
    _, _, after = rest.partition(END)
    return before + START + "\n" + table + "\n" + END + after


if __name__ == "__main__":
    table = render_models(json.load(sys.stdin))
    readme = Path(__file__).resolve().parents[1] / "README.md"
    updated = replace_models(readme.read_text(encoding="utf-8"), table)
    readme.write_text(updated, encoding="utf-8")
