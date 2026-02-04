"""Unit tests for Actor service (persona management and LLM interaction)."""
import pytest
from unittest.mock import patch, MagicMock, Mock
import sys
from pathlib import Path
import os

# Import the Actor class
from actor import Actor


class TestActorInitialization:
    """Test Actor initialization."""

    def test_actor_initializes_with_default_params(self, mock_personas_yaml, tmp_path):
        """Test that Actor initializes with default parameters."""
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = """personas:
  hazel:
    name: Hazel
    voice_id: hazel_original
    system_prompt: "You are Hazel, a helpful IRS representative."
"""
            with patch("os.path.dirname", return_value=str(tmp_path)):
                actor = Actor()
                assert actor.ollama_url == "http://ollama:11434"
                assert actor.model == "llama3"
                assert actor.current_persona == "hazel"

    def test_actor_initializes_with_custom_params(self, tmp_path):
        """Test that Actor initializes with custom parameters."""
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = """personas:
  hazel:
    name: Hazel
    system_prompt: test
"""
            actor = Actor(ollama_url="http://custom:9000", model="custom_model")
            assert actor.ollama_url == "http://custom:9000"
            assert actor.model == "custom_model"

    def test_actor_loads_personas(self, tmp_path):
        """Test that Actor loads personas from YAML file."""
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = """personas:
  hazel:
    name: Hazel
    system_prompt: "Hazel prompt"
  decoy:
    name: Decoy
    system_prompt: "Decoy prompt"
"""
            actor = Actor()
            assert "hazel" in actor.personas
            assert "decoy" in actor.personas
            assert actor.personas["hazel"]["name"] == "Hazel"


class TestPersonaManagement:
    """Test persona selection and management."""

    def test_set_persona_valid(self, tmp_path):
        """Test setting a valid persona."""
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = """personas:
  hazel:
    name: Hazel
    system_prompt: test
  decoy:
    name: Decoy
    system_prompt: test
"""
            actor = Actor()
            actor.set_persona("decoy")
            assert actor.current_persona == "decoy"

    def test_set_persona_invalid_ignores(self, tmp_path):
        """Test that invalid persona doesn't change current persona."""
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = """personas:
  hazel:
    name: Hazel
    system_prompt: test
"""
            actor = Actor()
            original_persona = actor.current_persona
            actor.set_persona("nonexistent")
            assert actor.current_persona == original_persona

    def test_set_persona_prints_confirmation(self, tmp_path, capsys):
        """Test that set_persona prints confirmation message."""
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = """personas:
  hazel:
    name: Hazel
    system_prompt: test
  decoy:
    name: Decoy
    system_prompt: test
"""
            actor = Actor()
            actor.set_persona("decoy")
            captured = capsys.readouterr()
            assert "Mask Swapped" in captured.out or "decoy" in captured.out.lower()


