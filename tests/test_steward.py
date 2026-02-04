"""Unit tests for Steward service (gamification & leaderboard)."""
import pytest
import sqlite3
from unittest.mock import patch
import sys
from pathlib import Path

# Import the Steward class
from steward import Steward


class TestStewardInitialization:
    """Test Steward database initialization."""

    def test_steward_init_with_custom_db_path(self, temp_db):
        """Test that Steward initializes with a custom database path."""
        steward = Steward(db_path=temp_db)
        assert steward.db_path == temp_db
        assert sqlite3.connect(temp_db)

    def test_steward_creates_users_table(self, temp_db):
        """Test that Steward creates the users table on initialization."""
        Steward(db_path=temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_steward_creates_call_sessions_table(self, temp_db):
        """Test that Steward creates the call_sessions table on initialization."""
        Steward(db_path=temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='call_sessions'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_users_table_has_correct_schema(self, temp_db):
        """Test that users table has expected columns."""
        Steward(db_path=temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

        expected_columns = {"user_id", "credits", "level", "xp", "total_time_wasted"}
        assert expected_columns.issubset(columns)
        conn.close()


class TestCreditCalculation:
    """Test credit calculation logic."""

    def test_calculate_credits_base_rate(self, temp_db):
        """Test base credit calculation (10 per minute)."""
        steward = Steward(db_path=temp_db)
        # 60 seconds = 1 minute = 10 credits
        credits = steward.calculate_credits(60)
        assert credits == 10

    def test_calculate_credits_multiple_minutes(self, temp_db):
        """Test credit calculation for multiple minutes."""
        steward = Steward(db_path=temp_db)
        # 300 seconds = 5 minutes = 50 credits
        credits = steward.calculate_credits(300)
        assert credits == 50

    def test_calculate_credits_auto_mode(self, temp_db):
        """Test credit calculation with auto mode (1x multiplier)."""
        steward = Steward(db_path=temp_db)
        credits = steward.calculate_credits(60, mode="auto")
        assert credits == 10

    def test_calculate_credits_handoff_mode(self, temp_db):
        """Test credit calculation with handoff mode (2x multiplier)."""
        steward = Steward(db_path=temp_db)
        credits = steward.calculate_credits(60, mode="handoff")
        assert credits == 20

    def test_calculate_credits_live_mode(self, temp_db):
        """Test credit calculation with live mode (5x multiplier)."""
        steward = Steward(db_path=temp_db)
        credits = steward.calculate_credits(60, mode="live")
        assert credits == 50

    def test_calculate_credits_unique_bonus(self, temp_db):
        """Test unique scam bonus (+2.0 multiplier = 3x total)."""
        steward = Steward(db_path=temp_db)
        credits = steward.calculate_credits(60, is_unique=True)
        # 10 * (1 + 2.0) = 30
        assert credits == 30

    def test_calculate_credits_ai_on_ai_bonus(self, temp_db):
        """Test AI-on-AI detection bonus (+1.5 multiplier = 2.5x total)."""
        steward = Steward(db_path=temp_db)
        credits = steward.calculate_credits(60, ai_on_ai=True)
        # 10 * (1 + 1.5) = 25
        assert credits == 25

    def test_calculate_credits_cloned_voice_bonus(self, temp_db):
        """Test cloned voice (Doppelgänger) bonus (2x multiplier)."""
        steward = Steward(db_path=temp_db)
        credits = steward.calculate_credits(60, is_cloned_voice=True)
        # 10 * 2 = 20
        assert credits == 20

    def test_calculate_credits_stacked_bonuses(self, temp_db):
        """Test that bonuses stack correctly."""
        steward = Steward(db_path=temp_db)
        # Base: 60 seconds = 10 credits
        # Mode: handoff (multiplier = 2)
        # Cloned: multiplier *= 2.0 (multiplier = 4)
        # Unique: multiplier += 2.0 (multiplier = 6)
        # = 10 * 6 = 60
        credits = steward.calculate_credits(60, is_unique=True, mode="handoff", is_cloned_voice=True)
        assert credits == 60

    def test_calculate_credits_partial_minute_truncates(self, temp_db):
        """Test that partial minutes are truncated (floor division)."""
        steward = Steward(db_path=temp_db)
        # 59 seconds = 0 minutes, so 0 credits
        credits = steward.calculate_credits(59)
        assert credits == 0

        # 119 seconds = 1 minute = 10 credits
        credits = steward.calculate_credits(119)
        assert credits == 10


class TestLogCall:
    """Test call logging functionality."""

    def test_log_call_creates_user_if_not_exists(self, temp_db):
        """Test that log_call creates a new user if they don't exist."""
        steward = Steward(db_path=temp_db)
        steward.log_call("new_user", "session_1", 60)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM users WHERE user_id = ?", ("new_user",))
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 10  # 60 seconds = 1 minute = 10 credits

    def test_log_call_accumulates_credits(self, temp_db):
        """Test that multiple calls accumulate credits."""
        steward = Steward(db_path=temp_db)
        steward.log_call("user1", "session_1", 60)
        steward.log_call("user1", "session_2", 60)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM users WHERE user_id = ?", ("user1",))
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 20

    def test_log_call_accumulates_xp(self, temp_db):
        """Test that XP accumulates correctly (1 XP per 10 seconds)."""
        steward = Steward(db_path=temp_db)
        steward.log_call("user1", "session_1", 100)  # 10 XP
        steward.log_call("user1", "session_2", 50)   # 5 XP

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT xp FROM users WHERE user_id = ?", ("user1",))
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 15

    def test_log_call_accumulates_total_time_wasted(self, temp_db):
        """Test that total_time_wasted accumulates."""
        steward = Steward(db_path=temp_db)
        steward.log_call("user1", "session_1", 100)
        steward.log_call("user1", "session_2", 50)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT total_time_wasted FROM users WHERE user_id = ?", ("user1",))
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 150

    def test_log_call_returns_credits_and_level(self, temp_db):
        """Test that log_call returns earned credits and new level."""
        steward = Steward(db_path=temp_db)
        credits, level = steward.log_call("user1", "session_1", 60)

        assert credits == 10
        assert level == 1  # First call, level still 1

    def test_log_call_creates_session_entry(self, temp_db):
        """Test that log_call creates a call_sessions entry."""
        steward = Steward(db_path=temp_db)
        steward.log_call("user1", "session_123", 100, scam_type="PCH_Scam")

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, session_id, duration_seconds, scam_type FROM call_sessions WHERE session_id = ?",
            ("session_123",)
        )
        result = cursor.fetchone()
        conn.close()

        assert result[0] == "user1"
        assert result[1] == "session_123"
        assert result[2] == 100
        assert result[3] == "PCH_Scam"

    def test_log_call_session_records_credits_earned(self, temp_db):
        """Test that call_sessions records the credits earned."""
        steward = Steward(db_path=temp_db)
        steward.log_call("user1", "session_1", 120, mode="live")  # 120 seconds = 2 minutes * 10 base = 20, * 5 (live) = 100

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT credits_earned FROM call_sessions WHERE session_id = ?",
            ("session_1",)
        )
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 100

    def test_log_call_calculates_level_correctly(self, temp_db):
        """Test that level is calculated as int((xp/100)**0.5) + 1."""
        steward = Steward(db_path=temp_db)
        # One call with 600 seconds = 60 XP -> level = int((60/100)**0.5) + 1 = 1
        steward.log_call("user1", "session_1", 600)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT level FROM users WHERE user_id = ?", ("user1",))
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 1


class TestLeaderboard:
    """Test leaderboard functionality."""

    def test_get_leaderboard_empty(self, temp_db):
        """Test get_leaderboard with no users."""
        steward = Steward(db_path=temp_db)
        leaderboard = steward.get_leaderboard()
        assert len(leaderboard) == 0

    def test_get_leaderboard_single_user(self, temp_db):
        """Test get_leaderboard with one user."""
        steward = Steward(db_path=temp_db)
        steward.log_call("user1", "session_1", 600)

        leaderboard = steward.get_leaderboard()
        assert len(leaderboard) == 1
        assert leaderboard[0][0] == "user1"  # user_id

    def test_get_leaderboard_sorted_by_time_wasted(self, temp_db):
        """Test that leaderboard is sorted by total_time_wasted (descending)."""
        steward = Steward(db_path=temp_db)
        steward.log_call("user_low", "session_1", 100)
        steward.log_call("user_high", "session_2", 500)
        steward.log_call("user_mid", "session_3", 300)

        leaderboard = steward.get_leaderboard()

        # Should be sorted by time_wasted descending
        assert leaderboard[0][0] == "user_high"   # 500 seconds
        assert leaderboard[1][0] == "user_mid"    # 300 seconds
        assert leaderboard[2][0] == "user_low"    # 100 seconds

    def test_get_leaderboard_limit(self, temp_db):
        """Test that get_leaderboard respects limit parameter."""
        steward = Steward(db_path=temp_db)
        for i in range(20):
            steward.log_call(f"user_{i}", f"session_{i}", (20 - i) * 100)

        leaderboard = steward.get_leaderboard(limit=5)
        assert len(leaderboard) == 5

    def test_get_leaderboard_default_limit(self, temp_db):
        """Test that get_leaderboard defaults to limit of 10."""
        steward = Steward(db_path=temp_db)
        for i in range(20):
            steward.log_call(f"user_{i}", f"session_{i}", (20 - i) * 100)

        leaderboard = steward.get_leaderboard()
        assert len(leaderboard) == 10

    def test_get_leaderboard_returns_correct_columns(self, temp_db):
        """Test that leaderboard returns user_id, level, credits, total_time_wasted."""
        steward = Steward(db_path=temp_db)
        steward.log_call("user1", "session_1", 600)

        leaderboard = steward.get_leaderboard()
        row = leaderboard[0]

        assert row[0] == "user1"  # user_id
        assert isinstance(row[1], int)  # level
        assert isinstance(row[2], int)  # credits
        assert isinstance(row[3], int)  # total_time_wasted
