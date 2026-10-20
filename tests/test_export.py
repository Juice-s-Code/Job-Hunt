"""Synthetic fixtures only: the exporter must never copy an enclosing vault."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import export_starter as exporter


class ExportTests(unittest.TestCase):
    def test_windows_path_handle_ctime_difference_is_not_a_mutation(self):
        import os
        from types import SimpleNamespace
        from unittest.mock import patch
        real_fstat = os.fstat

        def different_ctime(fd):
            info = real_fstat(fd)
            return SimpleNamespace(st_dev=info.st_dev, st_ino=info.st_ino,
                                   st_size=info.st_size, st_nlink=info.st_nlink,
                                   st_mtime_ns=info.st_mtime_ns, st_ctime_ns=info.st_ctime_ns + 123456)

        with patch.object(exporter.os, 'fstat', side_effect=different_ctime):
            self.assertEqual(exporter._source(self.root, 'README.md'), (self.root / 'README.md').read_bytes())

    def test_handle_mutation_still_refused(self):
        import os
        from types import SimpleNamespace
        from unittest.mock import patch
        real_fstat = os.fstat
        calls = []

        def changing_ctime(fd):
            info = real_fstat(fd)
            calls.append(True)
            return SimpleNamespace(st_dev=info.st_dev, st_ino=info.st_ino,
                                   st_size=info.st_size, st_nlink=info.st_nlink,
                                   st_mtime_ns=info.st_mtime_ns, st_ctime_ns=info.st_ctime_ns + len(calls))

        with patch.object(exporter.os, 'fstat', side_effect=changing_ctime):
            with self.assertRaises(exporter.ExportError):
                exporter._source(self.root, 'README.md')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "framework"
        self.root.mkdir()
        for rel in exporter.FILES:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("Synthetic safe fixture\n", encoding="utf-8")
        self.out = self.base / "starter.zip"

    def test_only_allowlisted_files_and_integrity_manifest(self):
        (self.root / ".env").write_text("DO_NOT_EXPORT_THIS_SENTINEL", encoding="utf-8")
        (self.base / "private-resume.txt").write_text("DO_NOT_EXPORT_THIS_SENTINEL", encoding="utf-8")
        (self.root / "personal.json").write_text("DO_NOT_EXPORT_THIS_SENTINEL", encoding="utf-8")
        result = exporter.export(self.root, self.out)
        with zipfile.ZipFile(self.out) as z:
            names = z.namelist()
            expected = {"job-hunt-starter/" + x for x in exporter.FILES}
            expected.add("job-hunt-starter/BUNDLE-MANIFEST.json")
            self.assertEqual(set(names), expected)
            self.assertEqual(len(names), len(expected))
            for n in names:
                self.assertNotIn(b"DO_NOT_EXPORT_THIS_SENTINEL", z.read(n))
            manifest = json.loads(z.read("job-hunt-starter/BUNDLE-MANIFEST.json"))
            self.assertEqual(set(manifest["sha256"]), set(exporter.FILES))
        self.assertEqual(result["file_count"], len(expected))

    def test_missing_file_fails_without_output(self):
        (self.root / exporter.FILES[0]).unlink()
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_existing_destination_never_overwritten(self):
        self.out.write_bytes(b"KEEP EXISTING")
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.root, self.out)
        self.assertEqual(self.out.read_bytes(), b"KEEP EXISTING")

    def test_secret_pattern_fails_without_output(self):
        (self.root / exporter.FILES[0]).write_text("-----BEGIN PRIVATE KEY-----", encoding="utf-8")
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_crlf_private_key_header_refused(self):
        # Synthetic marker only, not an actual key.
        (self.root / "README.md").write_bytes(b"-----BEGIN PRIVATE KEY-----\r\n")
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_symlink_not_followed(self):
        p = self.root / exporter.FILES[0]
        p.unlink()
        target = self.base / "private.txt"
        target.write_text("PRIVATE SYNTHETIC FIXTURE", encoding="utf-8")
        try:
            p.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Host cannot create test symlinks")
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.root, self.out)
        self.assertFalse(self.out.exists())

    @unittest.skipUnless(sys.platform == "win32", "Windows reparse-point test")
    def test_windows_junction_not_followed(self):
        import subprocess
        import shutil
        junction = self.root / "docs"
        shutil.rmtree(junction)
        target = self.base / "private-docs"
        target.mkdir()
        (target / "SCHEMA.md").write_text("PRIVATE SYNTHETIC FIXTURE", encoding="utf-8")
        result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(target)], capture_output=True, text=True)
        if result.returncode:
            self.skipTest("Host refused creation of test junction")
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_hardlinked_allowlisted_file_refused(self):
        import os
        outside = self.base / "private-synthetic.txt"
        outside.write_text("SYNTHETIC PRIVATE SENTINEL", encoding="utf-8")
        source = self.root / "README.md"
        source.unlink()
        os.link(outside, source)
        self.assertGreater(source.stat().st_nlink, 1)
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.root, self.out)
        self.assertFalse(self.out.exists())
        self.assertEqual(outside.read_text(encoding="utf-8"), "SYNTHETIC PRIVATE SENTINEL")

    def test_directory_substitution_at_source_open_refused(self):
        import io
        import os
        import subprocess
        from unittest import mock
        outside = self.base / "synthetic-outside-docs"
        outside.mkdir()
        (outside / "SCHEMA.md").write_text("SYNTHETIC OUTSIDE ROOT SENTINEL", encoding="utf-8")
        folder = self.root / "docs"
        saved = self.root / "docs-safe"
        victim = folder / "SCHEMA.md"
        real_open = io.open
        changed = []

        def substitute_before_open(file, mode="r", *args, **kwargs):
            if str(file) == str(victim) and mode == "rb" and not changed:
                changed.append(True)
                folder.rename(saved)
                try:
                    if os.name == "nt":
                        result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(folder), str(outside)], capture_output=True, text=True)
                        if result.returncode:
                            self.skipTest("Host refused synthetic junction")
                    else:
                        folder.symlink_to(outside, target_is_directory=True)
                    handle = real_open(file, mode, *args, **kwargs)
                finally:
                    if folder.is_symlink():
                        folder.unlink()
                    elif folder.exists():
                        folder.rmdir()
                    saved.rename(folder)
                return handle
            return real_open(file, mode, *args, **kwargs)

        with mock.patch("io.open", side_effect=substitute_before_open):
            with self.assertRaises(exporter.ExportError):
                exporter.export(self.root, self.out)
        self.assertEqual(changed, [True], "Substitution must reach the actual source-open seam")
        self.assertFalse(self.out.exists())

    def test_modified_manifest_during_readback_refused(self):
        import io
        from unittest import mock
        real_open = io.open
        changed = []

        def tamper_before_read(file, mode="r", *args, **kwargs):
            if str(file) == str(self.out) and mode == "rb" and not changed:
                changed.append(True)
                with real_open(self.out, "rb") as current:
                    before = current.read()
                replacement = io.BytesIO()
                with zipfile.ZipFile(io.BytesIO(before)) as source, zipfile.ZipFile(replacement, "w") as target:
                    for info in source.infolist():
                        data = source.read(info.filename)
                        if info.filename == exporter.PREFIX + "BUNDLE-MANIFEST.json":
                            manifest = json.loads(data)
                            manifest["sha256"]["README.md"] = "0" * 64
                            data = json.dumps(manifest).encode("utf-8")
                        target.writestr(info, data)
                with real_open(self.out, "wb") as current:
                    current.write(replacement.getvalue())
            return real_open(file, mode, *args, **kwargs)

        with mock.patch("io.open", side_effect=tamper_before_read):
            with self.assertRaises(exporter.ExportError):
                exporter.export(self.root, self.out)
        self.assertEqual(changed, [True], "Injection must exercise the real readback seam")

    def test_reproducible_archive(self):
        other = self.base / "other.zip"
        exporter.export(self.root, self.out)
        exporter.export(self.root, other)
        self.assertEqual(self.out.read_bytes(), other.read_bytes())

    def test_output_cannot_be_a_source_file(self):
        source = self.root / exporter.FILES[0]
        before = source.read_bytes()
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.root, source)
        self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
