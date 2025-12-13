# -*- coding: utf-8 -*-
"""
scan_Deian_Package_from_layers_to_sqlite.py

Goal:
  Recover Debian package (name, version, arch) from apt/dpkg logs inside each layer's text.tar.gz.

Layout assumption (flat layers folder):
  root/<layer_hash>/
      ├── text.tar.gz
      └── tree.txt

Speed strategy:
  Use sibling tree.txt as a fast pre-filter; only open tar for hits.

Output (SQLite):
  layers(layer_name, archive_path, mtime)
  packages(pkg_id, name, arch, version)
  layer_packages(layer_name, pkg_id, source, first_seen)

Windows-friendly, stdlib only.
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

# ---------- constants ----------

TAR_NAME = "text.tar.gz"
TREE_NAME = "tree.txt"

# tar internal path prefixes (your tar paths often have outDir1/)
PREFIX_CANDIDATES = ["", "./", "outDir1/", "./outDir1/"]

APT_HISTORY_PREFIX = "var/log/apt/history.log"   # match history.log, history.log.1, history.log.2.gz ...
DPKG_LOG_PREFIX = "var/log/dpkg.log"             # match dpkg.log, dpkg.log.1, dpkg.log.2.gz ...

TREE_NEEDLES = (
    b"var/log/dpkg.log",
    b"var/log/apt/history.log",
    b"var/log/apt/term.log",
    b"/var/log/dpkg.log",
    b"/var/log/apt/history.log",
    b"/var/log/apt/term.log",
)

# apt history.log patterns:
# Install: pkg:amd64 (1.2.3-1), otherpkg (2.0)
# Upgrade: pkg:amd64 (1.2.3-2, 1.2.3-1)
APT_ITEM_RE = re.compile(
    r"""
    (?P<name>[A-Za-z0-9.+-]+)
    (:(?P<arch>[A-Za-z0-9]+))?
    \s*\(
    (?P<ver>[^\s,;()]+)
""",
    re.VERBOSE,
)

# dpkg.log is usually space-separated; we parse by tokens for robustness.


# ---------- sqlite schema ----------

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
"""


def make_pkg_id(name: str, arch: str, ver: str) -> str:
    return hashlib.sha1(f"{name}|{arch}|{ver}".encode("utf-8")).hexdigest()


# ---------- core helpers ----------

def layer_has_logs_via_tree(layer_dir: Path, max_bytes: int = 2 * 1024 * 1024) -> bool:
    """Fast filter: read first 2MB of tree.txt and check needles."""
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
    """
    Find tar members that start with any (prefix_candidate + rel_prefix),
    including rotated/compressed variants.

    Example:
      outDir1/var/log/dpkg.log
      outDir1/var/log/dpkg.log.1
      outDir1/var/log/dpkg.log.2.gz
      outDir1/var/log/dpkg.log.3.xz
      outDir1/var/log/dpkg.log.4.zst   (we can list it; may not decode)
    """
    wanted_prefixes = [(p + rel_prefix) for p in PREFIX_CANDIDATES]
    hits: List[str] = []
    for m in tf.getmembers():
        n = normalize_member(m.name)
        for wp in wanted_prefixes:
            if n.startswith(wp):
                hits.append(m.name)  # keep original for getmember/extractfile
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


def decode_member_text(member_name: str, data: bytes) -> Tuple[str, str]:
    """
    Return (text, decode_mode)
      decode_mode in {"plain","gz","xz","zst-unsupported","unknown"}
    """
    mode = "plain"
    if member_name.endswith(".gz"):
        mode = "gz"
        try:
            data = gzip.decompress(data)
        except Exception:
            mode = "gz-decompress-failed"
    elif member_name.endswith(".xz"):
        mode = "xz"
        try:
            data = lzma.decompress(data)
        except Exception:
            mode = "xz-decompress-failed"
    elif member_name.endswith(".zst"):
        # stdlib does NOT support zstd; keep as unsupported marker
        return ("", "zst-unsupported")

    try:
        return (data.decode("utf-8", errors="replace"), mode)
    except Exception:
        return ("", "decode-failed")


# ---------- parsers ----------

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


def head_lines(text: str, k: int) -> str:
    return "\n".join(text.splitlines()[:k])


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Flat folder containing many layer dirs")
    ap.add_argument("--db", default="layers_pkgs.sqlite", help="SQLite output")
    ap.add_argument("--limit", type=int, default=0, help="Scan first N layers (after tar existence check)")
    ap.add_argument("--dry-run", action="store_true", help="Do NOT write SQLite")
    ap.add_argument("--rebuild", action="store_true", help="Drop tables and recreate")

    # Debug: print tar member hits + head lines for first N tree-hit layers
    ap.add_argument("--debug-hit", type=int, default=0, help="Debug first N tree-hit layers")
    ap.add_argument("--head-lines", type=int, default=40, help="Head lines per log in debug-hit")

    args = ap.parse_args()
    root = Path(args.root)

    # sqlite init
    conn = None
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

    discovered = 0
    scanned = 0
    tree_hit = 0
    tar_opened = 0
    parsed_events = 0

    dbg_left = args.debug_hit

    t0 = time.perf_counter()

    # FAST enumeration: only one level, no os.walk/rglob
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

        if not layer_has_logs_via_tree(layer_dir):
            continue
        tree_hit += 1

        try:
            with tarfile.open(tar_path, "r:*") as tf:
                tar_opened += 1

                apt_members = find_members_with_prefix(tf, APT_HISTORY_PREFIX)
                dpkg_members = find_members_with_prefix(tf, DPKG_LOG_PREFIX)

                # debug print even if parsed 0
                if dbg_left > 0:
                    dbg_left -= 1
                    print("\n========== DEBUG HIT LAYER ==========")
                    print(f"layer: {layer_dir.name}")
                    print(f"tar  : {tar_path}")
                    print(f"apt_members({len(apt_members)}):")
                    for m in apt_members[:80]:
                        print(f"  - {m}")
                    print(f"dpkg_members({len(dpkg_members)}):")
                    for m in dpkg_members[:80]:
                        print(f"  - {m}")

                    # print head of first few logs for quick truth
                    for m in (apt_members[:2] + dpkg_members[:2]):
                        data = read_member_bytes(tf, m) or b""
                        txt, mode = decode_member_text(m, data)
                        print(f"\n--- {m}  [mode={mode}] ---")
                        if not txt:
                            print("(empty/unreadable)")
                        else:
                            print(head_lines(txt, args.head_lines))
                    print("=====================================")

                rows: List[Tuple[str, str, str, str]] = []

                # parse apt history (including rotated/compressed variants)
                for mem in apt_members:
                    data = read_member_bytes(tf, mem)
                    if not data:
                        continue
                    txt, mode = decode_member_text(mem, data)
                    if not txt:
                        continue
                    rows.extend(parse_apt_history(txt))

                # parse dpkg log (including rotated/compressed variants)
                for mem in dpkg_members:
                    data = read_member_bytes(tf, mem)
                    if not data:
                        continue
                    txt, mode = decode_member_text(mem, data)
                    if not txt:
                        continue
                    rows.extend(parse_dpkg_log(txt))

        except tarfile.TarError:
            continue

        parsed_events += len(rows)

        # write sqlite
        if (not args.dry_run) and rows:
            ts = int(time.time())
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO layers VALUES (?, ?, ?)",
                (layer_dir.name, str(tar_path), int(tar_path.stat().st_mtime)),
            )
            for n, v, a, s in rows:
                pid = make_pkg_id(n, a, v)
                cur.execute("INSERT OR IGNORE INTO packages VALUES (?, ?, ?, ?)", (pid, n, a, v))
                cur.execute("INSERT OR IGNORE INTO layer_packages VALUES (?, ?, ?, ?)", (layer_dir.name, pid, s, ts))
            conn.commit()

    if conn:
        conn.close()

    elapsed = time.perf_counter() - t0
    print(
        f"[DONE] discovered={discovered} scanned={scanned} tree_hit={tree_hit} "
        f"tar_opened={tar_opened} parsed_events={parsed_events} elapsed={elapsed:.2f}s"
    )

    if parsed_events == 0:
        print(
            "[HINT] parsed_events=0 means one of the following is true:\n"
            "  1) tar does NOT actually contain dpkg/apt logs (even if tree.txt suggests paths)\n"
            "  2) logs exist but have no install/upgrade records\n"
            "  3) logs are compressed as .zst (unsupported by stdlib) or other format\n"
            "Try: --debug-hit 5 --head-lines 60 to see real member names and log headers."
        )


if __name__ == "__main__":
    main()
