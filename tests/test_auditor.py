"""Unit tests for Auditor service (v2.4 AEAD)."""
import pytest
import json
import hmac
import hashlib
import os
from unittest.mock import patch, mock_open, MagicMock

# Import the Auditor class
from auditor import Auditor


class TestAuditor:
    """Test suite for the Auditor service."""

    def test_auditor_initialization(self, temp_key_file):
        """Test that Auditor initializes correctly."""
        auditor = Auditor(key_path=temp_key_file)
        assert auditor.key_path == temp_key_file
        assert os.path.exists(temp_key_file)

    def test_ensure_key_creates_key_if_missing(self, tmp_path):
        """Test that _ensure_key creates a new key if it doesn't exist."""
        key_dir = tmp_path / "keys"
        key_path = key_dir / "test.key"

        auditor = Auditor(key_path=str(key_path))

        assert key_dir.exists()
        assert key_path.exists()
        assert key_path.stat().st_size == 32  # 256-bit key

    def test_sign_transaction_produces_consistent_signature(self, temp_key_file):
        """Test that signing the same payload produces the same signature."""
        auditor = Auditor(key_path=temp_key_file)
        payload = {"user_id": "test_user", "amount": 100}

        sig1 = auditor.sign_transaction(payload)
        sig2 = auditor.sign_transaction(payload)

        assert sig1 == sig2
        assert sig1.startswith("sig_v2.4_")

    def test_sign_transaction_different_payloads_different_signatures(self, temp_key_file):
        """Test that different payloads produce different signatures."""
        auditor = Auditor(key_path=temp_key_file)
        payload1 = {"user_id": "user1", "amount": 100}
        payload2 = {"user_id": "user2", "amount": 200}

        sig1 = auditor.sign_transaction(payload1)
        sig2 = auditor.sign_transaction(payload2)

        assert sig1 != sig2

    def test_sign_transaction_includes_all_fields(self, temp_key_file):
        """Test that signature includes all payload fields."""
        auditor = Auditor(key_path=temp_key_file)
        payload = {"id": 1, "name": "test", "value": 999}

        # Manually compute expected signature
        with open(temp_key_file, "rb") as f:
            key = f.read()
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        expected_sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()

        actual_sig = auditor.sign_transaction(payload)

        assert expected_sig in actual_sig

    def test_process_log_entry_creates_valid_entry(self, temp_key_file):
        """Test that process_log_entry creates a properly signed entry."""
        auditor = Auditor(key_path=temp_key_file)
        entry = auditor.process_log_entry("TEST_TYPE", "test content", "user123")

        assert entry["type"] == "TEST_TYPE"
        assert entry["content"] == "test content"
        assert entry["user_id"] == "user123"
        assert "signature" in entry
        assert "timestamp" in entry
        assert entry["signature"].startswith("sig_v2.4_")

    def test_process_log_entry_includes_timestamp(self, temp_key_file):
        """Test that log entries include timestamps."""
        import time
        auditor = Auditor(key_path=temp_key_file)
        before_time = time.time()
        entry = auditor.process_log_entry("EVENT", "content", "user")
        after_time = time.time()

        assert before_time <= entry["timestamp"] <= after_time

    def test_write_to_ledger_appends_entry(self, temp_key_file, temp_ledger):
        """Test that write_to_ledger appends entries to the ledger."""
        auditor = Auditor(key_path=temp_key_file)
        entry1 = auditor.process_log_entry("TYPE1", "content1", "user1")
        entry2 = auditor.process_log_entry("TYPE2", "content2", "user2")

        auditor.write_to_ledger(entry1, ledger_path=temp_ledger)
        auditor.write_to_ledger(entry2, ledger_path=temp_ledger)

        with open(temp_ledger, "r") as f:
            lines = f.readlines()

        assert len(lines) == 2
        line1_data = json.loads(lines[0])
        line2_data = json.loads(lines[1])
        assert line1_data["user_id"] == "user1"
        assert line2_data["user_id"] == "user2"

    def test_write_to_ledger_preserves_signature(self, temp_key_file, temp_ledger):
        """Test that ledger entries preserve their signatures."""
        auditor = Auditor(key_path=temp_key_file)
        entry = auditor.process_log_entry("CALL_FRAGMENT", "transcript", "user")

        auditor.write_to_ledger(entry, ledger_path=temp_ledger)

        with open(temp_ledger, "r") as f:
            saved_entry = json.loads(f.read())

        assert saved_entry["signature"] == entry["signature"]

    def test_detect_voice_theft_returns_false_by_default(self, temp_key_file):
        """Test that detect_voice_theft returns False when no signal detected."""
        auditor = Auditor(key_path=temp_key_file)
        result = auditor.detect_voice_theft({"recording_signal_detected": False})
        assert result is False

    def test_detect_voice_theft_returns_true_when_signal_detected(self, temp_key_file):
        """Test that detect_voice_theft returns True when signal detected."""
        auditor = Auditor(key_path=temp_key_file)
        result = auditor.detect_voice_theft({"recording_signal_detected": True})
        assert result is True

    def test_detect_voice_theft_handles_missing_key(self, temp_key_file):
        """Test that detect_voice_theft handles missing signal key gracefully."""
        auditor = Auditor(key_path=temp_key_file)
        result = auditor.detect_voice_theft({})
        assert result is False

    def test_trigger_voice_swap_returns_success(self, temp_key_file):
        """Test that trigger_voice_swap returns True."""
        auditor = Auditor(key_path=temp_key_file)
        result = auditor.trigger_voice_swap()
        assert result is True

    def test_trigger_voice_swap_handles_url_parameter(self, temp_key_file):
        """Test that trigger_voice_swap accepts custom actor URL."""
        auditor = Auditor(key_path=temp_key_file)
        result = auditor.trigger_voice_swap(actor_url="http://custom-actor:8000")
        assert result is True

    def test_signature_format_is_hex(self, temp_key_file):
        """Test that HMAC-SHA256 signature is valid hexadecimal."""
        auditor = Auditor(key_path=temp_key_file)
        payload = {"test": "data"}
        sig = auditor.sign_transaction(payload)

        # Extract hex part (after "sig_v2.4_")
        hex_part = sig.split("sig_v2.4_")[1]
        assert len(hex_part) == 64  # SHA256 produces 64 hex chars
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_payload_order_does_not_affect_signature(self, temp_key_file):
        """Test that JSON key ordering doesn't affect signature (sort_keys=True)."""
        auditor = Auditor(key_path=temp_key_file)
        payload1 = {"a": 1, "b": 2, "c": 3}
        payload2 = {"c": 3, "a": 1, "b": 2}

        sig1 = auditor.sign_transaction(payload1)
        sig2 = auditor.sign_transaction(payload2)

        assert sig1 == sig2
