#!/usr/bin/env python3
"""
build_index.py - builds an index from memory front-matter and suggests candidate
memories based on the current branch name and the files changed on it.

INDEX.md is NOT committed; it is regenerated on every session. That keeps a whole
team from fighting merge conflicts over a single shared file.

Usage:
  build_index.py --root ~/task-memory-store
  build_index.py --root ~/task-memory-store -o INDEX.md
  build_index.py --root ~/task-memory-store --suggest \
      --slug fix/PROJ-478-retry-duplicate \
      --files "$(git diff --name-only origin/main...HEAD)" --limit 8

PyYAML is used when available; otherwise a small fallback parser extracts the
fields the index needs, so the plugin has no hard dependency.
"""

import argparse
import os
import re
import sys

try:
    import yaml  # type: ignore
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
TOKEN_RE = re.compile(r"[a-z0-9]+")

# Tokens too common in source paths to carry any signal.
STOP = {
    "src", "main", "java", "com", "net", "org", "test", "tests", "index", "app",
    "lib", "libs", "pkg", "internal", "feature", "feat", "fix", "bugfix", "hotfix",
    "chore", "resources", "impl", "service", "services", "controller", "handler",
    "ts", "tsx", "js", "jsx", "py", "go", "rb", "cs", "kt", "yaml", "yml", "json",
    "xml", "md", "sql", "toml", "ini", "the", "and", "for", "with", "from",
    "dto", "dtos", "entity", "entities", "model", "models", "util", "utils",
    "common", "core", "base", "new", "old", "tmp", "temp",
}


def load_config(root):
    """Read optional KEY=VALUE settings from <root>/config.env.

    Parsed, never executed: the memory repo is team-writable and sourcing it
    would make any commit there run code on every developer's machine.
    """
    cfg = {}
    path = os.path.join(root, "config.env")
    if not os.path.isfile(path):
        return cfg
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip("'\"")
    except OSError:
        pass
    return cfg


def parse_front_matter(text):
    m = FM_RE.match(text)
    if not m:
        return {}
    raw = m.group(1)
    if HAVE_YAML:
        try:
            data = yaml.safe_load(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            pass
    return _fallback_parse(raw)


def _fallback_parse(raw):
    """Without PyYAML, extract just the fields the index needs."""
    out = {}
    for key in ("id", "title", "domain", "confidence", "status"):
        m = re.search(rf"^{key}:\s*(.+)$", raw, re.M)
        if m:
            out[key] = m.group(1).strip().strip("'\"")
    for key in ("domains", "keywords"):
        m = re.search(rf"^{key}:\s*\[(.*?)\]", raw, re.M | re.S)
        if m:
            out[key] = [x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()]
    paths = re.findall(r"^\s*(?:-\s*)?path:\s*(.+)$", raw, re.M)
    if paths:
        out["anchors"] = [{"path": p.strip().strip("'\"")} for p in paths]
    repos = re.findall(r"^\s*(?:-\s*)?repo:\s*(.+)$", raw, re.M)
    if repos:
        out.setdefault("anchors", [])
        for i, r in enumerate(repos):
            if i < len(out["anchors"]):
                out["anchors"][i]["repo"] = r.strip().strip("'\"")
    return out


def tokens(*parts, stop=STOP):
    bag = set()
    for p in parts:
        if not p:
            continue
        if isinstance(p, (list, tuple)):
            p = " ".join(str(x) for x in p)
        norm = str(p).lower().replace("/", " ").replace(".", " ").replace("-", " ")
        for t in TOKEN_RE.findall(norm):
            if len(t) > 2 and t not in stop:
                bag.add(t)
    return bag


def load_memories(root):
    """Read tasks/*/README.md and domains/*.md."""
    items = []
    tasks_dir = os.path.join(root, "tasks")
    if os.path.isdir(tasks_dir):
        for name in sorted(os.listdir(tasks_dir)):
            path = os.path.join(tasks_dir, name, "README.md")
            if os.path.isfile(path):
                items.append(_load(path, "task", root))
    dom_dir = os.path.join(root, "domains")
    if os.path.isdir(dom_dir):
        for name in sorted(os.listdir(dom_dir)):
            if name.endswith(".md") and not name.startswith("_"):
                items.append(_load(os.path.join(dom_dir, name), "domain", root))
    return [i for i in items if i]


def _load(path, kind, root):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    fm = parse_front_matter(text)
    anchors = fm.get("anchors") or []
    anchor_paths = [a.get("path", "") for a in anchors if isinstance(a, dict)]
    anchor_repos = [a.get("repo", "") for a in anchors if isinstance(a, dict)]
    return {
        "kind": kind,
        "rel": os.path.relpath(path, root),
        "id": str(fm.get("id") or fm.get("domain")
                  or os.path.basename(os.path.dirname(path))),
        "title": str(fm.get("title") or ""),
        "domains": fm.get("domains") or ([fm["domain"]] if fm.get("domain") else []),
        "keywords": fm.get("keywords") or [],
        "confidence": str(fm.get("confidence") or "-"),
        "status": str(fm.get("status") or "-"),
        "anchor_paths": anchor_paths,
        "anchor_repos": [r for r in anchor_repos if r],
    }


def render_index(items):
    lines = ["# INDEX (generated file - do not edit by hand)", ""]
    lines.append("| ID | Kind | Title | Domains | Confidence | Keywords |")
    lines.append("|---|---|---|---|---|---|")
    for i in items:
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            i["id"], i["kind"], i["title"][:60],
            ", ".join(i["domains"]), i["confidence"],
            ", ".join(i["keywords"])[:80]))
    return "\n".join(lines) + "\n"


