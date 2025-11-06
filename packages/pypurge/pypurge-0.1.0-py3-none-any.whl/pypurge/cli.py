#!/usr/bin/env python3
"""
clean.py - 10/10 Production-grade Python cleanup utility

This is an improved, hardened, and user-friendly version of the "6.0.0"
script you supplied. Focus areas:
 - Fixed datetime/logging bugs and syntax issues
 - Robust stale-lock detection + safe release on signals
 - Atomic backup with sha256 and safe tmp cleanup
 - Console color support that can be disabled
 - Rich, grouped preview (counts + sizes) for excellent user visibility
 - Better arranged grouping (sorted by group size and item count)
 - Clear exit codes and automation-friendly flags

Requirements: Python 3.10+
No external dependencies (optional: psutil for Windows PID checks)
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import logging
import os
import re
import shutil
import signal
import stat
import sys
import tempfile
import time
import zipfile
from collections import defaultdict
from datetime import datetime as _dt
from pathlib import Path
from typing import List, Optional, Tuple

__version__ = "6.0.0"

# Exit codes
EXIT_OK = 0
EXIT_CANCELLED = 2
EXIT_PARTIAL_FAILURE = 3
EXIT_DANGEROUS_ROOT = 4
EXIT_LOCK_ERROR = 5
EXIT_UNKNOWN_ERROR = 6

# Defaults
DEFAULT_LOCK_TTL = 24 * 3600  # 24 hours stale lock threshold
DEFAULT_LARGE_THRESHOLD = 100 * 1024 * 1024  # 100MB

# ----- Logging helpers -----


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": _dt.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(
    log_format: str,
    log_file: Optional[Path],
    level: int = logging.INFO,
    rotate: bool = True,
) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    # clear existing handlers
    while root.handlers:
        root.handlers.pop()

    if log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    if log_file:
        try:
            if rotate:
                from logging.handlers import RotatingFileHandler

                fh = RotatingFileHandler(
                    str(log_file),
                    maxBytes=5 * 1024 * 1024,
                    backupCount=5,
                    encoding="utf-8",
                )
            else:
                fh = logging.FileHandler(str(log_file), encoding="utf-8")
            fh.setFormatter(
                JsonFormatter()
                if log_format == "json"
                else logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
            )
            root.addHandler(fh)
        except Exception:
            # best-effort: add a simple file handler
            try:
                fh = logging.FileHandler(str(log_file), encoding="utf-8")
                fh.setFormatter(
                    JsonFormatter()
                    if log_format == "json"
                    else logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
                )
                root.addHandler(fh)
            except Exception:
                logging.getLogger(__name__).warning(
                    "Failed to open log file: %s", log_file
                )


logger = logging.getLogger(__name__)

# ----- Utilities -----


def format_bytes(bytes_size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_size)
    unit = 0
    while size > 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1
    return f"{size:.2f}{units[unit]}" if unit > 0 else f"{int(size)}{units[unit]}"


def get_size(path: Path) -> int:
    total = 0
    try:
        if path.is_symlink():
            return int(path.lstat().st_size or 0)
        if path.is_file():
            return int(path.stat().st_size or 0)
        for sub in path.rglob("*"):
            try:
                if sub.is_file():
                    total += int(sub.stat().st_size or 0)
                elif sub.is_symlink():
                    total += int(sub.lstat().st_size or 0)
            except Exception:
                continue
    except Exception:
        return 0
    return total


def is_old_enough(path: Path, older_than_sec: float, age_type: str) -> bool:
    try:
        st = path.stat()
        if age_type == "mtime":
            t = st.st_mtime
        elif age_type == "atime":
            t = st.st_atime
        elif age_type == "ctime":
            t = st.st_ctime
        else:
            t = st.st_mtime
        return t < time.time() - older_than_sec
    except Exception:
        return False


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ----- Lock helpers (with stale detection) -----


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if hasattr(os, "kill"):
            os.kill(pid, 0)
            return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        try:
            if sys.platform.startswith("win"):
                import psutil  # type: ignore

                return psutil.pid_exists(pid)
        except Exception:
            return True
    return True


def acquire_lock(
    lock_path: Path, stale_seconds: int = DEFAULT_LOCK_TTL
) -> Optional[int]:
    """Create exclusive lockfile. If existing lock appears stale (PID gone and older than TTL), reap it."""
    try:
        if lock_path.exists():
            try:
                txt = lock_path.read_text()
                pid = None
                started = None
                for line in txt.splitlines():
                    if line.startswith("pid:"):
                        try:
                            pid = int(line.split(":", 1)[1])
                        except Exception:
                            pid = None
                    if line.startswith("started:"):
                        try:
                            started = float(line.split(":", 1)[1])
                        except Exception:
                            started = None
                if pid and _pid_alive(pid):
                    return None
                if started is not None and (time.time() - started) < stale_seconds:
                    return None
                try:
                    lock_path.unlink()
                    logger.warning("Removed stale lockfile %s", lock_path)
                except Exception:
                    logger.debug("Could not remove stale lockfile %s", lock_path)
            except Exception:
                return None
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"pid:{os.getpid()}\nstarted:{time.time()}\n".encode("utf-8"))
        return fd
    except FileExistsError:
        return None
    except Exception as e:
        logger.debug("acquire_lock exception: %s", e)
        return None


def release_lock(fd: Optional[int], lock_path: Path) -> None:
    try:
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            pass
    except Exception:
        pass


# ----- Atomic backup -----


def backup_targets_atomic(
    targets: List[Path], backup_root: Path, root: Path, name: Optional[str] = None
) -> Optional[Tuple[Path, str]]:
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.utcnow().strftime("%Y%m%d_%H%M%SZ")
    archive_name = (
        f"{name}_{timestamp}.zip" if name else f"cleanpy_backup_{timestamp}.zip"
    )
    final_path = backup_root / archive_name
    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix=f".{archive_name}.", dir=str(backup_root)
    )
    os.close(tmp_fd)
    tmp_path = Path(tmp_path)
    symlink_manifest = []
    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in targets:
                try:
                    rel = p.relative_to(root)
                except Exception:
                    rel = Path(p.name)
                if p.is_symlink():
                    try:
                        target = os.readlink(p)
                    except Exception:
                        target = None
                    symlink_manifest.append({"path": str(rel), "target": target})
                    continue
                if p.is_file():
                    try:
                        zf.write(p, arcname=rel)
                    except Exception:
                        logger.warning("Failed to write %s to archive", p)
                elif p.is_dir():
                    for sub in p.rglob("*"):
                        if sub.is_file():
                            try:
                                arc = sub.relative_to(root)
                            except Exception:
                                arc = Path(sub.name)
                            try:
                                zf.write(sub, arcname=arc)
                            except Exception:
                                logger.debug("Skipping file in backup: %s", sub)
            if symlink_manifest:
                zf.writestr(
                    "cleanpy_symlink_manifest.json",
                    json.dumps({"symlinks": symlink_manifest}, indent=2),
                )
        sha = sha256_of_file(tmp_path)
        os.replace(tmp_path, final_path)
        shafile = final_path.with_suffix(final_path.suffix + ".sha256")
        tmp_sha = str(shafile) + ".tmp"
        with open(tmp_sha, "w", encoding="utf-8") as f:
            f.write(sha + "  " + final_path.name + "\n")
        os.replace(tmp_sha, shafile)
        return final_path, sha
    except Exception as e:
        logger.error("Backup failed: %s", e)
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return None


# ----- Safety helpers -----
DANGEROUS_ROOTS = {
    Path("/"),
    Path.home(),
    Path("/usr"),
    Path("/bin"),
    Path("/sbin"),
    Path("/etc"),
}


def is_dangerous_root(p: Path) -> bool:
    try:
        p_res = p.resolve()
    except Exception:
        return True
    for d in DANGEROUS_ROOTS:
        try:
            if str(p_res) == str(d.resolve()):
                return True
        except Exception:
            continue
    if len(p_res.parts) <= 2:
        return True
    return False


# ----- Pretty interactive printing -----
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    GRAY = "\033[0;90m"
    NC = "\033[0m"


class NullColors:
    RED = GREEN = YELLOW = BLUE = CYAN = GRAY = NC = ""


def get_colors(use_color: bool):
    return Colors() if use_color else NullColors()


def print_info(msg: str, colors):
    print(f"{colors.BLUE}ℹ️  {msg}{colors.NC}")


def print_success(msg: str, colors):
    print(f"{colors.GREEN}✅ {msg}{colors.NC}")


def print_warning(msg: str, colors):
    print(f"{colors.YELLOW}⚠️  {msg}{colors.NC}")


def print_error(msg: str, colors):
    print(f"{colors.RED}❌ {msg}{colors.NC}")


# ----- Deletion helpers -----


def force_rmtree(path: Path):
    def onerror(func, p: str, exc_info):
        try:
            os.chmod(p, stat.S_IWUSR)
        except Exception:
            pass
        try:
            func(p)
        except Exception:
            pass

    shutil.rmtree(path, onerror=onerror)


def force_unlink(path: Path):
    try:
        if not os.access(path, os.W_OK):
            try:
                os.chmod(path, stat.S_IWUSR)
            except Exception:
                pass
        path.unlink(missing_ok=True)
    except Exception:
        pass


# ----- Preview helpers (rich grouping) -----


def summarize_groups(targets: dict) -> List[Tuple[str, int, int]]:
    """Return list of tuples (group_name, item_count, total_bytes) sorted by total_bytes desc."""
    res = []
    for g, items in targets.items():
        cnt = len(items)
        size = sum(get_size(p) for p in items)
        res.append((g, cnt, size))
    res.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return res


def print_rich_preview(root_path: Path, targets: dict, sizes: dict, colors):
    # summary table
    summary = summarize_groups(targets)
    print()
    print(
        f"{colors.CYAN}=== Preview: grouped cleanup summary for {root_path}{colors.NC}"
    )
    print(f"{colors.GRAY}Groups shown sorted by total size (largest first){colors.NC}")
    print()
    # header
    print(
        f" {colors.BLUE}Group{' ' * 30} Items   Size{' ' * 10}Paths (truncated){colors.NC}"
    )
    print(f" {colors.BLUE}{'-' * 70}{colors.NC}")
    for g, cnt, total in summary:
        size_s = format_bytes(total)
        name = g
        print(f" {colors.YELLOW}{name:35}{colors.NC} {cnt:5d}   {size_s:12} ")
    print()
    # detailed listing for each group (top 30 entries per group to avoid flood)
    for g, cnt, total in summary:
        print(
            f"{colors.BLUE}\n📁 {g} — {cnt} item(s), {format_bytes(total)}{colors.NC}"
        )
        group_items = sorted(targets.get(g, []), key=lambda p: (p.is_dir(), str(p)))
        preview_items = group_items[:30]
        for p in preview_items:
            try:
                rel = p.relative_to(root_path)
            except Exception:
                rel = p
            suffix = (
                "/"
                if p.is_dir() and not p.is_symlink()
                else " (symlink)"
                if p.is_symlink()
                else ""
            )
            print(f"   {rel}{suffix} — {format_bytes(sizes.get(p, 0))}")
        if cnt > len(preview_items):
            print(f"   ... and {cnt - len(preview_items)} more items in this group ...")
    print()


# ----- Main -----


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cleanpy_final_prod.py", description="Production-grade Python cleanup tool"
    )
    parser.add_argument(
        "root",
        nargs="*",
        default=["."],
        help="Directories to clean (default: current).",
    )
    parser.add_argument(
        "-p", "--preview", action="store_true", help="Preview only (no deletions)."
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Assume yes (skip interactive confirm).",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Quiet mode: fewer prints."
    )
    parser.add_argument(
        "--clean-venv",
        action="store_true",
        help="Also clean virtualenv folders (.venv, venv...).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob or regex (re:) pattern to exclude. Can be used multiple times.",
    )
    parser.add_argument(
        "--older-than",
        type=int,
        default=0,
        help="Only consider items older than N days.",
    )
    parser.add_argument(
        "--age-type", choices=["mtime", "atime", "ctime"], default="mtime"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force deletion by attempting chmod when needed.",
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create a backup archive before deleting."
    )
    parser.add_argument(
        "--backup-dir", default=None, help="Directory to place backups (default: root)."
    )
    parser.add_argument(
        "--backup-name",
        default=None,
        help="Base name for backups (makes names reproducible).",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output."
    )
    parser.add_argument(
        "--delete-symlinks",
        action="store_true",
        help="Include symlinks in cleanup (delete link only).",
    )
    parser.add_argument("--config", default=None, help="Path to config JSON file.")
    parser.add_argument(
        "--allow-broad-root",
        action="store_true",
        help="Allow running against broad roots like / or home.",
    )
    parser.add_argument(
        "--allow-root", action="store_true", help="Allow running as root (dangerous)."
    )
    parser.add_argument(
        "--lockfile",
        default=".cleanpy.lock",
        help="Path to lockfile (relative to each root).",
    )
    parser.add_argument(
        "--lock-stale-seconds",
        type=int,
        default=DEFAULT_LOCK_TTL,
        help="Stale lock TTL in seconds.",
    )
    parser.add_argument(
        "--log-format", choices=["text", "json"], default="text", help="Logging format."
    )
    parser.add_argument("--log-file", default=None, help="Optional log file path.")
    parser.add_argument(
        "--no-rotate-log", action="store_true", help="Disable log file rotation."
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Force interactive pretty output (colors), useful when piping to terminal.",
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Show version and exit."
    )

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return EXIT_OK

    # logging
    log_file = Path(args.log_file) if args.log_file else None
    level = logging.INFO
    setup_logging(args.log_format, log_file, level=level, rotate=not args.no_rotate_log)

    # determine whether we should use pretty printing
    use_pretty = (
        (args.interactive or sys.stdout.isatty())
        and not args.no_color
        and args.log_format == "text"
    )
    colors = get_colors(use_pretty)

    # root checks (POSIX only)
    try:
        running_as_root = hasattr(os, "geteuid") and os.geteuid() == 0
    except Exception:
        running_as_root = False
    if running_as_root and not args.allow_root:
        logger.error(
            "Running as root is dangerous. Re-run with --allow-root if you really mean it."
        )
        if use_pretty:
            print_error(
                "Running as root is dangerous. Re-run with --allow-root if you really mean it.",
                colors,
            )
        return EXIT_DANGEROUS_ROOT

    root_paths = [Path(r).resolve() for r in args.root]

    if not args.allow_broad_root:
        for rp in root_paths:
            if is_dangerous_root(rp):
                logger.error(
                    "Target root %s looks dangerously broad. Re-run with --allow-broad-root if you mean it.",
                    rp,
                )
                if use_pretty:
                    print_warning(
                        f"Target root {rp} looks dangerously broad. Re-run with --allow-broad-root if you mean it.",
                        colors,
                    )
                return EXIT_DANGEROUS_ROOT

    # signal-safe storage for locks
    acquired_locks: dict[Path, int] = {}

    def _release_all_and_exit(signum=None, frame=None):
        logger.info("Signal received (%s). Releasing locks and exiting.", signum)
        for lp, fd in list(acquired_locks.items()):
            release_lock(fd, lp)
            acquired_locks.pop(lp, None)
        sys.exit(EXIT_CANCELLED)

    # register signals
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(s, _release_all_and_exit)
        except Exception:
            pass

    overall_failed = False

    for root_path in root_paths:
        logger.info("Starting cleanup in %s", root_path)
        if use_pretty:
            print_info(f"Starting Python project cleanup in {root_path}...", colors)

        lock_path = root_path / args.lockfile
        lock_fd = acquire_lock(lock_path, stale_seconds=args.lock_stale_seconds)
        if lock_fd is None:
            logger.error(
                "Unable to acquire lock for %s. Another run might be active (lockfile=%s).",
                root_path,
                lock_path,
            )
            if use_pretty:
                print_error(
                    f"Unable to acquire lock for {root_path}. Another run might be active (lockfile={lock_path}).",
                    colors,
                )
            for lp, fd in list(acquired_locks.items()):
                release_lock(fd, lp)
            return EXIT_LOCK_ERROR
        acquired_locks[lock_path] = lock_fd

        try:
            # load config
            config = {}
            cfg_path = Path(args.config) if args.config else root_path / ".cleanpy.json"
            if cfg_path.exists():
                try:
                    with open(cfg_path) as f:
                        config = json.load(f)
                    logger.info("Loaded config %s", cfg_path)
                except Exception as e:
                    logger.warning("Failed to load config %s: %s", cfg_path, e)

            dir_groups = {
                "Python Caches": ["__pycache__"],
                "Build/Packaging": [
                    "*.egg-info",
                    "build",
                    "dist",
                    ".eggs",
                    "wheels",
                    "__pypackages__",
                    ".pdm-build",
                    "pip-wheel-metadata",
                    ".hatch",
                ],
                "Testing/Linting/Type-Checking": [
                    ".pytest_cache",
                    ".mypy_cache",
                    ".ruff_cache",
                    ".tox",
                    ".nox",
                    "htmlcov",
                    ".coverage_html",
                    ".hypothesis",
                    ".benchmarks",
                    ".dmypy",
                    ".pytype",
                    ".pyre",
                    "cover",
                ],
                "Jupyter": [".ipynb_checkpoints"],
                "Documentation": ["docs/_build"],
                "Cython": ["cython_debug"],
            }
            for g, pats in config.get("dir_groups", {}).items():
                if g in dir_groups:
                    dir_groups[g] += pats
                else:
                    dir_groups[g] = pats
            if args.clean_venv:
                venv_pats = [".venv", "venv", "env", "ENV", ".virtualenv"]
                dir_groups.setdefault("Virtual Environments", []).extend(venv_pats)

            file_groups = {
                "Python Bytecode": ["*.pyc", "*.pyo", "*.pyd"],
                "Coverage": [".coverage", "coverage.xml", "nosetests.xml", "*.cover"],
                "Editor/OS Temps": [
                    "*.swp",
                    "*.swo",
                    "*~",
                    "*.bak",
                    ".DS_Store",
                    "Thumbs.db",
                    "desktop.ini",
                    "._*",
                ],
                "DB Temps": ["*.db-wal", "*.db-shm"],
                "General Temps": ["*.tmp", "*.temp", "*.log", "CACHEDIR.TAG"],
                "Profiling": ["*.prof"],
                "Installer Logs": ["pip-log.txt", "pip-delete-this-directory.txt"],
                "PyInstaller": ["*.manifest", "*.spec"],
            }
            for g, pats in config.get("file_groups", {}).items():
                if g in file_groups:
                    file_groups[g] += pats
                else:
                    file_groups[g] = pats

            exclude_dirs = {".git", ".svn", ".hg", ".idea", ".vscode"} | set(
                config.get("exclude_dirs", [])
            )
            exclude_patterns = []
            excludes = list(args.exclude) + config.get("exclude_patterns", [])
            for ex in excludes:
                if isinstance(ex, str) and ex.startswith("re:"):
                    try:
                        exclude_patterns.append(("re", re.compile(ex[3:])))
                    except re.error:
                        logger.warning("Invalid regex exclude %s", ex)
                else:
                    exclude_patterns.append(("glob", ex))

            older_than_sec = args.older_than * 86400 if args.older_than > 0 else 0

            # scan
            targets = defaultdict(list)
            for root, dirs, files in os.walk(
                root_path, topdown=True, followlinks=False
            ):
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                try:
                    rel_root = Path(root).relative_to(root_path)
                except Exception:
                    rel_root = Path(".")
                for d in list(dirs):
                    d_path = Path(root) / d
                    if d_path.is_symlink() and not args.delete_symlinks:
                        continue
                    if older_than_sec and not is_old_enough(
                        d_path, older_than_sec, args.age_type
                    ):
                        continue
                    rel_str = str(rel_root / d)
                    if any(
                        (pt == "re" and pat.search(rel_str))
                        or (pt == "glob" and fnmatch.fnmatch(rel_str, pat))
                        for pt, pat in exclude_patterns
                    ):
                        dirs.remove(d)
                        continue
                    matched = False
                    for g, pats in dir_groups.items():
                        for pat in pats:
                            try:
                                if fnmatch.fnmatch(d, pat) or fnmatch.fnmatch(
                                    rel_str, pat
                                ):
                                    targets[g].append(d_path)
                                    matched = True
                                    break
                            except Exception:
                                continue
                        if matched:
                            break
                    if matched and d in dirs:
                        dirs.remove(d)
                for f in files:
                    f_path = Path(root) / f
                    if f_path.is_symlink() and not args.delete_symlinks:
                        continue
                    if older_than_sec and not is_old_enough(
                        f_path, older_than_sec, args.age_type
                    ):
                        continue
                    rel_str = str(rel_root / f)
                    if any(
                        (pt == "re" and pat.search(rel_str))
                        or (pt == "glob" and fnmatch.fnmatch(rel_str, pat))
                        for pt, pat in exclude_patterns
                    ):
                        continue
                    for g, pats in file_groups.items():
                        matched = False
                        for pat in pats:
                            try:
                                if fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(
                                    rel_str, pat
                                ):
                                    targets[g].append(f_path)
                                    matched = True
                                    break
                            except Exception:
                                continue
                        if matched:
                            break

            all_targets = [
                p for group_targets in targets.values() for p in group_targets
            ]
            total_items = len(all_targets)

            if total_items == 0:
                logger.info("Project is already clean. No targets found.")
                if use_pretty:
                    print_success("Project is already clean. No targets found.", colors)
                release_lock(lock_fd, lock_path)
                acquired_locks.pop(lock_path, None)
                continue

            sizes = {p: get_size(p) for p in all_targets}
            total_size = sum(sizes.values())
            size_str = format_bytes(total_size)

            if args.quiet:
                logger.info(
                    "Found %d items (estimated space: %s).", total_items, size_str
                )
            else:
                if use_pretty:
                    print_rich_preview(root_path, targets, sizes, colors)
                else:
                    logger.info(
                        "Found %d items to clean (approx %s).", total_items, size_str
                    )

            if args.preview:
                logger.info("Dry run complete. No files were deleted.")
                if use_pretty:
                    print_info("Dry run complete. No files were deleted.", colors)
                release_lock(lock_fd, lock_path)
                acquired_locks.pop(lock_path, None)
                continue

            if total_size > DEFAULT_LARGE_THRESHOLD:
                logger.warning(
                    "Large amount of data to delete (%s > 100MB). Proceed with caution.",
                    size_str,
                )
                if use_pretty:
                    print_warning(
                        f"Large amount of data to delete ({size_str} > 100MB). Proceed with caution.",
                        colors,
                    )

            if not args.yes:
                try:
                    prompt = "Proceed with deletion? (y/N): "
                    ans = input(prompt).strip().lower()
                except EOFError:
                    ans = "n"
                if ans not in ("y", "yes"):
                    logger.info("Operation cancelled by user.")
                    if use_pretty:
                        print_info("Operation cancelled by user.", colors)
                    release_lock(lock_fd, lock_path)
                    acquired_locks.pop(lock_path, None)
                    return EXIT_CANCELLED

            # backup
            if args.backup:
                backup_root = (
                    Path(args.backup_dir).resolve() if args.backup_dir else root_path
                )
                logger.info("Creating backup in %s", backup_root)
                res = backup_targets_atomic(
                    all_targets, backup_root, root_path, name=args.backup_name
                )
                if not res:
                    logger.error("Backup failed; aborting deletion for safety.")
                    release_lock(lock_fd, lock_path)
                    acquired_locks.pop(lock_path, None)
                    return EXIT_UNKNOWN_ERROR
                else:
                    archive_file, sha = res
                    logger.info("Backup created: %s (sha256=%s)", archive_file, sha)
                    if use_pretty:
                        print_success(
                            f"Backup created: {archive_file} (sha256={sha})", colors
                        )

            # deletion
            failed = False
            sorted_targets = sorted(
                all_targets, key=lambda p: str(p.relative_to(root_path))
            )
            total = len(sorted_targets)
            for i, p in enumerate(sorted_targets, 1):
                if not args.quiet:
                    suffix = (
                        "/"
                        if p.is_dir() and not p.is_symlink()
                        else " (symlink)"
                        if p.is_symlink()
                        else ""
                    )
                    msg = (
                        f"[{i}/{total}] Deleting {p.relative_to(root_path)}{suffix}..."
                    )
                    if use_pretty:
                        print(msg)
                    else:
                        logger.info(msg)
                try:
                    if p.is_symlink():
                        if args.delete_symlinks:
                            p.unlink(missing_ok=True)
                    elif p.is_file():
                        if args.force:
                            force_unlink(p)
                        else:
                            p.unlink(missing_ok=True)
                    elif p.is_dir():
                        if args.force:
                            force_rmtree(p)
                        else:
                            try:
                                shutil.rmtree(p)
                            except FileNotFoundError:
                                pass
                except Exception as e:
                    logger.warning("Failed to delete %s: %s", p, e)
                    if use_pretty:
                        print_warning(
                            f"Failed to delete {p.relative_to(root_path)}: {e}", colors
                        )
                    failed = True

            if failed:
                logger.warning(
                    "Some items could not be deleted. Consider --force or check permissions."
                )
                overall_failed = True
            else:
                logger.info(
                    "Cleanup complete for %s. Freed approximately %s.",
                    root_path,
                    size_str,
                )
                if use_pretty:
                    print_success(
                        f"Cleanup complete! Freed approximately {size_str}.", colors
                    )

        finally:
            # release this lock
            release_lock(lock_fd, lock_path)
            acquired_locks.pop(lock_path, None)

    if overall_failed:
        return EXIT_PARTIAL_FAILURE
    return EXIT_OK


if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        sys.exit(EXIT_CANCELLED)
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(EXIT_UNKNOWN_ERROR)
    sys.exit(exit_code)
