"""Unit tests for DeepfakeDetector (Architect service)."""
import pytest
from unittest.mock import patch, MagicMock, Mock
import numpy as np

# Mock torch and transformers before importing architect_stream
@pytest.fixture(autouse=True)
def mock_torch_imports():
    """Mock torch and transformers imports for testing."""
    mock_torch = MagicMock()
    mock_torchaudio = MagicMock()
    mock_transformers = MagicMock()

    with patch.dict('sys.modules', {
        'torch': mock_torch,
        'torchaudio': mock_torchaudio,
        'transformers': mock_transformers,
    }):
        yield


@pytest.fixture
def mock_model_and_processor():
    """Provide mock model and processor."""
    mock_processor = MagicMock()
    mock_model = MagicMock()

    # Mock processor output
    mock_processor.return_value = {
        'input_values': MagicMock()
    }

    # Mock model output (logits)
    mock_logits = MagicMock()
    mock_logits.argmax.return_value.item.return_value = 0
    mock_model.return_value.logits = mock_logits

    return mock_model, mock_processor


class TestDeepfakeDetectorInitialization:
    """Test DeepfakeDetector initialization."""

    @patch('torch.device')
    @patch('transformers.Wav2Vec2Processor.from_pretrained')
    @patch('transformers.Wav2Vec2ForSequenceClassification.from_pretrained')
    def test_detector_initializes_with_defaults(
        self, mock_model_class, mock_processor_class, mock_device
    ):
        """Test that DeepfakeDetector initializes with default model path."""
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_model_class.return_value = mock_model_instance
        mock_processor_class.return_value = mock_processor_instance
        mock_device.return_value = MagicMock()

        with patch('builtins.open', create=True):
            with patch('torch.device'):
                # Import after mocking
                from architect_stream import DeepfakeDetector

                detector = DeepfakeDetector()

                assert detector.processor is not None
                assert detector.model is not None

    @patch('torch.device')
    @patch('transformers.Wav2Vec2Processor.from_pretrained')
    @patch('transformers.Wav2Vec2ForSequenceClassification.from_pretrained')
    def test_detector_initializes_with_custom_paths(
        self, mock_model_class, mock_processor_class, mock_device
    ):
        """Test that DeepfakeDetector accepts custom model paths."""
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_model_class.return_value = mock_model_instance
        mock_processor_class.return_value = mock_processor_instance

        with patch('builtins.open', create=True):
            with patch('torch.device'):
                from architect_stream import DeepfakeDetector

                custom_path = "custom/model/path"
                detector = DeepfakeDetector(
                    model_path=custom_path,
                    processor_path=custom_path
                )

                assert detector.model is not None
                mock_model_class.assert_called_once()
                mock_processor_class.assert_called_once()

    @patch('torch.device')
    @patch('transformers.Wav2Vec2Processor.from_pretrained')
    @patch('transformers.Wav2Vec2ForSequenceClassification.from_pretrained')
    def test_detector_sets_eval_mode(
        self, mock_model_class, mock_processor_class, mock_device
    ):
        """Test that model is set to eval mode."""
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_model_class.return_value = mock_model_instance
        mock_processor_class.return_value = mock_processor_instance

        with patch('builtins.open', create=True):
            with patch('torch.device'):
                from architect_stream import DeepfakeDetector

                DeepfakeDetector()

                mock_model_instance.eval.assert_called_once()


