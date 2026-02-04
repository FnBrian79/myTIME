"""Unit tests for HallucinationEngine (AI detection and counter-measures)."""
import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Import the HallucinationEngine class
from hallucination_engine import HallucinationEngine


class TestHallucinationEngineInitialization:
    """Test HallucinationEngine initialization."""

    def test_engine_initializes_with_contradictions(self):
        """Test that engine initializes with contradiction phrases."""
        engine = HallucinationEngine()
        assert len(engine.contradictions) > 0
        assert all(isinstance(c, str) for c in engine.contradictions)

    def test_engine_initializes_with_logic_bombs(self):
        """Test that engine initializes with logic bomb phrases."""
        engine = HallucinationEngine()
        assert len(engine.logic_bombs) > 0
        assert all(isinstance(b, str) for b in engine.logic_bombs)


class TestAIDetection:
    """Test AI artifact detection."""

    def test_detect_ai_artifacts_clean_text(self):
        """Test that normal human text doesn't trigger AI detection."""
        engine = HallucinationEngine()
        result = engine.detect_ai_artifacts("Hey, can you tell me my bank password?")
        assert result is False

    def test_detect_ai_artifacts_detects_kindly_alone(self):
        """Test that word 'kindly' alone doesn't exceed threshold (0.3 < 0.4)."""
        engine = HallucinationEngine()
        result = engine.detect_ai_artifacts("Kindly provide your credit card information.")
        # "kindly" = 0.3, which is not > 0.4
        assert result is False

    def test_detect_ai_artifacts_detects_long_monologue_alone(self):
        """Test that long monologues alone don't trigger AI detection (0.2 < 0.4)."""
        engine = HallucinationEngine()
        long_text = "A" * 101  # 101 characters = 0.2, which is not > 0.4
        result = engine.detect_ai_artifacts(long_text)
        assert result is False

    def test_detect_ai_artifacts_case_insensitive_with_length(self):
        """Test that 'kindly' + long text detection is case-insensitive."""
        engine = HallucinationEngine()
        # Need both triggers to exceed threshold: 0.3 + 0.2 = 0.5 > 0.4
        result_lower = engine.detect_ai_artifacts("kindly " + "A" * 100)
        result_upper = engine.detect_ai_artifacts("KINDLY " + "A" * 100)
        result_mixed = engine.detect_ai_artifacts("Kindly " + "A" * 100)

        assert result_lower is True
        assert result_upper is True
        assert result_mixed is True

    def test_detect_ai_artifacts_combined_triggers(self):
        """Test that multiple AI triggers combine to exceed threshold."""
        engine = HallucinationEngine()
        # "Kindly" (0.3) + long text >100 chars (0.2) = 0.5 > 0.4 threshold
        text = "Kindly " + "A" * 100
        result = engine.detect_ai_artifacts(text)
        assert result is True

    def test_detect_ai_artifacts_threshold_boundary(self):
        """Test behavior at the 0.4 threshold boundary."""
        engine = HallucinationEngine()
        # Exactly at threshold from one trigger shouldn't be enough
        result_just_below = engine.detect_ai_artifacts("A" * 50)  # ~0.2 score
        assert result_just_below is False


class TestContradictionGeneration:
    """Test contradiction phrase generation."""

    def test_generate_contradiction_returns_string(self):
        """Test that generate_contradiction returns a string."""
        engine = HallucinationEngine()
        contradiction = engine.generate_contradiction()
        assert isinstance(contradiction, str)
        assert len(contradiction) > 0

    def test_generate_contradiction_is_from_list(self):
        """Test that generated contradiction is from the predefined list."""
        engine = HallucinationEngine()
        contradiction = engine.generate_contradiction()
        assert contradiction in engine.contradictions

    def test_generate_contradiction_produces_variety(self):
        """Test that multiple calls can produce different contradictions."""
        engine = HallucinationEngine()
        contradictions = {engine.generate_contradiction() for _ in range(100)}
        # Should have generated at least 2 different contradictions in 100 tries
        # (extremely unlikely to get same one 100 times)
        assert len(contradictions) > 1

    def test_generate_contradiction_contains_confusing_logic(self):
        """Test that contradictions contain confusing or contradictory statements."""
        engine = HallucinationEngine()
        contradiction = engine.generate_contradiction()
        # Check for markers of confusion
        confusion_markers = ["but", "wait", "actually", "does", "why", "which", "?"]
        assert any(marker in contradiction.lower() for marker in confusion_markers)


class TestLogicBombGeneration:
    """Test logic bomb generation."""

    def test_trigger_logic_bomb_returns_string(self):
        """Test that trigger_logic_bomb returns a string."""
        engine = HallucinationEngine()
        logic_bomb = engine.trigger_logic_bomb()
        assert isinstance(logic_bomb, str)
        assert len(logic_bomb) > 0

    def test_trigger_logic_bomb_is_from_list(self):
        """Test that logic bomb is from the predefined list."""
        engine = HallucinationEngine()
        logic_bomb = engine.trigger_logic_bomb()
        assert logic_bomb in engine.logic_bombs

    def test_trigger_logic_bomb_produces_variety(self):
        """Test that multiple calls can produce different logic bombs."""
        engine = HallucinationEngine()
        logic_bombs = {engine.trigger_logic_bomb() for _ in range(100)}
        # Should have generated at least 2 different logic bombs in 100 tries
        assert len(logic_bombs) > 1

    def test_trigger_logic_bomb_contains_questions(self):
        """Test that logic bombs contain questions or logical contradictions."""
        engine = HallucinationEngine()
        logic_bomb = engine.trigger_logic_bomb()
        # Logic bombs should contain question marks or logical challenges
        assert "?" in logic_bomb or "why" in logic_bomb.lower()


class TestIntegration:
    """Integration tests for HallucinationEngine."""

    def test_ai_detection_and_counter_response(self):
        """Test realistic scenario: detect AI and generate counter."""
        engine = HallucinationEngine()

        # Simulate AI scammer speech with both triggers: "kindly" + long monologue
        scammer_text = "Kindly navigate to the website and verify your credentials for security purposes. " + "A" * 100

        # Detect AI (needs both triggers to exceed 0.4 threshold)
        is_ai = engine.detect_ai_artifacts(scammer_text)
        assert is_ai is True

        # Generate counter-measures
        contradiction = engine.generate_contradiction()
        logic_bomb = engine.trigger_logic_bomb()

        assert len(contradiction) > 0
        assert len(logic_bomb) > 0

    def test_multiple_detection_cycles(self):
        """Test multiple detection cycles don't cause issues."""
        engine = HallucinationEngine()
        # Use both triggers to exceed threshold
        test_text = "Kindly provide your information " + "A" * 100
        for _ in range(10):
            result = engine.detect_ai_artifacts(test_text)
            assert result is True
            contradiction = engine.generate_contradiction()
            assert contradiction is not None
