#!/usr/bin/env python3
"""
Takes a review JSON (matching the schema below) via stdin or --file,
and writes output/<name>.md + output/<name>.json.
Keeps the same schema as the original Pydantic model so the .md
formatting logic didn't need to change at all:

{
  "summary": str,
  "tech": [str],
  "pros": [str],
  "cons": [str],
  "suggestions": [str]
}
"""
import argparse
import json
import sys
from pathlib import Path


def save_to_markdown(data: dict, filename: str = "review"):
    folder_path = Path("output")
    folder_path.mkdir(parents=True, exist_ok=True)

    md_path = folder_path / f"{filename}.md"
    json_path = folder_path / f"{filename}.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    def format_bullets(items):
        if not items or not isinstance(items, list):
            return ""
        return "\n".join(f"- {item}" for item in items)

    md_content = f"""# Code Review Report

### Summary

{data.get('summary', '')}

---
### Technologies

{format_bullets(data.get('tech', []))}

### Pros

{format_bullets(data.get('pros', []))}

### Cons / Issues

{format_bullets(data.get('cons', []))}

### Suggestions

{format_bullets(data.get('suggestions', []))}
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved: {md_path} and {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Save a code review JSON as markdown")
    parser.add_argument("--file", help="Path to JSON file. If omitted, reads from stdin.")
    parser.add_argument("--name", default="review")
    args = parser.parse_args()

    raw = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    data = json.loads(raw)
    save_to_markdown(data, args.name)


if __name__ == "__main__":
    main()