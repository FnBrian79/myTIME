"""Unit tests for GhostBuffer service (transcript capture and handover)."""
import pytest
from unittest.mock import patch, MagicMock
import time

# Import the GhostBuffer class
from ghost_buffer import GhostBuffer


class TestGhostBufferInitialization:
    """Test GhostBuffer initialization."""

    def test_ghost_buffer_initializes(self):
        """Test that GhostBuffer initializes correctly."""
        gb = GhostBuffer()
        assert gb.ollama_url == "http://ollama:11434"
        assert gb.buffer == []
        assert gb.is_active is False

    def test_ghost_buffer_custom_ollama_url(self):
        """Test that GhostBuffer accepts custom Ollama URL."""
        gb = GhostBuffer(ollama_url="http://custom:9000")
        assert gb.ollama_url == "http://custom:9000"


class TestTranscriptCapture:
    """Test transcript capture functionality."""

    def test_capture_transcript_adds_to_buffer(self):
        """Test that capture_transcript adds entries to buffer."""
        gb = GhostBuffer()
        gb.capture_transcript("Hello, this is a test")
        assert len(gb.buffer) == 1

    def test_capture_transcript_includes_speaker(self):
        """Test that transcript captures speaker name."""
        gb = GhostBuffer()
        gb.capture_transcript("Hello", speaker="Scammer")
        assert "Scammer" in gb.buffer[0]

    def test_capture_transcript_default_speaker(self):
        """Test that default speaker is 'Scammer'."""
        gb = GhostBuffer()
        gb.capture_transcript("Hello")
        assert "Scammer" in gb.buffer[0]

    def test_capture_transcript_custom_speaker(self):
        """Test that custom speaker is recorded."""
        gb = GhostBuffer()
        gb.capture_transcript("Yes, I understand", speaker="User")
        assert "User" in gb.buffer[0]

    def test_capture_transcript_includes_timestamp(self):
        """Test that captured transcript includes timestamp."""
        gb = GhostBuffer()
        gb.capture_transcript("Test message")
        entry = gb.buffer[0]
        # Check for timestamp pattern HH:MM:SS
        assert "[" in entry and "]" in entry

    def test_capture_transcript_multiple_entries(self):
        """Test capturing multiple transcript entries."""
        gb = GhostBuffer()
        gb.capture_transcript("First message")
        gb.capture_transcript("Second message", speaker="User")
        gb.capture_transcript("Third message")
        assert len(gb.buffer) == 3

    def test_capture_transcript_preserves_order(self):
        """Test that captured transcripts maintain order."""
        gb = GhostBuffer()
        gb.capture_transcript("First")
        gb.capture_transcript("Second")
        gb.capture_transcript("Third")

        assert "First" in gb.buffer[0]
        assert "Second" in gb.buffer[1]
        assert "Third" in gb.buffer[2]


class TestContextGeneration:
    """Test context generation for handover."""

    def test_get_context_empty_buffer(self):
        """Test get_context with empty buffer."""
        gb = GhostBuffer()
        context = gb.get_context()
        assert context == ""

    def test_get_context_single_entry(self):
        """Test get_context with single entry."""
        gb = GhostBuffer()
        gb.capture_transcript("Hello")
        context = gb.get_context()
        assert "Hello" in context
        assert "Scammer" in context

    def test_get_context_multiple_entries(self):
        """Test get_context joins all entries."""
        gb = GhostBuffer()
        gb.capture_transcript("First")
        gb.capture_transcript("Second", speaker="User")
        context = gb.get_context()

        assert "First" in context
        assert "Second" in context
        assert "\n" in context  # Should be joined with newlines

    def test_get_context_preserves_speakers(self):
        """Test that get_context preserves speaker labels."""
        gb = GhostBuffer()
        gb.capture_transcript("Scammer message", speaker="Scammer")
        gb.capture_transcript("User message", speaker="User")
        context = gb.get_context()

        assert "Scammer:" in context
        assert "User:" in context


