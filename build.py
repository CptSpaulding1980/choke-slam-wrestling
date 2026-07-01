#!/usr/bin/env python3
"""
Choke Slam Wrestling — static site pipeline.
Site is pre-built in docs/ from Obsidian vault via Digital Garden export.
Content-root is docs/; GitHub Pages serves directly from there.
"""
from pathlib import Path
import json

REPO = Path(__file__).resolve().parent
DOCS = REPO / "docs"

def main():
    print("=== Choke Slam Wrestling Pipeline ===")

    # Count pages
    html_files = list(DOCS.rglob("*.html"))
    print(f"  HTML pages: {len(html_files)}")

    # Verify key directories
    for d in ["wrestler", "events", "championships", "teams"]:
        p = DOCS / d
        if p.exists():
            entries = [x.name for x in p.iterdir() if x.is_dir()]
            print(f"  {d}/: {len(entries)} entries")

    # Copy Cagematch CSS (if source exists)
    # (handled manually or via other pipeline scripts)

    print("\n=== Pipeline Complete ===")
    print("Site is ready in docs/ — commit and push to deploy.")

if __name__ == '__main__':
    main()