def suggest(items, slug, files, limit, stop=STOP):
    file_list = [f.strip() for f in (files or "").split("\n") if f.strip()]
    query = tokens(slug, stop=stop) | tokens(file_list, stop=stop)
    scored = []
    for i in items:
        score = 0
        # Strongest signal: an anchor path matching a file that actually changed.
        for ap in i["anchor_paths"]:
            for f in file_list:
                if ap and (ap == f or os.path.basename(ap) == os.path.basename(f)):
                    score += 10
                elif ap and os.path.dirname(ap) and os.path.dirname(ap) in f:
                    score += 4
        overlap = query & tokens(i["keywords"], i["title"], i["domains"],
                                 i["anchor_paths"], i["anchor_repos"], stop=stop)
        score += 2 * len(overlap)
        if score:
            scored.append([score, sorted(overlap)[:6], i])

    # A domain memory describes how things work TODAY; a task memory is historical.
    # When a task scores high, pull its domain up too - otherwise the reader sees
    # the outdated record before the current one.
    hot = {d for s, _, i in scored if i["kind"] == "task" and s >= 6 for d in i["domains"]}
    for row in scored:
        if row[2]["kind"] == "domain" and row[2]["id"] in hot:
            row[0] += 12
    for d in hot:
        if not any(r[2]["kind"] == "domain" and r[2]["id"] == d for r in scored):
            match = next((x for x in items
                          if x["kind"] == "domain" and x["id"] == d), None)
            if match:
                scored.append([12, [], match])

    scored.sort(key=lambda x: -x[0])
    if not scored:
        return "(no matching records)"
    out = []
    for score, ov, i in scored[:limit]:
        out.append("  - {} [{}] {} -> {}  (score {}{})".format(
            i["id"], i["kind"], i["title"][:50], i["rel"], score,
            "; matched: " + ", ".join(ov) if ov else ""))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get(
        "TASK_MEMORY_DIR", os.path.expanduser("~/task-memory-store")))
    ap.add_argument("-o", "--output")
    ap.add_argument("--suggest", action="store_true")
    ap.add_argument("--slug", default="")
    ap.add_argument("--files", default="")
    ap.add_argument("--limit", type=int, default=8)
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"[build_index] directory not found: {args.root}", file=sys.stderr)
        return 1

    cfg = load_config(args.root)
    stop = STOP | {w.lower() for w in cfg.get("EXTRA_STOP_WORDS", "").split() if w}

    items = load_memories(args.root)
    text = (suggest(items, args.slug, args.files, args.limit, stop=stop)
            if args.suggest else render_index(items))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text if text.endswith("\n") else text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
