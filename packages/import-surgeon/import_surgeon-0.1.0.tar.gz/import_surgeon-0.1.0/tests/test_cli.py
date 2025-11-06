#!/usr/bin/env python3
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import libcst as cst
import libcst.metadata as md
import yaml

import import_surgeon
# Import the script modules
from import_surgeon.cli import (
    DottedReplacer,
    ImportReplacer,
    _attr_to_dotted,
    _import_alias_name,
    _module_to_str,
    _str_to_expr,
    check_remaining_usages,
    detect_encoding,
    find_git_root,
    find_py_files,
    git_commit_changes,
    git_is_clean,
    load_config,
    main,
    parse_args,
    process_file,
)

class TestSafeReplaceImports(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        logging.disable(logging.CRITICAL)  # Suppress logs during tests

    def tearDown(self):
        self.temp_dir.cleanup()
        logging.disable(logging.NOTSET)

    # Test config helpers
    def test_load_config_valid(self):
        config_path = self.temp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"old-module": "old"}, f)
        config = load_config(str(config_path))
        self.assertEqual(config, {"old-module": "old"})

    def test_load_config_invalid(self):
        config_path = self.temp_path / "invalid.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: here")
        with patch("logging.Logger.warning") as mock_warn:
            config = load_config(str(config_path))
            self.assertEqual(config, {})
            mock_warn.assert_called()

    def test_load_config_missing(self):
        config = load_config(None)
        self.assertEqual(config, {})

    # Test encoding helpers
    def test_detect_encoding_utf8(self):
        file_path = self.temp_path / "test.py"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# coding: utf-8\nprint('hello')")
        enc = detect_encoding(file_path)
        self.assertEqual(enc, "utf-8")

    def test_detect_encoding_no_declaration(self):
        file_path = self.temp_path / "test.py"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("print('hello')")
        enc = detect_encoding(file_path)
        self.assertEqual(enc, "utf-8")  # Default fallback

    @patch("import_surgeon.cli.HAS_CHARDET", True)
    @patch(
        "import_surgeon.cli.py_tokenize.detect_encoding", return_value=(None, [])
    )
    @patch("import_surgeon.cli.UniversalDetector")
    def test_detect_encoding_chardet(self, mock_detector, mock_tokenize):
        mock_inst = mock_detector.return_value
        mock_inst.result = {"encoding": "ascii"}
        file_path = self.temp_path / "test.py"
        file_path.write_bytes(b"print('hello')")
        enc = detect_encoding(file_path)
        self.assertEqual(enc, "ascii")

    # New test: Non-UTF8 encoding
    def test_detect_encoding_latin1(self):
        file_path = self.temp_path / "test.py"
        with open(file_path, "wb") as f:
            f.write(b"# -*- coding: latin-1 -*-\nprint('\xe9')")
        enc = detect_encoding(file_path)
        self.assertIn(enc, ["latin-1", "iso-8859-1", "latin1"])
        content = file_path.read_text(encoding=enc)
        self.assertIn("\xe9", content)

    # Test CST helpers
    def test_attr_to_dotted_name(self):
        node = cst.Name("foo")
        self.assertEqual(_attr_to_dotted(node), "foo")

    def test_attr_to_dotted_attribute(self):
        node = cst.Attribute(value=cst.Name("mod"), attr=cst.Name("sub"))
        self.assertEqual(_attr_to_dotted(node), "mod.sub")

    def test_attr_to_dotted_complex(self):
        node = cst.Attribute(
            value=cst.Attribute(value=cst.Name("a"), attr=cst.Name("b")),
            attr=cst.Name("c"),
        )
        self.assertEqual(_attr_to_dotted(node), "a.b.c")

    def test_attr_to_dotted_none(self):
        node = cst.SimpleString('"foo"')
        self.assertIsNone(_attr_to_dotted(node))

    def test_module_to_str(self):
        node = cst.Name("mod")
        self.assertEqual(_module_to_str(node), "mod")

    def test_module_to_str_relative(self):
        self.assertEqual(_module_to_str(None, 2), "..")

    def test_module_to_str_attribute(self):
        node = cst.Attribute(value=cst.Name("pkg"), attr=cst.Name("mod"))
        self.assertEqual(_module_to_str(node), "pkg.mod")

    def test_import_alias_name(self):
        alias = cst.ImportAlias(name=cst.Name("Symbol"))
        self.assertEqual(_import_alias_name(alias), "Symbol")

    def test_import_alias_name_dotted(self):
        alias = cst.ImportAlias(
            name=cst.Attribute(value=cst.Name("mod"), attr=cst.Name("Symbol"))
        )
        self.assertEqual(_import_alias_name(alias), "mod.Symbol")

    def test_str_to_expr(self):
        expr = _str_to_expr("pkg.mod")
        self.assertEqual(_attr_to_dotted(expr), "pkg.mod")

    # Test ImportReplacer
    def test_import_replacer_simple(self):
        code = "from old.mod import Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "from new.mod import Symbol")

    def test_import_replacer_alias(self):
        code = "from old.mod import Symbol as Alias"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "from new.mod import Symbol as Alias")

    def test_import_replacer_star(self):
        code = "from old.mod import *"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertIn("from new.mod import Symbol", new_code)
        self.assertIn("from old.mod import *", new_code)

    def test_import_replacer_multi(self):
        code = "from old.mod import A, Symbol, B"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertIn("from old.mod import A, B", new_code)
        self.assertIn("from new.mod import Symbol", new_code)

    def test_import_replacer_no_change(self):
        code = "from new.mod import Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), code)

    def test_import_replacer_relative_skip(self):
        code = "from .old_sub import Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old_sub", "new_sub", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), code)

    def test_import_replacer_relative_force(self):
        code = "from .old.mod import Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"], force_relative=True)
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "from new.mod import Symbol")

    def test_import_replacer_resolve_relative(self):
        code = "from ..old.mod import Symbol"
        file_path = Path("/fake/pkg/sub/file.py")
        replacer = ImportReplacer(
            "pkg.old.mod",
            "pkg.new.mod",
            ["Symbol"],
            force_relative=True,
            base_package="pkg",
            file_path=file_path,
        )
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "from pkg.new.mod import Symbol")

    def test_import_replacer_duplicate_avoid(self):
        code = "from new.mod import Symbol\nfrom old.mod import Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "from new.mod import Symbol")

    def test_import_replacer_empty_removal(self):
        code = "from old.mod import Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "from new.mod import Symbol")

    def test_import_replacer_no_change_dotted(self):
        code = "import old.mod\nold.mod.Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), code)

    def test_import_replacer_insert_position(self):
        code = '''"""Docstring"""
from __future__ import annotations
import os
from old.mod import Symbol'''
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        lines = new_code.splitlines()
        self.assertIn("from new.mod import Symbol", lines)
        self.assertEqual(
            lines.index("from new.mod import Symbol"), 3
        )  # After future and before os

    def test_import_replacer_multi_level_relative(self):
        code = "from ...old.mod import Symbol"
        file_path = Path("/fake/pkg/sub/dir/file.py")
        replacer = ImportReplacer(
            "pkg.old.mod",
            "pkg.new.mod",
            ["Symbol"],
            force_relative=True,
            base_package="pkg",
            file_path=file_path,
        )
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "from pkg.new.mod import Symbol")

    def test_import_replacer_with_comments(self):
        code = "# Comment above\nfrom old.mod import Symbol  # inline comment"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertIn("from new.mod import Symbol", new_code)
        self.assertIn("# Comment above", new_code)

    def test_import_replacer_multi_line(self):
        code = "from old.mod import (\n    A,\n    Symbol,\n    B,\n)"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertIn("from old.mod import (\n    A, B)", new_code)
        self.assertIn("from new.mod import Symbol", new_code)

    def test_import_replacer_no_body(self):
        code = ""
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code, "")

    def test_import_replacer_star_new_with_alias_old(self):
        code = """from new.mod import *
from old.mod import Symbol as Alias"""
        expected = """from new.mod import *
from new.mod import Symbol as Alias"""
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), expected.strip())

    def test_import_replacer_existing_alias_in_new(self):
        code = """from new.mod import Symbol as Alias
from old.mod import Symbol as Alias"""
        expected = """from new.mod import Symbol as Alias"""
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), expected.strip())

    def test_import_replacer_relative_too_deep(self):
        code = "from ....old.mod import Symbol"
        file_path = Path("/fake/pkg/sub/file.py")
        replacer = ImportReplacer(
            "pkg.old.mod",
            "pkg.new.mod",
            ["Symbol"],
            force_relative=True,
            base_package="pkg",
            file_path=file_path,
        )
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), code)

    def test_import_replacer_nested_in_function(self):
        code = """def f():
    from old.mod import Symbol"""
        expected = """from new.mod import Symbol
def f():
    pass"""
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), expected.strip())

    def test_import_replacer_conditional_import(self):
        code = """if cond:
    from old.mod import Symbol"""
        expected = """from new.mod import Symbol
if cond:
    pass"""
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), expected.strip())

    def test_import_replacer_in_try_except(self):
        code = """try:
    from old.mod import Symbol
except ImportError:
    pass"""
        expected = """from new.mod import Symbol
try:
    pass
except ImportError:
    pass"""
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), expected.strip())

    def test_import_replacer_relative_force_no_base_no_match(self):
        code = "from ..old.mod import Symbol"
        expected = code
        file_path = Path("/fake/pkg/sub/file.py")
        replacer = ImportReplacer(
            "pkg.old.mod",
            "pkg.new.mod",
            ["Symbol"],
            force_relative=True,
            base_package=None,
            file_path=file_path,
        )
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), expected)

    def test_import_replacer_multiple_symbols(self):
        code = "from old.mod import Sym1, Sym2"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Sym1", "Sym2"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "from new.mod import Sym1, Sym2")

    def test_import_replacer_multiple_symbols_mixed(self):
        code = "from old.mod import Sym1, Other, Sym2"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Sym1", "Sym2"])
        new_code = wrapper.visit(replacer).code
        self.assertIn("from old.mod import Other", new_code)
        self.assertIn("from new.mod import Sym1, Sym2", new_code)

    def test_import_replacer_multiple_symbols_aliases(self):
        code = "from old.mod import Sym1 as A, Sym2 as B"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Sym1", "Sym2"])
        new_code = wrapper.visit(replacer).code
        self.assertIn("from new.mod import Sym1 as A, Sym2 as B", new_code)

    def test_import_replacer_star_multiple_symbols(self):
        code = "from old.mod import *"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = ImportReplacer("old.mod", "new.mod", ["Sym1", "Sym2"])
        new_code = wrapper.visit(replacer).code
        self.assertIn("from old.mod import *", new_code)
        self.assertIn("from new.mod import Sym1, Sym2", new_code)

    # Test DottedReplacer
    def test_dotted_replacer_simple(self):
        code = "a = old.mod.Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = DottedReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "a = new.mod.Symbol")

    def test_dotted_replacer_multiple(self):
        code = "a = old.mod.Sym1\nb = old.mod.Sym2"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = DottedReplacer("old.mod", "new.mod", ["Sym1", "Sym2"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "a = new.mod.Sym1\nb = new.mod.Sym2")

    def test_dotted_replacer_no_match(self):
        code = "a = other.mod.Symbol"
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        replacer = DottedReplacer("old.mod", "new.mod", ["Symbol"])
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), code)

    def test_dotted_replacer_relative(self):
        code = "a = old.mod.Symbol"
        file_path = Path("/fake/pkg/sub/file.py")
        replacer = DottedReplacer(
            "pkg.old.mod",
            "pkg.new.mod",
            ["Symbol"],
            force_relative=True,
            base_package="pkg",
            file_path=file_path,
        )
        wrapper = md.MetadataWrapper(cst.parse_module(code))
        new_code = wrapper.visit(replacer).code
        self.assertEqual(new_code.strip(), "a = pkg.new.mod.Symbol")

    # Test check_remaining_usages updated
    def test_check_remaining_usages_multiple_symbols(self):
        content = "old.mod.Sym1 used\nold.mod.Sym2 here"
        warnings = check_remaining_usages(content, "old.mod", ["Sym1", "Sym2"])
        self.assertEqual(len(warnings), 2)
        self.assertIn("Sym1: 1", warnings[0])
        self.assertIn("Sym2: 1", warnings[1])

    # Test process_file updated
    def test_process_file_change(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from old.mod import Symbol\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        changed, msg, detail = process_file(file_path, migrations, dry_run=True)
        self.assertTrue(changed)
        self.assertIn("CHANGES IN", msg)
        self.assertIn("diff", detail)
        self.assertEqual(detail["risk_level"], "low")

    def test_process_file_no_change(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from new.mod import Symbol\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        changed, msg, detail = process_file(file_path, migrations, dry_run=True)
        self.assertFalse(changed)
        self.assertIn("UNCHANGED", msg)

    def test_process_file_apply_backup(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from old.mod import Symbol\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        changed, msg, detail = process_file(
            file_path, migrations, dry_run=False, no_backup=False
        )
        self.assertTrue(changed)
        self.assertIn("MODIFIED", msg)
        self.assertIn("backup", detail)
        self.assertEqual(file_path.read_text(), "from new.mod import Symbol\n")

    def test_process_file_star_warning(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from old.mod import *\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        changed, msg, detail = process_file(file_path, migrations, dry_run=True)
        self.assertTrue(changed)
        self.assertEqual(detail["risk_level"], "medium")
        self.assertIn("Handled wildcard import", detail["warnings"])

    def test_process_file_relative_skip(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from .old import Symbol\n")
        migrations = [{"old_module": "old", "new_module": "new", "symbols": ["Symbol"]}]
        changed, msg, detail = process_file(file_path, migrations, dry_run=True)
        self.assertFalse(changed)
        self.assertIn("SKIPPED (relative)", msg)
        self.assertEqual(detail["risk_level"], "high")

    def test_process_file_dotted_warning(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from old.mod import Symbol\nold.mod.Symbol\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        changed, msg, detail = process_file(file_path, migrations, dry_run=True)
        self.assertTrue(changed)
        self.assertEqual(detail["risk_level"], "high")
        self.assertIn(
            "Potential remaining dotted usages for Symbol: 1 instances",
            detail["warnings"],
        )

    def test_process_file_error(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("invalid syntax")
        migrations = [{"old_module": "old", "new_module": "new", "symbols": ["Symbol"]}]
        with patch("libcst.parse_module", side_effect=SyntaxError("invalid")):
            changed, msg, detail = process_file(file_path, migrations)
        self.assertFalse(changed)
        self.assertIn("ERROR", msg)
        self.assertIn("Error", detail["warnings"][0])

    def test_process_file_rewrite_dotted(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("a = old.mod.Symbol\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        changed, msg, detail = process_file(
            file_path, migrations, dry_run=False, rewrite_dotted=True
        )
        self.assertTrue(changed)
        self.assertIn("MODIFIED", msg)
        self.assertEqual(file_path.read_text(), "a = new.mod.Symbol\n")
        self.assertIn("Rewrote 1 dotted usages", detail["warnings"][0])
        self.assertEqual(detail["risk_level"], "medium")

    def test_process_file_multiple_migrations(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from mod1 import Sym1\nfrom mod2 import Sym2\n")
        migrations = [
            {"old_module": "mod1", "new_module": "new1", "symbols": ["Sym1"]},
            {"old_module": "mod2", "new_module": "new2", "symbols": ["Sym2"]},
        ]
        changed, msg, detail = process_file(file_path, migrations, dry_run=False)
        self.assertTrue(changed)
        content = file_path.read_text()
        self.assertIn("from new1 import Sym1", content)
        self.assertIn("from new2 import Sym2", content)

    def test_process_file_format(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from old.mod import Symbol\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        with patch("subprocess.run") as mock_run:
            changed, msg, detail = process_file(
                file_path, migrations, dry_run=False, do_format=True
            )
            self.assertTrue(changed)
            mock_run.assert_any_call(
                ["isort", "--quiet", "--atomic", str(file_path)],
                check=True,
                capture_output=True,
            )
            mock_run.assert_any_call(
                ["black", "--quiet", str(file_path)], check=True, capture_output=True
            )

    def test_process_file_format_fail(self):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from old.mod import Symbol\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        with patch("subprocess.run", side_effect=Exception("fail")):
            changed, msg, detail = process_file(
                file_path, migrations, dry_run=False, do_format=True
            )
            self.assertTrue(changed)
            self.assertIn("Formatting failed", detail["warnings"][0])

    # Test find_py_files (unchanged)
    def test_find_py_files_dir(self):
        (self.temp_path / "a.py").touch()
        (self.temp_path / "b.txt").touch()
        (self.temp_path / "sub").mkdir()
        (self.temp_path / "sub" / "c.py").touch()
        files = find_py_files(self.temp_path, [])
        self.assertEqual(len(files), 2)
        self.assertIn(self.temp_path / "a.py", files)
        self.assertIn(self.temp_path / "sub" / "c.py", files)

    def test_find_py_files_single_file(self):
        file_path = self.temp_path / "test.py"
        file_path.touch()
        files = find_py_files(file_path, [])
        self.assertEqual(files, [file_path])

    def test_find_py_files_excludes(self):
        (self.temp_path / "a.py").touch()
        (self.temp_path / "tests").mkdir(exist_ok=True)
        (self.temp_path / "tests" / "b.py").touch()
        files = find_py_files(self.temp_path, ["tests/*"])
        self.assertEqual(len(files), 1)
        self.assertIn(self.temp_path / "a.py", files)

    def test_find_py_files_max_files(self):
        for i in range(5):
            (self.temp_path / f"{i}.py").touch()
        files = find_py_files(self.temp_path, [], max_files=3)
        self.assertEqual(len(files), 3)

    # Test safety checks
    @patch("import_surgeon.cli.find_git_root", return_value=Path("/tmp"))
    @patch("subprocess.run")
    def test_git_is_clean(self, mock_run, mock_find):
        mock_run.return_value = MagicMock(stdout="")
        self.assertTrue(git_is_clean(self.temp_path))

    @patch("import_surgeon.cli.find_git_root", return_value=Path("/tmp"))
    @patch("subprocess.run")
    def test_git_is_clean_dirty(self, mock_run, mock_find):
        mock_run.return_value = MagicMock(stdout="M file.py")
        self.assertFalse(git_is_clean(self.temp_path))

    def test_find_git_root(self):
        git_dir = self.temp_path / ".git"
        git_dir.mkdir()
        self.assertEqual(find_git_root(self.temp_path), self.temp_path)

    def test_find_git_root_none(self):
        self.assertIsNone(find_git_root(self.temp_path))

    @patch("subprocess.run")
    def test_git_commit_changes_success(self, mock_run):
        mock_run.return_value = MagicMock()
        self.assertTrue(git_commit_changes(self.temp_path, "msg"))

    @patch("subprocess.run", side_effect=Exception("fail"))
    def test_git_commit_changes_fail(self, mock_run):
        with patch("logging.Logger.error") as mock_err:
            self.assertFalse(git_commit_changes(self.temp_path, "msg"))
            mock_err.assert_called()

    # Test CLI
    def test_parse_args(self):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym1,Sym2",
            ".",
        ]
        args = parse_args(argv)
        self.assertEqual(args.old_module, "old")
        self.assertEqual(args.new_module, "new")
        self.assertEqual(args.symbols, "Sym1,Sym2")
        self.assertEqual(args.target, ".")

    def test_main_missing_args(self):
        argv = ["."]
        with patch("logging.Logger.error") as mock_err:
            exit_code = main(argv)
            self.assertEqual(exit_code, 2)
            mock_err.assert_called()

    def test_main_target_not_found(self):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "/nonexistent",
        ]
        with patch("logging.Logger.error") as mock_err:
            exit_code = main(argv)
            self.assertEqual(exit_code, 2)
            mock_err.assert_called_with("Target not found: %s", Path("/nonexistent"))

    @patch("import_surgeon.cli.find_py_files", return_value=[])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(False, "UNCHANGED", {"warnings": []}),
    )
    @patch("builtins.print")
    def test_main_dry_run(self, mock_print, mock_process, mock_find):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            str(self.temp_path),
        ]
        exit_code = main(argv)
        self.assertEqual(exit_code, 0)

    @patch("import_surgeon.cli.find_py_files", return_value=[Path("test.py")])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(True, "MODIFIED", {"warnings": []}),
    )
    @patch("import_surgeon.cli.git_is_clean", return_value=True)
    @patch("import_surgeon.cli.git_commit_changes", return_value=True)
    @patch("builtins.print")
    def test_main_apply_auto_commit(
        self, mock_print, mock_commit, mock_clean, mock_process, mock_find
    ):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--apply",
            "--auto-commit",
            "msg",
            "--require-clean-git",
            str(self.temp_path),
        ]
        with patch(
            "import_surgeon.cli.find_git_root", return_value=self.temp_path
        ):
            exit_code = main(argv)
            self.assertEqual(exit_code, 0)
            mock_commit.assert_called()

    @patch("import_surgeon.cli.find_py_files", return_value=[Path("test.py")])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(False, "ERROR", {"warnings": []}),
    )
    @patch("builtins.print")
    def test_main_errors(self, mock_print, mock_process, mock_find):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            str(self.temp_path),
        ]
        exit_code = main(argv)
        self.assertEqual(exit_code, 1)

    @patch("import_surgeon.cli.find_py_files", return_value=[Path("test.py")])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(False, "SKIPPED", {"warnings": ["warn"]}),
    )
    @patch("builtins.print")
    def test_main_strict_warnings(self, mock_print, mock_process, mock_find):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--strict-warnings",
            str(self.temp_path),
        ]
        exit_code = main(argv)
        self.assertEqual(exit_code, 1)

    @patch("import_surgeon.cli.find_py_files", return_value=[Path("test.py")])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(True, "CHANGED", {"warnings": []}),
    )
    @patch("json.dump")
    def test_main_summary_json(self, mock_json, mock_process, mock_find):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--summary-json",
            "out.json",
            str(self.temp_path),
        ]
        exit_code = main(argv)
        self.assertEqual(exit_code, 0)
        mock_json.assert_called()

    @patch("import_surgeon.cli.git_is_clean", return_value=False)
    @patch("logging.Logger.error")
    def test_main_git_not_clean(self, mock_err, mock_clean):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--apply",
            "--require-clean-git",
            str(self.temp_path),
        ]
        with patch(
            "import_surgeon.cli.find_git_root", return_value=self.temp_path
        ):
            exit_code = main(argv)
            self.assertEqual(exit_code, 1)
            mock_err.assert_called_with(
                "Git not clean; commit/stash or remove --require-clean-git"
            )

    @patch("import_surgeon.cli.load_config", return_value={"old-module": "old"})
    def test_main_config_override(self, mock_load):
        argv = [
            "--config",
            "config.yaml",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            str(self.temp_path),
        ]
        args = parse_args(argv)
        config = import_surgeon.cli.load_config(args.config)
        for k, v in config.items():
            key = k.replace("-", "_")
            if not hasattr(args, key) or getattr(args, key) is None:
                setattr(args, key, v)
        self.assertEqual(args.old_module, "old")

    @patch(
        "import_surgeon.cli.load_config",
        return_value={"old-module": "old", "new-module": "newer"},
    )
    def test_main_config_override_selective(self, mock_load):
        argv = [
            "--config",
            "config.yaml",
            "--old-module",
            "myold",
            "--symbols",
            "Sym",
            str(self.temp_path),
        ]
        args = parse_args(argv)
        config = import_surgeon.cli.load_config(args.config)
        for k, v in config.items():
            key = k.replace("-", "_")
            if not hasattr(args, key) or getattr(args, key) is None:
                setattr(args, key, v)
        self.assertEqual(args.old_module, "myold")
        self.assertEqual(args.new_module, "newer")

    # New test: Quiet mode not printing
    @patch("builtins.print")
    def test_process_file_quiet(self, mock_print):
        file_path = self.temp_path / "test.py"
        file_path.write_text("from old.mod import Symbol\n")
        migrations = [
            {"old_module": "old.mod", "new_module": "new.mod", "symbols": ["Symbol"]}
        ]
        changed, msg, detail = process_file(
            file_path, migrations, dry_run=True, quiet="all"
        )
        mock_print.assert_not_called()

    # New test: Summary JSON content
    @patch("import_surgeon.cli.find_py_files", return_value=[Path("test.py")])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(True, "CHANGED", {"warnings": [], "risk_level": "low"}),
    )
    @patch("json.dump")
    @patch("builtins.open", mock_open())
    def test_main_summary_json_content(self, mock_json, mock_process, mock_find):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--summary-json",
            "out.json",
            str(self.temp_path),
        ]
        main(argv)
        mock_json.assert_called_once()
        args, _ = mock_json.call_args
        summary = args[0]
        self.assertIn("summary", summary)
        self.assertIn("timestamp", summary)
        self.assertEqual(len(summary["summary"]), 1)
        entry = summary["summary"][0]
        self.assertTrue(entry["changed"])
        self.assertEqual(entry["risk_level"], "low")

    # New test: Auto-commit failure
    @patch("import_surgeon.cli.find_py_files", return_value=[Path("test.py")])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(True, "MODIFIED", {"warnings": []}),
    )
    @patch("import_surgeon.cli.git_is_clean", return_value=True)
    @patch("import_surgeon.cli.git_commit_changes", return_value=False)
    @patch("builtins.print")
    @patch("logging.Logger.info")
    def test_main_auto_commit_failure(
        self, mock_info, mock_print, mock_commit, mock_clean, mock_process, mock_find
    ):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--apply",
            "--auto-commit",
            "msg",
            str(self.temp_path),
        ]
        with patch(
            "import_surgeon.cli.find_git_root", return_value=self.temp_path
        ):
            exit_code = main(argv)
            self.assertEqual(exit_code, 0)
            mock_commit.assert_called()
            calls = mock_info.call_args_list
            self.assertFalse(
                any(call[0][0].startswith("Auto-committed") for call in calls)
            )  # No success message

    # New test: Main with migrations in config
    @patch(
        "import_surgeon.cli.load_config",
        return_value={
            "migrations": [
                {"old_module": "old", "new_module": "new", "symbols": ["Sym"]}
            ]
        },
    )
    @patch("import_surgeon.cli.find_py_files", return_value=[])
    @patch("import_surgeon.cli.process_file")
    def test_main_with_migrations_config(self, mock_process, mock_find, mock_load):
        argv = ["--config", "config.yaml", str(self.temp_path)]
        exit_code = main(argv)
        self.assertEqual(exit_code, 0)

    # New test: Rollback success
    def test_main_rollback(self):
        summary_path = self.temp_path / "summary.json"
        file_path = self.temp_path / "test.py"
        backup_path = self.temp_path / "test.py.bak"
        file_path.write_text("modified")
        backup_path.write_text("original")
        summary_data = {
            "summary": [
                {"file": str(file_path), "changed": True, "backup": str(backup_path)}
            ]
        }
        with open(summary_path, "w") as f:
            json.dump(summary_data, f)
        argv = ["--rollback", "--summary-json", str(summary_path)]
        with patch("logging.Logger.info") as mock_info:
            exit_code = main(argv)
            self.assertEqual(exit_code, 0)
            self.assertEqual(file_path.read_text(), "original")
            self.assertFalse(backup_path.exists())

    # New test: Rollback missing backup
    def test_main_rollback_missing_backup(self):
        summary_path = self.temp_path / "summary.json"
        file_path = self.temp_path / "test.py"
        backup_path = self.temp_path / "missing.bak"
        summary_data = {
            "summary": [
                {"file": str(file_path), "changed": True, "backup": str(backup_path)}
            ]
        }
        with open(summary_path, "w") as f:
            json.dump(summary_data, f)
        argv = ["--rollback", "--summary-json", str(summary_path)]
        with patch("logging.Logger.warning") as mock_warn:
            exit_code = main(argv)
            self.assertEqual(exit_code, 0)
            mock_warn.assert_called_with("Backup missing for %s", file_path)

    # New test: Auto base_package detection
    @patch("import_surgeon.cli.find_py_files", return_value=[])
    @patch("import_surgeon.cli.process_file")
    @patch(
        "import_surgeon.cli.find_git_root", return_value=Path("/repo/myproject")
    )
    @patch("logging.Logger.info")
    def test_main_auto_base_package(
        self, mock_info, mock_root, mock_process, mock_find
    ):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            str(self.temp_path),
        ]
        exit_code = main(argv)
        self.assertEqual(exit_code, 0)
        mock_info.assert_any_call("Auto-detected base_package: %s", "myproject")

    # New test: Main with --rewrite-dotted
    @patch("import_surgeon.cli.find_py_files", return_value=[Path("test.py")])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(True, "MODIFIED", {"warnings": []}),
    )
    def test_main_rewrite_dotted(self, mock_process, mock_find):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--rewrite-dotted",
            str(self.temp_path),
        ]
        exit_code = main(argv)
        self.assertEqual(exit_code, 0)
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0]
        self.assertTrue(call_args[6])  # rewrite_dotted=True

    # New test: Main with --format
    @patch("import_surgeon.cli.find_py_files", return_value=[Path("test.py")])
    @patch(
        "import_surgeon.cli.process_file",
        return_value=(True, "MODIFIED", {"warnings": []}),
    )
    def test_main_format(self, mock_process, mock_find):
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--format",
            str(self.temp_path),
        ]
        exit_code = main(argv)
        self.assertEqual(exit_code, 0)
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0]
        self.assertTrue(call_args[7])  # do_format=True

    # New test: Rollback with non-UTF8 encoding
    def test_main_rollback_non_utf8(self):
        summary_path = self.temp_path / "summary.json"
        file_path = self.temp_path / "test.py"
        backup_path = self.temp_path / "test.py.bak"
        latin_content = b"# -*- coding: latin-1 -*-\nprint('\xe9')\n"
        file_path.write_bytes(latin_content + b"# modified")
        backup_path.write_bytes(latin_content)
        summary_data = {
            "summary": [
                {"file": str(file_path), "changed": True, "backup": str(backup_path)}
            ]
        }
        with open(summary_path, "w") as f:
            json.dump(summary_data, f)
        argv = ["--rollback", "--summary-json", str(summary_path)]
        exit_code = main(argv)
        self.assertEqual(exit_code, 0)
        enc = detect_encoding(file_path)
        self.assertIn(enc, ["latin-1", "iso-8859-1", "latin1"])
        self.assertEqual(file_path.read_bytes(), latin_content)
        self.assertFalse(backup_path.exists())

    # New test: Interrupted apply (partial failure during multi-file processing)
    @patch(
        "import_surgeon.cli.find_py_files",
        return_value=[Path("good.py"), Path("bad.py")],
    )
    @patch("import_surgeon.cli.process_file")
    @patch("builtins.print")
    def test_main_partial_failure(self, mock_print, mock_process, mock_find):
        mock_process.side_effect = [
            (True, "MODIFIED: good.py", {"warnings": []}),
            (False, "ERROR: bad.py: fail", {"warnings": ["Error: fail"]}),
        ]
        argv = [
            "--old-module",
            "old",
            "--new-module",
            "new",
            "--symbols",
            "Sym",
            "--apply",
            str(self.temp_path),
        ]
        exit_code = main(argv)
        self.assertEqual(exit_code, 1)  # Exits with error due to failure
        self.assertEqual(mock_process.call_count, 2)  # Processes all files


if __name__ == "__main__":
    unittest.main()