class TestDeepfakeDetection:
    """Test deepfake detection functionality."""

    @patch('torch.no_grad')
    @patch('torch.softmax')
    @patch('torch.device')
    @patch('transformers.Wav2Vec2Processor.from_pretrained')
    @patch('transformers.Wav2Vec2ForSequenceClassification.from_pretrained')
    def test_detect_deepfake_returns_tuple(
        self, mock_model_class, mock_processor_class, mock_device,
        mock_softmax, mock_no_grad
    ):
        """Test that detect_deepfake returns a tuple."""
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        # Setup processor mock
        mock_processor_instance.return_value = {
            'input_values': MagicMock()
        }

        # Setup model output
        mock_logits = MagicMock()
        mock_logits.argmax.return_value.item.return_value = 0
        mock_model_instance.return_value.logits = mock_logits

        # Setup softmax
        mock_probs = np.array([[0.8, 0.2]])
        mock_softmax_result = MagicMock()
        mock_softmax_result.cpu.return_value.numpy.return_value = mock_probs
        mock_softmax.return_value = mock_softmax_result

        mock_model_class.return_value = mock_model_instance
        mock_processor_class.return_value = mock_processor_instance

        with patch('builtins.open', create=True):
            with patch('torch.device'):
                with patch('torch.no_grad', return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock())):
                    from architect_stream import DeepfakeDetector

                    detector = DeepfakeDetector()
                    audio_data = np.zeros(16000)

                    result = detector.detect_deepfake(audio_data)

                    assert isinstance(result, tuple)
                    assert len(result) == 2
                    assert isinstance(result[0], str)  # scammer_type
                    assert isinstance(result[1], float)  # confidence

    @patch('torch.no_grad')
    @patch('torch.softmax')
    @patch('torch.device')
    @patch('transformers.Wav2Vec2Processor.from_pretrained')
    @patch('transformers.Wav2Vec2ForSequenceClassification.from_pretrained')
    def test_detect_deepfake_returns_human_label(
        self, mock_model_class, mock_processor_class, mock_device,
        mock_softmax, mock_no_grad
    ):
        """Test that detection returns correct label for human."""
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_processor_instance.return_value = {'input_values': MagicMock()}

        mock_logits = MagicMock()
        mock_logits.argmax.return_value.item.return_value = 0  # human
        mock_model_instance.return_value.logits = mock_logits

        mock_probs = np.array([[0.9, 0.1]])
        mock_softmax_result = MagicMock()
        mock_softmax_result.cpu.return_value.numpy.return_value = mock_probs
        mock_softmax.return_value = mock_softmax_result

        mock_model_class.return_value = mock_model_instance
        mock_processor_class.return_value = mock_processor_instance

        with patch('builtins.open', create=True):
            with patch('torch.device'):
                with patch('torch.no_grad', return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock())):
                    from architect_stream import DeepfakeDetector

                    detector = DeepfakeDetector()
                    audio_data = np.zeros(16000)

                    scammer_type, confidence = detector.detect_deepfake(audio_data)

                    assert scammer_type == "human"

    @patch('torch.no_grad')
    @patch('torch.softmax')
    @patch('torch.device')
    @patch('transformers.Wav2Vec2Processor.from_pretrained')
    @patch('transformers.Wav2Vec2ForSequenceClassification.from_pretrained')
    def test_detect_deepfake_returns_deepfake_label(
        self, mock_model_class, mock_processor_class, mock_device,
        mock_softmax, mock_no_grad
    ):
        """Test that detection returns correct label for deepfake."""
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_processor_instance.return_value = {'input_values': MagicMock()}

        mock_logits = MagicMock()
        mock_logits.argmax.return_value.item.return_value = 1  # deepfake
        mock_model_instance.return_value.logits = mock_logits

        mock_probs = np.array([[0.2, 0.8]])
        mock_softmax_result = MagicMock()
        mock_softmax_result.cpu.return_value.numpy.return_value = mock_probs
        mock_softmax.return_value = mock_softmax_result

        mock_model_class.return_value = mock_model_instance
        mock_processor_class.return_value = mock_processor_instance

        with patch('builtins.open', create=True):
            with patch('torch.device'):
                with patch('torch.no_grad', return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock())):
                    from architect_stream import DeepfakeDetector

                    detector = DeepfakeDetector()
                    audio_data = np.zeros(16000)

                    scammer_type, confidence = detector.detect_deepfake(audio_data)

                    assert scammer_type == "deepfake"

    @patch('torch.device')
    @patch('transformers.Wav2Vec2Processor.from_pretrained')
    @patch('transformers.Wav2Vec2ForSequenceClassification.from_pretrained')
    def test_detect_deepfake_handles_error(
        self, mock_model_class, mock_processor_class, mock_device
    ):
        """Test that detection handles errors gracefully."""
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        # Make processor raise an exception
        mock_processor_instance.side_effect = Exception("Processing error")

        mock_model_class.return_value = mock_model_instance
        mock_processor_class.return_value = mock_processor_instance

        with patch('builtins.open', create=True):
            with patch('torch.device'):
                from architect_stream import DeepfakeDetector

                detector = DeepfakeDetector()
                detector.processor = MagicMock()
                detector.processor.side_effect = Exception("Processing error")

                audio_data = np.zeros(16000)
                scammer_type, confidence = detector.detect_deepfake(audio_data)

                # Should return unknown with 0.0 confidence
                assert scammer_type == "unknown"
                assert confidence == 0.0

    @patch('torch.no_grad')
    @patch('torch.softmax')
    @patch('torch.device')
    @patch('transformers.Wav2Vec2Processor.from_pretrained')
    @patch('transformers.Wav2Vec2ForSequenceClassification.from_pretrained')
    def test_detect_deepfake_returns_confidence_score(
        self, mock_model_class, mock_processor_class, mock_device,
        mock_softmax, mock_no_grad
    ):
        """Test that confidence score is returned correctly."""
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_processor_instance.return_value = {'input_values': MagicMock()}

        mock_logits = MagicMock()
        mock_logits.argmax.return_value.item.return_value = 0
        mock_model_instance.return_value.logits = mock_logits

        # High confidence for first class
        mock_probs = np.array([[0.95, 0.05]])
        mock_softmax_result = MagicMock()
        mock_softmax_result.cpu.return_value.numpy.return_value = mock_probs
        mock_softmax.return_value = mock_softmax_result

        mock_model_class.return_value = mock_model_instance
        mock_processor_class.return_value = mock_processor_instance

        with patch('builtins.open', create=True):
            with patch('torch.device'):
                with patch('torch.no_grad', return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock())):
                    from architect_stream import DeepfakeDetector

                    detector = DeepfakeDetector()
                    audio_data = np.zeros(16000)

                    scammer_type, confidence = detector.detect_deepfake(audio_data)

                    assert confidence == pytest.approx(0.95, abs=0.01)