class TestAIDetectionAndResponse:
    """Test AI detection and response generation."""

    def test_generate_response_detects_ai(self, tmp_path):
        """Test that generate_response detects AI in transcript."""
        with patch("builtins.open", create=True):
            with patch("hallucination_engine.HallucinationEngine") as mock_he:
                mock_he_instance = MagicMock()
                mock_he_instance.detect_ai_artifacts.return_value = True
                mock_he_instance.generate_contradiction.return_value = "test contradiction"
                mock_he.return_value = mock_he_instance

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"response": "Test response"}
                    mock_post.return_value = mock_response

                    actor = Actor()
                    # Need to properly mock personas
                    actor.personas = {
                        "hazel": {"system_prompt": "You are Hazel"}
                    }

                    result = actor.generate_response(["Kindly verify your account"])
                    assert mock_he_instance.detect_ai_artifacts.called

    def test_generate_response_calls_ollama(self, tmp_path):
        """Test that generate_response calls Ollama API."""
        with patch("builtins.open", create=True):
            with patch("hallucination_engine.HallucinationEngine") as mock_he:
                mock_he_instance = MagicMock()
                mock_he_instance.detect_ai_artifacts.return_value = False
                mock_he.return_value = mock_he_instance

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"response": "Generated response"}
                    mock_post.return_value = mock_response

                    actor = Actor(ollama_url="http://test:11434", model="test_model")
                    actor.personas = {
                        "hazel": {"system_prompt": "You are Hazel"}
                    }

                    result = actor.generate_response(["test input"])

                    mock_post.assert_called_once()
                    call_args = mock_post.call_args
                    assert "http://test:11434/api/generate" in call_args[0][0]

    def test_generate_response_returns_model_output(self, tmp_path):
        """Test that generate_response returns the model output."""
        with patch("builtins.open", create=True):
            with patch("hallucination_engine.HallucinationEngine") as mock_he:
                mock_he_instance = MagicMock()
                mock_he_instance.detect_ai_artifacts.return_value = False
                mock_he.return_value = mock_he_instance

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    expected_response = "This is the AI's response"
                    mock_response.json.return_value = {"response": expected_response}
                    mock_post.return_value = mock_response

                    actor = Actor()
                    actor.personas = {
                        "hazel": {"system_prompt": "You are Hazel"}
                    }

                    result = actor.generate_response(["input"])
                    assert result == expected_response

    def test_generate_response_handles_api_error(self, tmp_path):
        """Test that generate_response handles Ollama API errors gracefully."""
        with patch("builtins.open", create=True):
            with patch("hallucination_engine.HallucinationEngine") as mock_he:
                mock_he_instance = MagicMock()
                mock_he_instance.detect_ai_artifacts.return_value = False
                mock_he.return_value = mock_he_instance

                with patch("requests.post") as mock_post:
                    mock_post.side_effect = Exception("Connection refused")

                    actor = Actor()
                    actor.personas = {
                        "hazel": {"system_prompt": "You are Hazel"}
                    }

                    result = actor.generate_response(["input"])
                    assert "Error" in result or "error" in result.lower()

    def test_generate_response_with_empty_history(self, tmp_path):
        """Test generate_response with empty transcript history."""
        with patch("builtins.open", create=True):
            with patch("hallucination_engine.HallucinationEngine") as mock_he:
                mock_he_instance = MagicMock()
                mock_he_instance.detect_ai_artifacts.return_value = False
                mock_he.return_value = mock_he_instance

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"response": "Hello"}
                    mock_post.return_value = mock_response

                    actor = Actor()
                    actor.personas = {
                        "hazel": {"system_prompt": "You are Hazel"}
                    }

                    result = actor.generate_response([])
                    assert result is not None


class TestPayloadConstruction:
    """Test payload construction for API calls."""

    def test_generate_response_constructs_correct_payload(self, tmp_path):
        """Test that payload is constructed correctly for Ollama API."""
        with patch("builtins.open", create=True):
            with patch("hallucination_engine.HallucinationEngine") as mock_he:
                mock_he_instance = MagicMock()
                mock_he_instance.detect_ai_artifacts.return_value = False
                mock_he.return_value = mock_he_instance

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"response": "test"}
                    mock_post.return_value = mock_response

                    actor = Actor(model="test_model")
                    actor.personas = {
                        "hazel": {"system_prompt": "Test prompt"}
                    }

                    actor.generate_response(["input1", "input2"])

                    call_json = mock_post.call_args[1]["json"]
                    assert call_json["model"] == "test_model"
                    assert call_json["stream"] is False
                    assert call_json["system"] == "Test prompt"
                    assert "input1" in call_json["prompt"]
                    assert "input2" in call_json["prompt"]

    def test_generate_response_uses_current_persona_prompt(self, tmp_path):
        """Test that correct persona's system prompt is used."""
        with patch("builtins.open", create=True):
            with patch("hallucination_engine.HallucinationEngine") as mock_he:
                mock_he_instance = MagicMock()
                mock_he_instance.detect_ai_artifacts.return_value = False
                mock_he.return_value = mock_he_instance

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"response": "test"}
                    mock_post.return_value = mock_response

                    actor = Actor()
                    actor.personas = {
                        "hazel": {"system_prompt": "Hazel prompt"},
                        "decoy": {"system_prompt": "Decoy prompt"}
                    }
                    actor.current_persona = "decoy"

                    actor.generate_response(["input"])

                    call_json = mock_post.call_args[1]["json"]
                    assert "Decoy prompt" in call_json["system"]


class TestAIEnhancedResponses:
    """Test enhanced responses when AI is detected."""

    def test_ai_detection_adds_instructions(self, tmp_path):
        """Test that AI detection adds hallucination instructions."""
        with patch("builtins.open", create=True):
            with patch("hallucination_engine.HallucinationEngine") as mock_he:
                mock_he_instance = MagicMock()
                mock_he_instance.detect_ai_artifacts.return_value = True
                mock_he_instance.generate_contradiction.return_value = "contradiction text"
                mock_he.return_value = mock_he_instance

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"response": "test"}
                    mock_post.return_value = mock_response

                    actor = Actor()
                    actor.personas = {
                        "hazel": {"system_prompt": "Base prompt"}
                    }

                    actor.generate_response(["Kindly verify"])

                    call_json = mock_post.call_args[1]["json"]
                    # Should have added hallucination note
                    assert "Hallucination" in call_json["system"] or "AI" in call_json["system"]
