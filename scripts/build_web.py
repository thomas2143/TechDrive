"""
Inline data.json into the page so the result is one portable file.

Fetching data.json would work on a web server and fail from the filesystem,
which is where this gets opened most often. Inlining costs 28 KB and removes
the failure mode entirely.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "web"
template = (ROOT / "template.html").read_text()
data = (ROOT / "data.json").read_text()

marker = "/*__DATA__*/null"
if marker not in template:
    raise SystemExit("data placeholder missing from template.html")

out = ROOT / "index.html"
out.write_text(template.replace(marker, data))
print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
