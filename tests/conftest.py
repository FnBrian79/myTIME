import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add services directory to Python path for imports
services_path = Path(__file__).parent.parent / "services"
sys.path.insert(0, str(services_path))
sys.path.insert(0, str(services_path / "auditor"))
sys.path.insert(0, str(services_path / "actor"))
sys.path.insert(0, str(services_path / "steward"))
sys.path.insert(0, str(services_path / "architect"))
sys.path.insert(0, str(services_path / "foreman"))


@pytest.fixture
def temp_db():
    """Provides a temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_key_file():
    """Provides a temporary key file for Auditor testing."""
    fd, path = tempfile.mkstemp(suffix=".key")
    os.close(fd)
    # Write a test key
    with open(path, "wb") as f:
        f.write(b"test_key_32_bytes_long1234567890")
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_ledger():
    """Provides a temporary ledger file for Auditor testing."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def mock_personas_yaml(tmp_path):
    """Provides a mock personas.yaml file for Actor testing."""
    personas_content = """personas:
  hazel:
    name: Hazel
    voice_id: hazel_original
    system_prompt: "You are Hazel, a helpful IRS representative."
  decoy:
    name: Decoy
    voice_id: decoy_voice
    system_prompt: "You are a decoy persona."
"""
    personas_file = tmp_path / "personas.yaml"
    personas_file.write_text(personas_content)
    return str(personas_file)
