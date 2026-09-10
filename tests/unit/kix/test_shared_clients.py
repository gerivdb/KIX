#!/usr/bin/env python3
r"""
Test Shared Clients (P1-T09)
Tests for KG_L_Client, WAZAA_Client, VaultWriter, BaseRunner, BaseSkill, SkillRunner
"""
import io
import sys
import time
import tempfile
from pathlib import Path

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add to path
_shared_path = str(Path(__file__).resolve().parent.parent.parent.parent / "kix" / "libs" / "shared-clients")
sys.path.insert(0, _shared_path)

# Use absolute import since path is set
from vault_writer import VaultWriter


def test_vault_writer_write_auto_index():
    """Test VaultWriter.write_auto_index()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = VaultWriter(vault_path=tmpdir)
        
        content = "# Test Index\n\nSome content here."
        path = writer.write_auto_index(content)
        
        assert path.exists(), "auto-index.md should exist"
        assert path.parent.name == "00-Index"
        assert "Test Index" in path.read_text(encoding="utf-8")


def test_vault_writer_compute_hash():
    """Test VaultWriter.compute_hash() consistency."""
    writer = VaultWriter(vault_path="/tmp/test_vault")
    
    content = "test content"
    h1 = writer.compute_hash(content)
    h2 = writer.compute_hash(content)
    
    assert h1 == h2, "Same content should produce same hash"
    assert len(h1) == 64, f"SHA256 should be 64 chars, got {len(h1)}"


def test_vault_writer_is_identical():
    """Test VaultWriter.is_identical()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = VaultWriter(vault_path=tmpdir)
        
        path = Path(tmpdir) / "test.md"
        path.write_text("original", encoding="utf-8")
        
        assert writer.is_identical(path, "original"), "Same content should be identical"
        assert not writer.is_identical(path, "different"), "Different content should not be identical"


def test_vault_writer_write_hub():
    """Test VaultWriter.write_hub()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = VaultWriter(vault_path=tmpdir)
        
        path = writer.write_hub("test-hub", "# Test Hub\n\nContent")
        assert path.exists()
        assert path.parent.name == "01-Hubs"


def test_vault_writer_dirs_created():
    """Test that VaultWriter creates required directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = VaultWriter(vault_path=tmpdir)
        
        for d in ["00-Index", "01-Hubs", "02-Concepts"]:
            assert (Path(tmpdir) / d).exists(), f"Directory {d} should exist"


if __name__ == "__main__":
    tests = [
        test_vault_writer_write_auto_index,
        test_vault_writer_compute_hash,
        test_vault_writer_is_identical,
        test_vault_writer_write_hub,
        test_vault_writer_dirs_created,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  [OK] {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [KO] {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
