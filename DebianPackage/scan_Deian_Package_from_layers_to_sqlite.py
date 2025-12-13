# -*- coding: utf-8 -*-
"""
scan_Deian_Package_from_layers_to_sqlite.py

Scan flat layer folder:
  root/<layer_hash>/{text.tar.gz, tree.txt}

Use tree.txt filter to reduce tar opens, then parse Debian package events from:
  - var/log/dpkg.log*
  - var/log/apt/history.log*
(rotated + .gz/.xz supported)

Write into SQLite with layer_name kept (for later manifest mapping).

Windows-friendly. Stdlib only.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import lzma
import os
import re
import sqlite3
import tarfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------- constants ----------------

TAR_NAME = "text.tar.gz"
TREE_NAME = "tree.txt"

PREFIX_CANDIDATES = ["", "./", "outDir1/", "./outDir1/"]

APT_HISTORY_PREFIX = "var/log/apt/history.log"
DPKG_LOG_PREFIX = "var/log/dpkg.log"

TREE_NEEDLES = (
    b"var/log/dpkg.log",
    b"var/log/apt/history.log",
    b"var/log/apt/term.log",
    b"/var/log/dpkg.log",
    b"/var/log/apt/history.log",
    b"/var/log/apt/term.log",
)

APT_ITEM_RE = re.compile(
    r"""
    (?P<name>[A-Za-z0-9.+-]+)
    (:(?P<arch>[A-Za-z0-9]+))?
    \s*\(
    (?P<ver>[^\s,;()]+)
""",
    re.VERBOSE,
)

DDL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS layers (
  layer_name TEXT PRIMARY KEY,
  archive_path TEXT,
  mtime INTEGER
);

CREATE TABLE IF NOT EXISTS packages (
  pkg_id TEXT PRIMARY KEY,
  name TEXT,
  arch TEXT,
  version TEXT
);

CREATE TABLE IF NOT EXISTS layer_packages (
  layer_name TEXT,
  pkg_id TEXT,
  source TEXT,
  first_seen INTEGER,
  PRIMARY KEY(layer_name, pkg_id, source)
);

CREATE INDEX IF NOT EXISTS idx_layer_packages_layer ON layer_packages(layer_name);
CREATE INDEX IF NOT EXISTS idx_layer_packages_pkg   ON layer_packages(pkg_id);
"""

# ---------------- helpers ----------------

def make_pkg_id(name: str, arch: str, ver: str) -> str:
    return hashlib.sha1(f"{name}|{arch}|{ver}".encode("utf-8")).hexdigest()

def layer_has_logs_via_tree(layer_dir: Path, max_bytes: int = 2 * 1024 * 1024) -> bool:
    tp = layer_dir / TREE_NAME
    if not tp.exists():
        return False
    try:
        with tp.open("rb") as f:
            data = f.read(max_bytes)
    except OSError:
        return False
    return any(n in data for n in TREE_NEEDLES)

def normalize_member(name: str) -> str:
    return name[2:] if name.startswith("./") else name

def find_members_with_prefix(tf: tarfile.TarFile, rel_prefix: str) -> List[str]:
    wanted = [(p + rel_prefix) for p in PREFIX_CANDIDATES]
    hits: List[str] = []
    for m in tf.getmembers():
        n = normalize_member(m.name)
        for wp in wanted:
            if n.startswith(wp):
                hits.append(m.name)
                break
    return hits

def read_member_bytes(tf: tarfile.TarFile, member_name: str) -> Optional[bytes]:
    try:
        m = tf.getmember(member_name)
    except KeyError:
        return None
    f = tf.extractfile(m)
    if f is None:
        return None
    return f.read()

def decode_member_text(member_name: str, data: bytes) -> str:
    if member_name.endswith(".gz"):
        try:
            data = gzip.decompress(data)
        except Exception:
            return ""
    elif member_name.endswith(".xz"):
        try:
            data = lzma.decompress(data)
        except Exception:
            return ""
    elif member_name.endswith(".zst"):
        # stdlib does not support zstd. We just skip.
        return ""

    return data.decode("utf-8", errors="replace")

# ---------------- parsers ----------------

def parse_apt_history(text: str) -> List[Tuple[str, str, str, str]]:
    rows: List[Tuple[str, str, str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("Install:", "Upgrade:", "Remove:", "Purge:")):
            action, _, rest = line.partition(":")
            if action in ("Install", "Upgrade"):
                src = f"apt-{action.lower()}"
                for m in APT_ITEM_RE.finditer(rest):
                    rows.append((m.group("name"), m.group("ver"), m.group("arch") or "", src))
    return rows

def parse_dpkg_log(text: str) -> List[Tuple[str, str, str, str]]:
    rows: List[Tuple[str, str, str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        action = parts[2]
        if action not in ("install", "upgrade"):
            continue

        pkg_arch = parts[3]
        if ":" in pkg_arch:
            name, arch = pkg_arch.split(":", 1)
        else:
            name, arch = pkg_arch, ""

        new_ver = parts[-1]
        if new_ver in ("<none>", "half-configured", "installed"):
            continue
        rows.append((name, new_ver, arch, f"dpkg-{action}"))
    return rows

# ---------------- progress ----------------

def fmt_rate(x: float) -> str:
    if x <= 0:
        return "0"
    return f"{x:.2f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Flat folder that contains layer dirs")
    ap.add_argument("--db", required=True, help="SQLite file path")
    ap.add_argument("--limit", type=int, default=0, help="Scan at most N layers (0=all)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write to SQLite")
    ap.add_argument("--rebuild", action="store_true", help="Drop and recreate tables")

    ap.add_argument("--progress-every", type=int, default=2000,
                    help="Print progress every N scanned layer dirs")
    ap.add_argument("--commit-every", type=int, default=200,
                    help="Commit every N tar-opened hit layers (batch commit)")

    args = ap.parse_args()

    root = Path(args.root)

    conn = None
    cur = None
    if not args.dry_run:
        conn = sqlite3.connect(args.db)
        cur = conn.cursor()
        if args.rebuild:
            cur.executescript(
                "DROP TABLE IF EXISTS layer_packages; DROP TABLE IF EXISTS packages; DROP TABLE IF EXISTS layers;"
            )
        cur.executescript(DDL)
        conn.commit()
    else:
        print("[INFO] DRY-RUN mode: will NOT write anything to SQLite")

    discovered = 0          # layers with tar present
    scanned = 0             # iterated layer dirs with tar present
    tree_hit = 0            # passed tree filter
    tar_opened = 0          # tar opened
    parsed_events = 0       # total parsed rows
    written_rows = 0        # rows written into layer_packages (approx)

    hit_since_commit = 0

    t_start = time.perf_counter()
    t_last = t_start
    scanned_last = 0

    for entry in os.scandir(root):
        if not entry.is_dir():
            continue

        layer_dir = Path(entry.path)
        tar_path = layer_dir / TAR_NAME
        if not tar_path.exists():
            continue

        discovered += 1
        scanned += 1

        if args.limit and discovered > args.limit:
            break

        if args.progress_every and (scanned % args.progress_every == 0):
            t_now = time.perf_counter()
            dt = t_now - t_last
            d_layers = scanned - scanned_last
            rate = (d_layers / dt) if dt > 0 else 0.0

            elapsed = t_now - t_start
            print(
                f"[PROGRESS] scanned={scanned} tree_hit={tree_hit} tar_opened={tar_opened} "
                f"parsed_events={parsed_events} written={written_rows} "
                f"elapsed={elapsed:.1f}s rate={fmt_rate(rate)} layers/s"
            )
            t_last = t_now
            scanned_last = scanned

        if not layer_has_logs_via_tree(layer_dir):
            continue

        tree_hit += 1

        rows: List[Tuple[str, str, str, str]] = []
        try:
            with tarfile.open(tar_path, "r:*") as tf:
                tar_opened += 1

                apt_members = find_members_with_prefix(tf, APT_HISTORY_PREFIX)
                dpkg_members = find_members_with_prefix(tf, DPKG_LOG_PREFIX)

                for mem in apt_members:
                    data = read_member_bytes(tf, mem)
                    if not data:
                        continue
                    txt = decode_member_text(mem, data)
                    if not txt:
                        continue
                    rows.extend(parse_apt_history(txt))

                for mem in dpkg_members:
                    data = read_member_bytes(tf, mem)
                    if not data:
                        continue
                    txt = decode_member_text(mem, data)
                    if not txt:
                        continue
                    rows.extend(parse_dpkg_log(txt))

        except tarfile.TarError:
            continue

        if not rows:
            continue

        parsed_events += len(rows)

        if args.dry_run:
            continue

        # ---- SQLite write (batched commit) ----
        ts = int(time.time())
        assert conn is not None and cur is not None

        cur.execute(
            "INSERT OR IGNORE INTO layers VALUES (?, ?, ?)",
            (layer_dir.name, str(tar_path), int(tar_path.stat().st_mtime)),
        )

        for n, v, a, s in rows:
            pid = make_pkg_id(n, a, v)
            cur.execute("INSERT OR IGNORE INTO packages VALUES (?, ?, ?, ?)", (pid, n, a, v))
            cur.execute("INSERT OR IGNORE INTO layer_packages VALUES (?, ?, ?, ?)", (layer_dir.name, pid, s, ts))
            written_rows += 1

        hit_since_commit += 1
        if hit_since_commit >= args.commit_every:
            conn.commit()
            hit_since_commit = 0

    if conn:
        conn.commit()
        conn.close()

    elapsed = time.perf_counter() - t_start
    print(
        f"[DONE] discovered={discovered} scanned={scanned} tree_hit={tree_hit} "
        f"tar_opened={tar_opened} parsed_events={parsed_events} written={written_rows} "
        f"elapsed={elapsed:.2f}s"
    )

if __name__ == "__main__":
    main()
