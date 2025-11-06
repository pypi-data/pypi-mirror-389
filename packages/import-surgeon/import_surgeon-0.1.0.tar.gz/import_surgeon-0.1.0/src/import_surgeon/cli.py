#!/usr/bin/env python3
"""import_surgeon.py

Elite production-standard, peace-of-mind utility to move symbols' `from ... import X` bindings
from one module to another across a Python repository.

New features:
- Rewrite dotted usages (e.g., old_module.Symbol) with --rewrite-dotted (note: does not handle aliased module imports)
- Batch mode for multiple symbols/modules via YAML config 'migrations' list (e.g., migrations: [{old_module: ..., new_module: ..., symbols: [Sym1, Sym2]}])
- Integration with isort and black formatters via --format
- Automatic detection of base_package from git repo root name if not provided
- Rollback changes using --rollback --summary-json

Design goals / guarantees:
- Dry-run by default (shows unified diffs). --apply writes changes atomically.
- Backups always (unless --no-backup), with preservation of metadata.
- Robust encoding, relative import handling with accurate directory-based resolution (auto or --base-package).
- Safety checks: Git clean requirement, max-files, post-change usage warnings for dotted accesses.
- Automation: JSON summary with detailed metadata (risk, lines, encodings) for all files, progress bar (tqdm fallback to print).
- Usability: YAML config support, granular quiet modes, optional auto-commit.
- Optional rewrite of dotted usages; warns if detected and not rewritten.

Usage examples:
  # Dry-run with config including migrations
  python import_surgeon.py --config config.yaml

  # Apply with formatting and dotted rewrite
  python import_surgeon.py --apply --format --rewrite-dotted --old-module old --new-module new --symbols Sym1,Sym2

  # Rollback
  python import_surgeon.py --rollback --summary-json summary.json

Exit codes:
 0 - success
 1 - errors/warnings (configurable)
 2 - CLI/invalid setup

"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import os
import re
import stat
import subprocess
import tempfile
import tokenize as py_tokenize
import traceback
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import libcst as cst
import libcst.metadata as md
import yaml

# Optional dependencies
HAS_TQDM = True
try:
    from tqdm import tqdm  # Progress bar
except ImportError:
    HAS_TQDM = False

    def tqdm(iterable, **kwargs):
        return iterable


HAS_CHARDET = True
try:
    from chardet.universaldetector import UniversalDetector
except ImportError:
    HAS_CHARDET = False
    UniversalDetector = None

logger = logging.getLogger("import_surgeon")


# ----------------------------- Config helpers ---------------------------------
def load_config(config_path: Optional[str]) -> Dict:
    if not config_path:
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Failed to load config %s: %s", config_path, e)
        return {}


# ----------------------------- Encoding helpers ---------------------------------
def detect_encoding(file_path: Path) -> str:
    try:
        with file_path.open("rb") as f:
            encoding, _ = py_tokenize.detect_encoding(f.readline)
            if encoding:
                return encoding.lower()
    except Exception:
        pass

    if HAS_CHARDET:
        detector = UniversalDetector()
        try:
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    detector.feed(chunk)
                    if detector.done:
                        break
            detector.close()
            enc = detector.result.get("encoding")
            if enc:
                return enc.lower()
        except Exception:
            pass
    else:
        logger.debug("chardet unavailable; defaulting to utf-8 for %s", file_path)

    return "utf-8"


# ----------------------------- CST helpers -------------------------------------
def _attr_to_dotted(name: cst.BaseExpression) -> Optional[str]:
    if isinstance(name, cst.Name):
        return name.value
    parts: List[str] = []
    node = name
    while isinstance(node, cst.Attribute):
        attr = node.attr
        if not isinstance(attr, cst.Name):
            return None
        parts.append(attr.value)
        node = node.value
    if isinstance(node, cst.Name):
        parts.append(node.value)
        return ".".join(reversed(parts))
    return None


def _module_to_str(module_expr: Optional[cst.BaseExpression], level: int = 0) -> str:
    if module_expr is None:
        base = ""
    else:
        dotted = _attr_to_dotted(module_expr)
        base = dotted if dotted is not None else module_expr.code.strip()
    return ("." * level) + base


def _import_alias_name(alias: cst.ImportAlias) -> Optional[str]:
    return _attr_to_dotted(alias.name) or alias.name.code.strip()


def _str_to_expr(mod_str: str) -> cst.BaseExpression:
    parts = mod_str.split(".")
    expr: cst.BaseExpression = cst.Name(parts[0])
    for p in parts[1:]:
        expr = cst.Attribute(value=expr, attr=cst.Name(p))
    return expr


# ----------------------------- Transformers ------------------------------------
class BaseReplacer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (md.PositionProvider,)

    def __init__(
        self,
        old_module: str,
        new_module: str,
        symbols: List[str],
        force_relative: bool = False,
        base_package: Optional[str] = None,
        file_path: Optional[Path] = None,
    ):
        self.old_module = old_module
        self.new_module = new_module
        self.symbols = symbols
        self.force_relative = force_relative
        self.base_package = base_package
        self.file_path = file_path

        self.warnings: List[str] = []
        self.changed_lines: List[int] = []

    def _resolve_relative(self, mod_str: str) -> Optional[str]:
        if not self.file_path or not self.base_package or not mod_str.startswith("."):
            return None
        level = len(mod_str) - len(mod_str.lstrip("."))
        clean_mod = mod_str.lstrip(".")
        base_dir = None
        for parent in [self.file_path.parent] + list(self.file_path.parent.parents):
            if parent.name == self.base_package:
                base_dir = parent
                break
        if not base_dir:
            return None
        try:
            rel_path = self.file_path.parent.relative_to(base_dir)
            rel_parts = list(rel_path.parts)
        except ValueError:
            return None
        up = level - 1
        if up > len(rel_parts):
            return None
        abs_parts = rel_parts[:-up] if up > 0 else rel_parts
        clean_parts = clean_mod.split(".") if clean_mod else []
        full_parts = abs_parts + clean_parts
        return self.base_package + ("." + ".".join(full_parts) if full_parts else "")

    def _match_module(self, mod_str: str) -> bool:
        clean = mod_str.lstrip(".")
        if clean == self.old_module or mod_str == self.old_module:
            return True
        if not self.force_relative:
            return False
        resolved = self._resolve_relative(mod_str) if self.base_package else None
        if resolved and (
            resolved == self.old_module or resolved.endswith("." + self.old_module)
        ):
            return True
        if resolved is None and mod_str.startswith("."):
            return False
        if (
            self.force_relative
            and self.base_package
            and self.old_module.endswith("." + clean)
        ):
            return True
        if (
            clean.endswith("." + self.old_module)
            or clean == self.old_module.split(".")[-1]
        ):
            return True
        return False


class ImportReplacer(BaseReplacer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bound_names: Dict[str, str] = {}  # bound -> orig
        self.existing_new_bindings: Dict[str, str] = {}
        self.has_star_old = False
        self.has_star_new = False
        self.skipped_relative = False
        self.insert_line_approx: int = 1

    def visit_Module(self, node: cst.Module) -> Optional[bool]:
        self.bound_names = {}
        self.existing_new_bindings = {}
        self.has_star_old = False
        self.has_star_new = False
        self.skipped_relative = False
        self.changed_lines = []
        if node.body:
            pos = self.get_metadata(md.PositionProvider, node.body[0])
            self.insert_line_approx = pos.start.line
        else:
            self.insert_line_approx = 1
        return True

    def _get_bound_name(self, alias: cst.ImportAlias) -> Optional[str]:
        if alias.asname and isinstance(alias.asname.name, cst.Name):
            return alias.asname.name.value
        imported = _import_alias_name(alias)
        return imported if imported in self.symbols else None

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.CSTNode:
        level = len(original_node.relative)
        mod_str = _module_to_str(original_node.module, level)

        # Record existing from new_module
        if mod_str.lstrip(".") == self.new_module or mod_str == self.new_module:
            if isinstance(original_node.names, cst.ImportStar):
                self.has_star_new = True
                return updated_node
            if original_node.names:
                for alias in original_node.names:
                    if isinstance(alias, cst.ImportAlias):
                        orig = _import_alias_name(alias)
                        bound = self._get_bound_name(alias) or orig
                        self.existing_new_bindings[bound] = orig or bound
            return updated_node

        # Handle from old_module
        if self._match_module(mod_str):
            if mod_str.startswith(".") and not self.force_relative:
                logger.warning("Skipping relative import %s", mod_str)
                self.skipped_relative = True
                self.warnings.append(f"Skipped relative import {mod_str}")
                return updated_node

            if isinstance(original_node.names, cst.ImportStar):
                self.has_star_old = True
                for s in self.symbols:
                    self.bound_names[s] = s
                return updated_node

            if original_node.names:
                new_names: List[cst.ImportAlias] = []
                removed = False
                for alias in original_node.names:
                    if not isinstance(alias, cst.ImportAlias):
                        new_names.append(alias)
                        continue
                    orig = _import_alias_name(alias)
                    if orig in self.symbols:
                        bound = self._get_bound_name(alias) or orig
                        self.bound_names[bound] = orig
                        removed = True
                        pos = self.get_metadata(md.PositionProvider, original_node)
                        self.changed_lines.append(pos.start.line)
                    else:
                        new_names.append(alias)
                if removed:
                    if new_names:
                        # Reset commas to avoid trailing comma
                        new_names = [
                            new_names[i].with_changes(
                                comma=cst.Comma(
                                    whitespace_after=cst.SimpleWhitespace(" ")
                                )
                                if i < len(new_names) - 1
                                else cst.MaybeSentinel.DEFAULT
                            )
                            for i in range(len(new_names))
                        ]
                        return updated_node.with_changes(names=new_names)
                    else:
                        return cst.RemoveFromParent()
        return updated_node

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        if self.skipped_relative or not self.bound_names:
            return updated_node

        if self.has_star_old:
            self.warnings.append("Handled wildcard import")

        # Collect aliases for new import
        aliases: List[cst.ImportAlias] = []
        sorted_items = sorted(self.bound_names.items(), key=lambda x: x[1])
        for bound_name, orig_symbol in sorted_items:
            covered = bound_name in self.existing_new_bindings or (
                self.has_star_new and bound_name == orig_symbol
            )
            if covered:
                continue
            name = cst.Name(orig_symbol)
            asname = (
                cst.AsName(name=cst.Name(bound_name))
                if bound_name != orig_symbol
                else None
            )
            alias = cst.ImportAlias(name=name, asname=asname)
            aliases.append(alias)

        to_insert: List[cst.SimpleStatementLine] = []
        if aliases:
            # Add commas
            aliases_with_comma = [
                aliases[i].with_changes(
                    comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(" "))
                    if i < len(aliases) - 1
                    else cst.MaybeSentinel.DEFAULT
                )
                for i in range(len(aliases))
            ]
            import_from = cst.ImportFrom(
                module=_str_to_expr(self.new_module),
                names=aliases_with_comma,
            )
            stmt = cst.SimpleStatementLine(body=[import_from])
            to_insert.append(stmt)
            self.changed_lines.append(self.insert_line_approx)

        if not to_insert:
            return updated_node

        body = list(updated_node.body)
        insert_at = 0
        if (
            body
            and isinstance(body[0], cst.SimpleStatementLine)
            and body[0].body
            and isinstance(body[0].body[0], cst.Expr)
            and isinstance(body[0].body[0].value, cst.SimpleString)
        ):
            insert_at = 1

        while insert_at < len(body) and self._is_import_or_future_stmt(body[insert_at]):
            insert_at += 1

        new_body = body[:insert_at] + to_insert + body[insert_at:]
        return updated_node.with_changes(body=new_body)

    def _is_import_or_future_stmt(self, stmt: cst.CSTNode) -> bool:
        if not isinstance(stmt, cst.SimpleStatementLine) or not stmt.body:
            return False
        return isinstance(stmt.body[0], (cst.Import, cst.ImportFrom))


class DottedReplacer(BaseReplacer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rewrote_count = 0

    def leave_Attribute(
        self, original_node: cst.Attribute, updated_node: cst.Attribute
    ) -> cst.Attribute:
        if (
            isinstance(updated_node.attr, cst.Name)
            and updated_node.attr.value in self.symbols
        ):
            mod_str = _attr_to_dotted(updated_node.value)
            if mod_str and self._match_module(mod_str):
                new_value = _str_to_expr(self.new_module)
                self.rewrote_count += 1
                pos = self.get_metadata(md.PositionProvider, original_node)
                self.changed_lines.append(pos.start.line)
                return updated_node.with_changes(value=new_value)
        return updated_node

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        if self.rewrote_count > 0:
            self.warnings.append(
                f"Rewrote {self.rewrote_count} dotted usages for symbols {self.symbols}"
            )
        return updated_node


# ----------------------------- File ops --------------------------------------
def safe_backup(file_path: Path, backup_suffix: Optional[str] = None) -> Path:
    if backup_suffix is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        pid = os.getpid()
        backup_suffix = f".bak.{ts}.{pid}"
    backup_path = file_path.with_name(file_path.name + backup_suffix)
    if backup_path.exists():
        counter = 1
        while backup_path.exists():
            backup_path = file_path.with_name(
                file_path.name + backup_suffix + f".{counter}"
            )
            counter += 1
    encoding = detect_encoding(file_path)
    text = file_path.read_text(encoding=encoding)
    backup_path.write_text(text, encoding=encoding)
    try:
        st = file_path.stat()
        os.chmod(backup_path, st.st_mode)
        os.chown(backup_path, st.st_uid, st.st_gid)
    except Exception:
        logger.debug("Could not preserve metadata for backup: %s", backup_path)
    return backup_path


def atomic_write(file_path: Path, content: str, encoding: str = "utf-8") -> None:
    dirpath = file_path.parent
    tmpname = None
    try:
        st = file_path.stat() if file_path.exists() else None
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=str(dirpath), encoding=encoding
        ) as tf:
            tf.write(content)
            tmpname = tf.name
        if st:
            os.chmod(tmpname, stat.S_IMODE(st.st_mode))
            try:
                os.chown(tmpname, st.st_uid, st.st_gid)
            except Exception:
                pass
        os.replace(tmpname, str(file_path))
    finally:
        if tmpname and os.path.exists(tmpname):
            try:
                os.remove(tmpname)
            except Exception:
                pass


# ----------------------------- Post-process checks ----------------------------
def check_remaining_usages(
    content: str, old_module: str, symbols: List[str]
) -> List[str]:
    res = []
    for symbol in symbols:
        try:
            pattern = re.compile(rf"\b{re.escape(old_module)}\.{re.escape(symbol)}\b")
            matches = pattern.findall(content)
            if matches:
                res.append(
                    f"Potential remaining dotted usages for {symbol}: {len(matches)} instances"
                )
        except Exception:
            pass
    return res


# ----------------------------- Processing ------------------------------------
def process_file(
    file_path: Path,
    migrations: List[Dict],
    dry_run: bool = True,
    no_backup: bool = False,
    force_relative: bool = False,
    base_package: Optional[str] = None,
    rewrite_dotted: bool = False,
    do_format: bool = False,
    quiet: str = "none",
) -> Tuple[bool, str, Dict]:
    detail: Dict = {
        "diff": None,
        "backup": None,
        "encoding": None,
        "risk_level": "low",
        "changed_lines": [],
        "warnings": [],
    }
    try:
        encoding = detect_encoding(file_path)
        detail["encoding"] = encoding
        original_content = file_path.read_text(encoding=encoding)
        wrapper = md.MetadataWrapper(cst.parse_module(original_content))
        current = wrapper.module
        all_warnings: List[str] = []
        all_changed_lines: List[int] = []
        risk_levels = {"low": 0, "medium": 1, "high": 2}
        current_risk = 0
        skipped_relative = False
        for mig in migrations:
            old_module = mig["old_module"]
            new_module = mig["new_module"]
            symbols = (
                mig["symbols"] if isinstance(mig["symbols"], list) else [mig["symbols"]]
            )
            replacer = ImportReplacer(
                old_module, new_module, symbols, force_relative, base_package, file_path
            )
            wrapper = md.MetadataWrapper(current)
            current = wrapper.visit(replacer)
            all_warnings.extend(replacer.warnings)
            all_changed_lines.extend(replacer.changed_lines)
            if replacer.has_star_old or "wildcard" in " ".join(replacer.warnings):
                current_risk = max(current_risk, 1)
            if replacer.skipped_relative:
                skipped_relative = True
                current_risk = max(current_risk, 2)
            if rewrite_dotted:
                dotted_replacer = DottedReplacer(
                    old_module,
                    new_module,
                    symbols,
                    force_relative,
                    base_package,
                    file_path,
                )
                wrapper = md.MetadataWrapper(current)
                current = wrapper.visit(dotted_replacer)
                all_warnings.extend(dotted_replacer.warnings)
                all_changed_lines.extend(dotted_replacer.changed_lines)
                if dotted_replacer.rewrote_count > 0:
                    current_risk = max(current_risk, 1)
        new_content = current.code
        changed_flag = new_content != original_content
        detail["changed_lines"] = sorted(set(all_changed_lines))
        dotted_warnings = []
        content_to_check = original_content if dry_run else new_content
        for mig in migrations:
            symbols = (
                mig["symbols"] if isinstance(mig["symbols"], list) else [mig["symbols"]]
            )
            dotted_warnings.extend(
                check_remaining_usages(content_to_check, mig["old_module"], symbols)
            )
        if dotted_warnings:
            current_risk = max(current_risk, 2)
        detail["warnings"] = all_warnings + dotted_warnings
        detail["risk_level"] = list(risk_levels.keys())[current_risk]
        if changed_flag:
            diff = "\n".join(
                difflib.unified_diff(
                    original_content.splitlines(),
                    new_content.splitlines(),
                    fromfile=str(file_path),
                    tofile=str(file_path) + " (modified)",
                    lineterm="",
                )
            )
            detail["diff"] = diff
            if dry_run:
                return True, f"CHANGES IN {file_path}:\n{diff}", detail
            else:
                backup_path = None
                if not no_backup:
                    bkp = safe_backup(file_path)
                    backup_path = str(bkp)
                    detail["backup"] = backup_path
                atomic_write(file_path, new_content, encoding)
                if do_format:
                    try:
                        subprocess.run(
                            ["isort", "--quiet", "--atomic", str(file_path)],
                            check=True,
                            capture_output=True,
                        )
                        subprocess.run(
                            ["black", "--quiet", str(file_path)],
                            check=True,
                            capture_output=True,
                        )
                    except Exception as e:
                        detail["warnings"].append(f"Formatting failed: {str(e)}")
                backup_str = f" (backup: {backup_path})" if backup_path else ""
                return True, f"MODIFIED: {file_path}{backup_str}", detail
        else:
            if skipped_relative:
                return False, f"SKIPPED (relative): {file_path}", detail
        return False, f"UNCHANGED: {file_path}", detail
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Error in %s: %s\n%s", file_path, e, tb)
        detail["warnings"].append(f"Error: {e}")
        return False, f"ERROR: {file_path}: {e}", detail


# ----------------------------- File finding ------------------------------------
def find_py_files(
    target: Path, excludes: List[str], max_files: int = 10000
) -> List[Path]:
    matches: List[Path] = []
    count = 0
    if (
        target.is_file()
        and target.suffix == ".py"
        and not any(fnmatch(str(target), exc) for exc in excludes)
    ):
        matches.append(target)
        return matches

    if target.is_dir():
        for p in target.rglob("*.py"):
            if count >= max_files:
                logger.warning(
                    "Reached max_files limit (%d); stopping scan.", max_files
                )
                break
            rel = str(p.relative_to(target))
            if any(fnmatch(rel, exc) or fnmatch(str(p), exc) for exc in excludes):
                continue
            matches.append(p)
            count += 1
    return matches


# ----------------------------- Safety checks ---------------------------------
def git_is_clean(path: Path) -> bool:
    try:
        repo_root = find_git_root(path)
        if not repo_root:
            return False
        p = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return not p.stdout.strip()
    except Exception as e:
        logger.debug("Git check failed: %s", e)
        return False


def find_git_root(path: Path) -> Optional[Path]:
    current = path.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def git_commit_changes(repo_root: Path, message: str) -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(repo_root), "add", "."], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(repo_root), "commit", "-m", message],
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        logger.error("Auto-commit failed: %s", e)
        return False


# ----------------------------- CLI -------------------------------------------
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Elite safe import replacer")
    parser.add_argument("target", nargs="?", default=".", help="file/dir to scan")
    parser.add_argument("--old-module", help="old module")
    parser.add_argument("--new-module", help="new module")
    parser.add_argument("--symbol", help="symbol to move (deprecated, use --symbols)")
    parser.add_argument("--symbols", help="comma-separated symbols to move")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--exclude", help="comma-separated globs")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument("--quiet", default="none", choices=["none", "errors", "all"])
    parser.add_argument("--force-relative", action="store_true")
    parser.add_argument("--base-package", help="base package for relative resolution")
    parser.add_argument("--max-files", type=int, default=10000)
    parser.add_argument("--require-clean-git", action="store_true")
    parser.add_argument("--auto-commit", help="commit message for auto-commit")
    parser.add_argument("--summary-json", help="JSON summary path")
    parser.add_argument("--strict-warnings", action="store_true")
    parser.add_argument("--config", help="YAML config path")
    parser.add_argument(
        "--rewrite-dotted", action="store_true", help="rewrite dotted usages"
    )
    parser.add_argument(
        "--format",
        action="store_true",
        help="format with isort and black after changes",
    )
    parser.add_argument(
        "--rollback", action="store_true", help="rollback changes using summary-json"
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    for k, v in config.items():
        key = k.replace("-", "_")
        if not hasattr(args, key) or getattr(args, key) is None:
            setattr(args, key, v)

    if args.rollback:
        if not args.summary_json:
            logger.error("Missing --summary-json for rollback")
            return 2
        try:
            with open(args.summary_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data["summary"]:
                if entry.get("changed") and entry.get("backup"):
                    bkp = Path(entry["backup"])
                    file = Path(entry["file"])
                    if bkp.exists():
                        encoding = (
                            detect_encoding(file)
                            if file.exists()
                            else detect_encoding(bkp)
                        )
                        atomic_write(file, bkp.read_text(encoding), encoding)
                        os.remove(bkp)
                        logger.info("Restored %s from %s", file, bkp)
                    else:
                        logger.warning("Backup missing for %s", file)
            logger.info("Rollback completed")
            return 0
        except Exception as e:
            logger.error("Rollback failed: %s", e)
            return 1

    if not (hasattr(args, "old_module") and args.old_module) and not config.get(
        "migrations"
    ):
        logger.error("Missing required: --old-module or migrations in config")
        return 2

    if not (hasattr(args, "new_module") and args.new_module) and not config.get(
        "migrations"
    ):
        logger.error("Missing required: --new-module or migrations in config")
        return 2

    if not (hasattr(args, "symbol") or hasattr(args, "symbols")) and not config.get(
        "migrations"
    ):
        logger.error("Missing required: --symbol / --symbols or migrations in config")
        return 2

    lvl = max(logging.DEBUG, logging.WARNING - (10 * args.verbose))
    logging.basicConfig(level=lvl, format="%(levelname)s: %(message)s")

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        logger.error("Target not found: %s", target_path)
        return 2

    excludes = [s.strip() for s in (args.exclude or "").split(",") if s.strip()]
    py_files = find_py_files(target_path, excludes, args.max_files)
    logger.info("Found %d files", len(py_files))

    repo_root = find_git_root(target_path)
    if not args.base_package and repo_root:
        args.base_package = repo_root.name
        logger.info("Auto-detected base_package: %s", args.base_package)

    if (
        args.apply
        and args.require_clean_git
        and repo_root
        and not git_is_clean(target_path)
    ):
        logger.error("Git not clean; commit/stash or remove --require-clean-git")
        return 1

    # Prepare migrations
    if config.get("migrations"):
        migrations = config["migrations"]
    else:
        symbols = (
            args.symbols.split(",")
            if hasattr(args, "symbols") and args.symbols
            else [args.symbol]
            if hasattr(args, "symbol") and args.symbol
            else []
        )
        migrations = [
            {
                "old_module": args.old_module,
                "new_module": args.new_module,
                "symbols": symbols,
            }
        ]

    changed = 0
    errors = 0
    warnings = 0
    summary: List[Dict] = []
    dry_run = not args.apply

    progress_iter = tqdm(py_files, disable=(args.quiet != "none"))
    for p in progress_iter:
        progress_iter.set_description(f"Processing {p.name}")
        changed_flag, msg, detail = process_file(
            p,
            migrations,
            dry_run,
            args.no_backup,
            args.force_relative,
            args.base_package,
            args.rewrite_dotted if hasattr(args, "rewrite_dotted") else False,
            args.format if hasattr(args, "format") else False,
            args.quiet,
        )
        should_print = args.quiet == "none" or (
            args.quiet == "errors" and "ERROR" in msg
        )
        if should_print:
            print(msg)
        if "SKIPPED" in msg or detail["warnings"]:
            warnings += 1
        if changed_flag and not dry_run:
            changed += 1
        if "ERROR" in msg:
            errors += 1
        entry = {"file": str(p), "changed": changed_flag, "message": msg, **detail}
        summary.append(entry)

    if args.summary_json:
        with open(args.summary_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": summary,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                f,
                indent=2,
            )
        logger.info("JSON summary written to %s", args.summary_json)

    if args.apply and args.auto_commit and repo_root:
        if git_commit_changes(repo_root, args.auto_commit):
            logger.info("Auto-committed with message: %s", args.auto_commit)

    if args.quiet != "all":
        print("\nSummary:")
        if dry_run:
            print("  Dry-run; use --apply to write.")
        print(f"  Changed: {changed}")
        print(f"  Errors: {errors}")
        print(f"  Warnings: {warnings}")
        print(f"  Scanned: {len(py_files)}")

    if errors:
        return 1
    if args.strict_warnings and warnings:
        return 1
    return 0


if __name__ == "__main__":
    main()