class TestHandover:
    """Test persona handover functionality."""

    def test_trigger_handover_returns_prompt(self):
        """Test that trigger_handover returns a prompt."""
        gb = GhostBuffer()
        gb.capture_transcript("Initial message")

        persona_prompt = "You are a helpful assistant"
        result = gb.trigger_handover(persona_prompt)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_trigger_handover_includes_persona_prompt(self):
        """Test that handover includes the persona prompt."""
        gb = GhostBuffer()
        persona_prompt = "You are Hazel, a 75-year-old grandmother"
        result = gb.trigger_handover(persona_prompt)

        assert persona_prompt in result

    def test_trigger_handover_includes_conversation_history(self):
        """Test that handover includes conversation history."""
        gb = GhostBuffer()
        gb.capture_transcript("Hello, this is Steve from Microsoft")
        gb.capture_transcript("Yes, I see a virus", speaker="User")

        result = gb.trigger_handover("You are Hazel")

        assert "Hello, this is Steve from Microsoft" in result
        assert "Yes, I see a virus" in result

    def test_trigger_handover_includes_handover_instruction(self):
        """Test that handover includes the handover instruction."""
        gb = GhostBuffer()
        result = gb.trigger_handover("Test persona")

        assert "handed over" in result.lower() or "continue" in result.lower()

    def test_trigger_handover_with_empty_buffer(self):
        """Test handover with empty transcript buffer."""
        gb = GhostBuffer()
        result = gb.trigger_handover("You are a test persona")

        assert result is not None
        assert "You are a test persona" in result

    def test_trigger_handover_prompt_structure(self):
        """Test that handover prompt has proper structure."""
        gb = GhostBuffer()
        gb.capture_transcript("Test message")

        result = gb.trigger_handover("Test persona")

        # Should include System, Conversation History, and instruction sections
        assert "System:" in result
        assert "Conversation History:" in result or "Recent" in result
        assert "Character" in result or "continue" in result.lower()


class TestIntegration:
    """Integration tests for GhostBuffer."""

    def test_realistic_call_flow(self):
        """Test realistic call flow from start to handover."""
        gb = GhostBuffer()

        # Simulate a scam call
        gb.capture_transcript("Hello, this is Steve from Microsoft Windows calling about your computer virus.")
        gb.capture_transcript("Yes, I'm looking at my screen now. It's very slow!", speaker="User")
        gb.capture_transcript("Okay, I need you to go to www.scam-website.com and download the support tool.")

        # Get context
        context = gb.get_context()
        assert len(context) > 0

        # Trigger handover
        hazel_persona = "You are Hazel, a 75-year-old grandmother"
        prompt = gb.trigger_handover(hazel_persona)

        assert len(prompt) > 0
        assert "Hazel" in prompt
        assert "Microsoft" in prompt

    def test_transcript_capture_and_context_consistency(self):
        """Test that captured transcripts match context."""
        gb = GhostBuffer()
        messages = [
            "Message 1",
            "Message 2",
            "Message 3"
        ]

        for msg in messages:
            gb.capture_transcript(msg)

        context = gb.get_context()
        for msg in messages:
            assert msg in context

    def test_multiple_handover_calls(self):
        """Test that multiple handovers work correctly."""
        gb = GhostBuffer()
        gb.capture_transcript("Initial message")

        prompt1 = gb.trigger_handover("Persona 1")
        prompt2 = gb.trigger_handover("Persona 2")

        assert "Persona 1" in prompt1
        assert "Persona 2" in prompt2
        assert prompt1 != prompt2  # Different personas should produce different prompts

    def test_buffer_state_across_operations(self):
        """Test that buffer state is maintained across operations."""
        gb = GhostBuffer()

        gb.capture_transcript("Message 1")
        assert len(gb.buffer) == 1

        context1 = gb.get_context()
        assert "Message 1" in context1

        gb.capture_transcript("Message 2")
        assert len(gb.buffer) == 2

        context2 = gb.get_context()
        assert "Message 1" in context2
        assert "Message 2" in context2
